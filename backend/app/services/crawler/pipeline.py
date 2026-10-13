"""数据抓取管道 — 清洗、去重、入库、分类"""


import logging
import re
import uuid
from datetime import datetime
from difflib import SequenceMatcher
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import async_session_factory
from app.models.paper import Paper, PaperSource
from app.models.author import Author, PaperAuthor
from app.models.topic import Topic, PaperTopic, Experiment, PaperExperiment
from app.models.datasource import DataSource, CrawlTask
from app.services.crawler.arxiv import ArxivPaper, search_arxiv_batch
from app.services.crawler.inspire import InspirePaper, search_inspire

logger = logging.getLogger(__name__)


def _fuzzy_dedup_check(title: str, existing_titles: list[str], threshold: float = 0.85) -> bool:
    """检查标题是否与已有论文高度相似"""
    norm_title = title.lower().strip()[:150]
    for et in existing_titles:
        norm_et = et.lower().strip()[:150]
        if SequenceMatcher(None, norm_title, norm_et).ratio() >= threshold:
            return True
    return False


def clean_text(text: str) -> str:
    """清洗文本：去除多余空格、换行、HTML 标签"""
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def normalize_author_name(name: str) -> str:
    """标准化作者姓名：小写、去空格"""
    return name.lower().strip()


def split_authors_affiliations(authors: list[str]) -> list[tuple[str, str]]:
    """从作者名称字符串中分离姓名和机构"""
    results: list[tuple[str, str]] = []
    for name in authors:
        if "(" in name and ")" in name:
            m = re.match(r"(.+?)\s*\((.+?)\)", name)
            if m:
                results.append((m.group(1).strip(), m.group(2).strip()))
            else:
                results.append((name.strip(), ""))
        else:
            results.append((name.strip(), ""))
    return results


async def _get_or_create_author(
    db: AsyncSession, name: str, affiliation: str = ""
) -> uuid.UUID:
    """查找或创建作者"""
    name_norm = normalize_author_name(name)
    result = await db.execute(
        select(Author).where(Author.name_normalized == name_norm)
    )
    author = result.scalar_one_or_none()
    if author:
        return author.id

    author = Author(
        name=name,
        name_normalized=name_norm,
        affiliation=affiliation if affiliation else None,
    )
    db.add(author)
    await db.flush()
    return author.id


async def _match_paper_to_topics(db: AsyncSession, title: str, abstract: str) -> list[uuid.UUID]:
    """基于关键词匹配论文到专题"""
    result = await db.execute(
        select(Topic).where(Topic.is_active == True)
    )
    topics = result.scalars().all()

    text = f"{title} {abstract}".lower()
    matched: list[tuple[uuid.UUID, int]] = []

    for topic in topics:
        if not topic.keywords:
            continue
        score = 0
        for kw in topic.keywords:
            if kw.lower() in text:
                score += 1
        if score > 0:
            matched.append((topic.id, score))

    matched.sort(key=lambda x: x[1], reverse=True)
    return [m[0] for m in matched[:3]]


async def _match_paper_to_experiments(db: AsyncSession, title: str, abstract: str) -> list[uuid.UUID]:
    """基于实验组名称关键词匹配论文"""
    text = ((title or "") + " " + (abstract or "")).lower()

    result = await db.execute(
        select(Experiment).where(Experiment.is_active == True)
    )
    experiments = result.scalars().all()

    matched: list[uuid.UUID] = []
    for exp in experiments:
        name_lower = exp.name.lower()
        full_lower = (exp.full_name or "").lower()

        if name_lower in text or (full_lower and full_lower in text):
            matched.append(exp.id)

    return matched


async def _get_or_create_paper_from_arxiv(
    db: AsyncSession, ap: ArxivPaper, source_id: uuid.UUID
) -> uuid.UUID | None:
    """将 ArxivPaper 入库，去重，返回 paper_id（若已存在返回已存在的ID）"""
    existing = await db.execute(
        select(Paper).where(Paper.arxiv_id == ap.arxiv_id)
    )
    paper = existing.scalar_one_or_none()

    if not paper:
        all_titles = await db.execute(
            select(Paper.title).where(Paper.is_hidden == False)
        )
        existing_titles = [row[0] for row in all_titles if row[0]]
        if _fuzzy_dedup_check(ap.title, existing_titles):
            logger.info("Fuzzy dedup: skipping similar paper: %s", ap.title[:80])
            return None

    if paper:
        exist_source = await db.execute(
            select(PaperSource).where(
                PaperSource.paper_id == paper.id,
                PaperSource.source_id == source_id,
            )
        )
        if not exist_source.scalar_one_or_none():
            db.add(PaperSource(
                paper_id=paper.id,
                source_id=source_id,
                external_id=ap.arxiv_id,
            ))
        return paper.id

    paper = Paper(
        title=ap.title[:1000],
        title_en=ap.title[:1000],
        abstract=clean_text(ap.abstract),
        arxiv_id=ap.arxiv_id,
        doi=ap.doi,
        publish_date=ap.published,
        pdf_url=ap.pdf_url,
        source_url=ap.source_url,
        language="en",
    )
    db.add(paper)
    await db.flush()

    db.add(PaperSource(
        paper_id=paper.id,
        source_id=source_id,
        external_id=ap.arxiv_id,
    ))

    authors_parsed = split_authors_affiliations(ap.authors)
    seen_author_ids: set[uuid.UUID] = set()
    author_order = 0
    for name, aff in authors_parsed:
        author_id = await _get_or_create_author(db, name, aff)
        if author_id in seen_author_ids:
            continue
        seen_author_ids.add(author_id)
        db.add(PaperAuthor(paper_id=paper.id, author_id=author_id, author_order=author_order))
        author_order += 1

    topic_ids = await _match_paper_to_topics(db, ap.title, ap.abstract)
    for tid in topic_ids:
        db.add(PaperTopic(paper_id=paper.id, topic_id=tid, confidence=0.8))

    experiment_ids = await _match_paper_to_experiments(db, ap.title, ap.abstract)
    for eid in experiment_ids:
        db.add(PaperExperiment(paper_id=paper.id, experiment_id=eid))

    logger.info("New paper from arXiv: %s", ap.title[:80])
    await _sync_to_es(paper, db)
    await _notify_subscribers(paper, db)
    return paper.id


async def _sync_to_es(paper: Paper, db: AsyncSession) -> None:
    """同步单篇论文到 Elasticsearch"""
    try:
        from sqlalchemy.orm import selectinload
        from app.services.search import sync_paper_to_es

        result = await db.execute(
            select(Paper)
            .options(
                selectinload(Paper.paper_authors).selectinload(PaperAuthor.author),
                selectinload(Paper.paper_topics).selectinload(PaperTopic.topic),
                selectinload(Paper.paper_experiments).selectinload(PaperExperiment.experiment),
            )
            .where(Paper.id == paper.id)
        )
        p = result.scalar_one()

        doc = {
            "id": str(p.id),
            "title": p.title,
            "title_en": p.title_en,
            "abstract": p.abstract,
            "abstract_en": p.abstract_en,
            "doi": p.doi,
            "arxiv_id": p.arxiv_id,
            "publish_date": p.publish_date.isoformat() if p.publish_date else None,
            "citation_count": p.citation_count,
            "relevance_score": p.relevance_score,
            "hot_score": p.hot_score,
            "language": p.language,
            "authors": [pa.author.name for pa in p.paper_authors],
            "topic_ids": [str(pt.topic_id) for pt in p.paper_topics],
            "topic_names": [pt.topic.name for pt in p.paper_topics],
            "experiment_ids": [str(pe.experiment_id) for pe in p.paper_experiments],
            "experiment_names": [pe.experiment.name for pe in p.paper_experiments],
            "is_hidden": p.is_hidden,
            "created_at": p.created_at.isoformat(),
        }
        await sync_paper_to_es(doc)
    except Exception as e:
        logger.warning(f"ES sync skipped: {e}")


async def _notify_subscribers(paper: Paper, db: AsyncSession) -> None:
    """论文入库后匹配订阅并生成通知"""
    try:
        from app.services.notification import generate_notifications_for_paper
        await generate_notifications_for_paper(
            db, paper.id, paper.title, paper.abstract
        )
    except Exception as e:
        logger.warning(f"Notification generation skipped: {e}")


async def _import_from_inspire(
    db: AsyncSession, ip: InspirePaper, source_id: uuid.UUID
) -> uuid.UUID | None:
    """将 InspirePaper 入库（优先匹配已有 arXiv ID）"""
    arxiv_id = ip.arxiv_eprint

    if arxiv_id:
        existing = await db.execute(
            select(Paper).where(Paper.arxiv_id == arxiv_id)
        )
        paper = existing.scalar_one_or_none()
        if paper:
            paper.citation_count = max(paper.citation_count, ip.citation_count)
            if ip.doi and not paper.doi:
                paper.doi = ip.doi
            await db.flush()

            exist_source = await db.execute(
                select(PaperSource).where(
                    PaperSource.paper_id == paper.id,
                    PaperSource.source_id == source_id,
                )
            )
            if not exist_source.scalar_one_or_none():
                db.add(PaperSource(
                    paper_id=paper.id,
                    source_id=source_id,
                    external_id=ip.inspire_id,
                ))
            return paper.id

    if ip.doi:
        existing = await db.execute(
            select(Paper).where(Paper.doi == ip.doi)
        )
        paper = existing.scalar_one_or_none()
        if paper:
            paper.citation_count = max(paper.citation_count, ip.citation_count)
            if arxiv_id and not paper.arxiv_id:
                paper.arxiv_id = arxiv_id
            await db.flush()
            return paper.id

    all_titles = await db.execute(
        select(Paper.title).where(Paper.is_hidden == False)
    )
    existing_titles = [row[0] for row in all_titles if row[0]]
    if _fuzzy_dedup_check(ip.title, existing_titles):
        logger.info("Fuzzy dedup (inspire): skipping similar paper: %s", ip.title[:80])
        return None

    paper = Paper(
        title=ip.title[:1000],
        title_en=ip.title[:1000],
        abstract=clean_text(ip.abstract),
        arxiv_id=arxiv_id,
        doi=ip.doi,
        publish_date=ip.published,
        source_url=ip.source_url,
        citation_count=ip.citation_count,
        language="en",
    )
    db.add(paper)
    await db.flush()

    db.add(PaperSource(
        paper_id=paper.id,
        source_id=source_id,
        external_id=ip.inspire_id,
    ))

    seen_author_ids: set[uuid.UUID] = set()
    author_order = 0
    for i, name in enumerate(ip.authors):
        aff = ip.author_affiliations[i] if i < len(ip.author_affiliations) else ""
        author_id = await _get_or_create_author(db, name, aff)
        if author_id in seen_author_ids:
            continue
        seen_author_ids.add(author_id)
        db.add(PaperAuthor(paper_id=paper.id, author_id=author_id, author_order=author_order))
        author_order += 1

    topic_ids = await _match_paper_to_topics(db, ip.title, ip.abstract)
    for tid in topic_ids:
        db.add(PaperTopic(paper_id=paper.id, topic_id=tid, confidence=0.8))

    experiment_ids = await _match_paper_to_experiments(db, ip.title, ip.abstract)
    for eid in experiment_ids:
        db.add(PaperExperiment(paper_id=paper.id, experiment_id=eid))

    logger.info("New paper from INSPIRE: %s", ip.title[:80])
    await _sync_to_es(paper, db)
    await _notify_subscribers(paper, db)
    return paper.id


async def _recompute_topic_counts(db: AsyncSession) -> None:
    """回写各专题的论文计数（去规范化列，供专题列表/详情直接读取）"""
    rows = await db.execute(
        select(PaperTopic.topic_id, func.count()).group_by(PaperTopic.topic_id)
    )
    count_map = {tid: cnt for tid, cnt in rows.all()}
    topics = (await db.execute(select(Topic))).scalars().all()
    for t in topics:
        t.paper_count = count_map.get(t.id, 0)


async def run_crawl_pipeline() -> dict:
    """执行完整的抓取管道"""
    result = {
        "arxiv_fetched": 0,
        "inspire_fetched": 0,
        "papers_new": 0,
        "papers_updated": 0,
        "errors": [],
    }

    async with async_session_factory() as db:
        arxiv_source = await db.execute(
            select(DataSource).where(DataSource.api_type == "arxiv")
        )
        arxiv_source = arxiv_source.scalar_one_or_none()
        inspire_source = await db.execute(
            select(DataSource).where(DataSource.api_type == "inspire")
        )
        inspire_source = inspire_source.scalar_one_or_none()

        if arxiv_source:
            arxiv_task = CrawlTask(
                source_id=arxiv_source.id,
                keyword="batch_search",
                status="running",
                started_at=datetime.utcnow(),
            )
            db.add(arxiv_task)
            await db.flush()

            try:
                arxiv_papers = await search_arxiv_batch()
                result["arxiv_fetched"] = len(arxiv_papers)

                arxiv_new = 0
                for ap in arxiv_papers:
                    paper_id = await _get_or_create_paper_from_arxiv(
                        db, ap, arxiv_source.id
                    )
                    if paper_id:
                        arxiv_new += 1

                result["papers_new"] += arxiv_new
                arxiv_task.status = "success"
                arxiv_task.papers_fetched = len(arxiv_papers)
                arxiv_task.papers_new = arxiv_new
                arxiv_task.finished_at = datetime.utcnow()
            except Exception as e:
                logger.exception("arXiv crawl failed")
                arxiv_task.status = "failed"
                arxiv_task.error_message = str(e)
                arxiv_task.finished_at = datetime.utcnow()
                result["errors"].append(f"arXiv: {e}")

        if inspire_source:
            inspire_task = CrawlTask(
                source_id=inspire_source.id,
                keyword="inspire_search",
                status="running",
                started_at=datetime.utcnow(),
            )
            db.add(inspire_task)
            await db.flush()

            try:
                inspire_papers = await search_inspire()
                result["inspire_fetched"] = len(inspire_papers)

                inspire_new = 0
                for ip in inspire_papers:
                    paper_id = await _import_from_inspire(db, ip, inspire_source.id)
                    if paper_id:
                        inspire_new += 1

                result["papers_new"] += inspire_new
                inspire_task.status = "success"
                inspire_task.papers_fetched = len(inspire_papers)
                inspire_task.papers_new = inspire_new
                inspire_task.finished_at = datetime.utcnow()
            except Exception as e:
                logger.exception("INSPIRE crawl failed")
                inspire_task.status = "failed"
                inspire_task.error_message = str(e)
                inspire_task.finished_at = datetime.utcnow()
                result["errors"].append(f"INSPIRE: {e}")

        await _recompute_topic_counts(db)
        await db.commit()

    return result
