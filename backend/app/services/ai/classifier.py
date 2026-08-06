"""分类引擎 — 关键词匹配 + AI 辅助分类"""

import json
import logging
from datetime import datetime
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from openai import AsyncOpenAI
from app.core.config import settings
from app.core.database import async_session_factory
from app.models.paper import Paper
from app.models.topic import Topic, PaperTopic

logger = logging.getLogger(__name__)

CLASSIFICATION_PROMPT = """你是一个粒子物理学分类助手。请根据论文的标题和摘要，将其分类到以下专题中。

可选专题（每个专题的 slug 和关键词）:
{topics_desc}

请返回 JSON（不要包含 markdown 代码块标记）:
{{
  "classifications": [
    {{"topic_slug": "slug1", "confidence": 0.9}},
    {{"topic_slug": "slug2", "confidence": 0.6}}
  ]
}}

只返回置信度 >= 0.5 的分类，最多 3 个。
"""


async def classify_paper(paper_id: str) -> dict:
    """使用 AI 对单篇论文进行分类"""
    async with async_session_factory() as db:
        paper = (await db.execute(select(Paper).where(Paper.id == paper_id))).scalar_one_or_none()
        if not paper:
            return {"error": "Paper not found"}

        topics = (await db.execute(
            select(Topic).where(Topic.is_active == True)
        )).scalars().all()

        if not topics:
            return {"error": "No active topics"}

        topics_desc = "\n".join(
            f"  - {t.name} (slug: {t.slug}): {', '.join(t.keywords[:5]) if t.keywords else ''}"
            for t in topics
        )

        text = (paper.title + " " + (paper.abstract or "") + " " + (paper.abstract_en or ""))[:3000]

        client = AsyncOpenAI(
            api_key=settings.OPENAI_API_KEY,
            base_url=settings.OPENAI_BASE_URL,
        )

        try:
            response = await client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": CLASSIFICATION_PROMPT.format(topics_desc=topics_desc)},
                    {"role": "user", "content": text},
                ],
                temperature=0.2,
                max_tokens=500,
            )

            content = response.choices[0].message.content or "{}"
            data = _parse_json_response(content)
            classifications = data.get("classifications", [])

            slug_to_topic = {t.slug: t for t in topics}

            for cls in classifications:
                slug = cls.get("topic_slug", "")
                topic = slug_to_topic.get(slug)
                if not topic:
                    continue

                existing = await db.execute(
                    select(PaperTopic).where(
                        PaperTopic.paper_id == paper_id,
                        PaperTopic.topic_id == topic.id,
                    )
                )
                if existing.scalar_one_or_none():
                    continue

                db.add(PaperTopic(
                    paper_id=paper_id,
                    topic_id=topic.id,
                    confidence=cls.get("confidence", 0.5),
                    is_ai_classified=True,
                ))

            await db.commit()
            return {"status": "ok", "classifications": classifications}

        except Exception as e:
            logger.error("Classification failed for %s: %s", paper_id, e)
            return {"status": "error", "error": str(e)}


def _parse_json_response(content: str) -> dict:
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        pass
    import re
    m = re.search(r"\{[\s\S]*\}", content)
    if m:
        try:
            return json.loads(m.group())
        except json.JSONDecodeError:
            pass
    return {"classifications": []}


async def score_paper(paper_id: str) -> dict:
    """计算论文的相关度评分和热度评分"""
    async with async_session_factory() as db:
        paper = (await db.execute(select(Paper).where(Paper.id == paper_id))).scalar_one_or_none()
        if not paper:
            return {"error": "Paper not found"}

        paper_topics = (await db.execute(
            select(PaperTopic).where(PaperTopic.paper_id == paper_id)
        )).scalars().all()

        confidences = [pt.confidence for pt in paper_topics] if paper_topics else [0.5]
        relevance = sum(confidences) / len(confidences) if confidences else 0.5

        days_since_pub = 365
        if paper.publish_date:
            days_since_pub = max(1, (datetime.utcnow().date() - paper.publish_date).days)
        recency = max(0.1, 365 / days_since_pub)

        citations_log = __import__("math").log(paper.citation_count + 1)

        hot_score = round(relevance * 0.4 + recency * 0.3 + citations_log * 0.3, 3)
        relevance_score = round(relevance, 3)

        paper.relevance_score = relevance_score
        paper.hot_score = hot_score
        await db.commit()

        return {
            "paper_id": paper_id,
            "relevance_score": relevance_score,
            "hot_score": hot_score,
        }


async def batch_classify_and_score(limit: int = 50) -> dict:
    """批量分类 + 评分"""
    async with async_session_factory() as db:
        papers = (await db.execute(
            select(Paper)
            .where(Paper.is_hidden == False)
            .where(Paper.relevance_score.is_(None))
            .limit(limit)
        )).scalars().all()

        classified = 0
        scored = 0
        for paper in papers:
            pid = str(paper.id)
            c_res = await classify_paper(pid)
            if c_res.get("status") == "ok":
                classified += 1
            s_res = await score_paper(pid)
            if "error" not in s_res:
                scored += 1

        return {"classified": classified, "scored": scored, "total": len(papers)}
