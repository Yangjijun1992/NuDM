from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.core.database import get_db
from app.models.paper import Paper
from app.models.topic import PaperTopic, Topic
from app.models.author import PaperAuthor
from app.schemas.paper import PaperListItem, PaperDetail
from app.schemas.common import PaginatedResponse

router = APIRouter(prefix="/papers", tags=["papers"])


@router.get("", response_model=PaginatedResponse[PaperListItem])
async def list_papers(
    topic_slug: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort: str = Query("date"),
    db: AsyncSession = Depends(get_db),
):
    query = select(Paper).where(Paper.is_hidden == False)

    if topic_slug:
        query = query.join(Paper.paper_topics).join(PaperTopic.topic).where(
            Topic.slug == topic_slug
        )

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    if sort == "relevance":
        query = query.order_by(Paper.relevance_score.desc().nullslast())
    elif sort == "citations":
        query = query.order_by(Paper.citation_count.desc())
    elif sort == "hot":
        query = query.order_by(Paper.hot_score.desc().nullslast())
    else:
        query = query.order_by(Paper.publish_date.desc().nullslast())

    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    papers = result.scalars().all()

    items = [
        PaperListItem(
            id=str(p.id),
            title=p.title,
            title_en=p.title_en,
            abstract=p.abstract[:500] if p.abstract else None,
            doi=p.doi,
            arxiv_id=p.arxiv_id,
            publish_date=p.publish_date.isoformat() if p.publish_date else None,
            citation_count=p.citation_count,
            language=p.language,
            relevance_score=p.relevance_score,
            hot_score=p.hot_score,
            created_at=p.created_at.isoformat(),
        )
        for p in papers
    ]

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=max(1, (total + page_size - 1) // page_size),
    )


@router.get("/{paper_id}", response_model=PaperDetail)
async def get_paper(paper_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Paper)
        .options(
            selectinload(Paper.paper_authors).selectinload(PaperAuthor.author),
            selectinload(Paper.paper_topics).selectinload(PaperTopic.topic),
            selectinload(Paper.ai_summary),
        )
        .where(Paper.id == paper_id)
    )
    paper = result.scalar_one_or_none()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")

    from app.schemas.paper import AuthorOnPaper
    from app.schemas.topic import TopicBrief
    from app.schemas.paper import AISummaryBrief

    return PaperDetail(
        id=str(paper.id),
        title=paper.title,
        title_en=paper.title_en,
        abstract=paper.abstract,
        abstract_en=paper.abstract_en,
        doi=paper.doi,
        arxiv_id=paper.arxiv_id,
        publish_date=paper.publish_date.isoformat() if paper.publish_date else None,
        citation_count=paper.citation_count,
        pdf_url=paper.pdf_url,
        source_url=paper.source_url,
        language=paper.language,
        relevance_score=paper.relevance_score,
        hot_score=paper.hot_score,
        created_at=paper.created_at.isoformat(),
        updated_at=paper.updated_at.isoformat(),
        authors=[
            AuthorOnPaper(
                id=str(pa.author.id),
                name=pa.author.name,
                name_normalized=pa.author.name_normalized,
                affiliation=pa.author.affiliation,
                orcid=pa.author.orcid,
                order=pa.author_order,
            )
            for pa in paper.paper_authors
        ],
        topics=[
            TopicBrief(
                id=str(pt.topic.id),
                name=pt.topic.name,
                slug=pt.topic.slug,
            )
            for pt in paper.paper_topics
        ],
        ai_summary=AISummaryBrief(
            summary_cn=paper.ai_summary.summary_cn,
            summary_en=paper.ai_summary.summary_en,
            contribution=paper.ai_summary.contribution,
            method=paper.ai_summary.method,
            result=paper.ai_summary.result,
            keywords_extracted=paper.ai_summary.keywords_extracted,
        ) if paper.ai_summary else None,
    )
