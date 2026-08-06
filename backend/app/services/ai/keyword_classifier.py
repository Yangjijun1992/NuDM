"""
关键词规则基线分类器 —— 基于专题 keywords 字段进行规则匹配。
不依赖 AI 服务，作为 AI 分类的 baseline 和回退方案。
"""
import logging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.topic import Topic, PaperTopic

logger = logging.getLogger(__name__)


async def classify_by_keywords(
    db: AsyncSession,
    paper_id,
    paper_title: str,
    paper_abstract: str | None = None,
) -> list[tuple[str, float]]:
    """
    基于关键词规则匹配分类。
    返回 [(topic_id, confidence), ...]
    """
    result = await db.execute(
        select(Topic).where(Topic.is_active == True, Topic.keywords.isnot(None))
    )
    topics = result.scalars().all()

    text = ((paper_title or "") + " " + (paper_abstract or "")).lower()
    matches: list[tuple[str, float]] = []

    for topic in topics:
        if not topic.keywords:
            continue

        hit_count = 0
        for kw in topic.keywords:
            if kw.lower() in text:
                hit_count += 1

        if hit_count > 0:
            confidence = min(0.95, 0.4 + hit_count * 0.15)
            matches.append((str(topic.id), round(confidence, 2)))

    matches.sort(key=lambda x: x[1], reverse=True)
    return matches


async def merge_classifications(
    db: AsyncSession,
    paper_id,
    keyword_matches: list[tuple[str, float]],
    ai_matches: list[tuple[str, float]],
):
    """
    合并关键词规则分类和 AI 分类结果，取并集。
    AI 结果的置信度保留原始值，关键词结果的置信度取两者中较低值。
    """
    merged: dict[str, dict] = {}

    for tid, conf in keyword_matches:
        merged[tid] = {"confidence": conf, "is_ai_classified": False}

    for tid, conf in ai_matches:
        if tid in merged:
            merged[tid]["confidence"] = max(merged[tid]["confidence"], conf)
            merged[tid]["is_ai_classified"] = True
        else:
            merged[tid] = {"confidence": conf, "is_ai_classified": True}

    return merged


async def classify_and_save(
    db: AsyncSession,
    paper_id,
    paper_title: str,
    paper_abstract: str | None = None,
    ai_classifications: list[tuple[str, float]] | None = None,
) -> int:
    """
    综合分类：关键词规则 + AI 结果合并后写入 paper_topics 表。
    返回写入的关联数量。
    """
    keyword_matches = await classify_by_keywords(db, paper_id, paper_title, paper_abstract)
    ai_matches = ai_classifications or []

    merged = await merge_classifications(db, paper_id, keyword_matches, ai_matches)

    for tid, info in merged.items():
        existing = await db.execute(
            select(PaperTopic).where(
                PaperTopic.paper_id == paper_id, PaperTopic.topic_id == tid
            )
        )
        pt = existing.scalar_one_or_none()
        if pt:
            pt.confidence = info["confidence"]
            pt.is_ai_classified = info["is_ai_classified"]
        else:
            db.add(PaperTopic(
                paper_id=paper_id,
                topic_id=tid,
                confidence=info["confidence"],
                is_ai_classified=info["is_ai_classified"],
            ))

    return len(merged)
