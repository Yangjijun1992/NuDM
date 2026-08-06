import logging
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.social import Subscription, Notification
from app.models.topic import PaperTopic, PaperExperiment

logger = logging.getLogger(__name__)


async def generate_notifications_for_paper(
    db: AsyncSession,
    paper_id: uuid.UUID,
    paper_title: str,
    paper_abstract: str | None = None,
) -> int:
    """
    新论文入库后，匹配所有活跃订阅并生成通知。
    返回生成的通知数量。
    """
    subscriptions = await db.execute(
        select(Subscription).where(Subscription.is_active == True)
    )
    subs = subscriptions.scalars().all()

    if not subs:
        return 0

    topics_result = await db.execute(
        select(PaperTopic).where(PaperTopic.paper_id == paper_id)
    )
    paper_topics = [str(pt.topic_id) for pt in topics_result.scalars().all()]

    experiments_result = await db.execute(
        select(PaperExperiment).where(PaperExperiment.paper_id == paper_id)
    )
    paper_experiments = [str(pe.experiment_id) for pe in experiments_result.scalars().all()]

    text_for_match = (
        (paper_title or "")
        + " "
        + (paper_abstract or "")
    ).lower()

    notifications_created = 0

    for sub in subs:
        matched = False

        if sub.type == "topic" and sub.target_id:
            if str(sub.target_id) in paper_topics:
                matched = True
        elif sub.type == "keyword" and sub.keyword:
            if sub.keyword.lower() in text_for_match:
                matched = True
        elif sub.type == "experiment" and sub.target_id:
            if str(sub.target_id) in paper_experiments:
                matched = True

        if matched:
            existing = await db.execute(
                select(Notification).where(
                    Notification.user_id == sub.user_id,
                    Notification.reference_id == paper_id,
                    Notification.type == "new_paper",
                )
            )
            if existing.scalar_one_or_none():
                continue

            n = Notification(
                user_id=sub.user_id,
                type="new_paper",
                title=f"新论文: {paper_title[:200]}",
                content=paper_title if len(paper_title) <= 300 else paper_title[:300] + "...",
                reference_id=paper_id,
                reference_type="paper",
            )
            db.add(n)
            notifications_created += 1

    if notifications_created > 0:
        logger.info(
            "Generated %d notifications for paper %s from %d subscriptions",
            notifications_created,
            str(paper_id),
            len(subs),
        )

    return notifications_created
