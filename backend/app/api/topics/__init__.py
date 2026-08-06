from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.models.topic import Topic, Experiment
from app.schemas.topic import TopicResponse, TopicDetail, ExperimentResponse

router = APIRouter(prefix="/topics", tags=["topics"])


@router.get("", response_model=list[TopicResponse])
async def list_topics(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Topic).where(Topic.is_active == True).order_by(Topic.sort_order)
    )
    topics = result.scalars().all()
    return [
        TopicResponse(
            id=str(t.id),
            name=t.name,
            slug=t.slug,
            description=t.description,
            parent_id=str(t.parent_id) if t.parent_id else None,
            sort_order=t.sort_order,
            icon=t.icon,
            keywords=t.keywords,
            paper_count=t.paper_count,
            is_active=t.is_active,
            created_at=t.created_at.isoformat(),
        )
        for t in topics
    ]


@router.get("/{slug}", response_model=TopicDetail)
async def get_topic(slug: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Topic).where(Topic.slug == slug))
    topic = result.scalar_one_or_none()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")

    exp_result = await db.execute(
        select(Experiment).where(
            Experiment.topic_id == topic.id, Experiment.is_active == True
        )
    )
    experiments = exp_result.scalars().all()

    return TopicDetail(
        id=str(topic.id),
        name=topic.name,
        slug=topic.slug,
        description=topic.description,
        parent_id=str(topic.parent_id) if topic.parent_id else None,
        sort_order=topic.sort_order,
        icon=topic.icon,
        keywords=topic.keywords,
        paper_count=topic.paper_count,
        is_active=topic.is_active,
        created_at=topic.created_at.isoformat(),
        experiments=[
            ExperimentResponse(
                id=str(e.id),
                name=e.name,
                full_name=e.full_name,
                description=e.description,
                topic_id=str(e.topic_id) if e.topic_id else None,
                website=e.website,
                is_active=e.is_active,
                created_at=e.created_at.isoformat(),
            )
            for e in experiments
        ],
    )


@router.get("/{slug}/trend")
async def get_topic_trend(slug: str, db: AsyncSession = Depends(get_db)):
    """返回专题按月统计的论文发布趋势"""
    from sqlalchemy import func, extract
    from app.models.paper import Paper
    from app.models.topic import PaperTopic

    result = await db.execute(select(Topic).where(Topic.slug == slug))
    topic = result.scalar_one_or_none()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")

    trend_data = await db.execute(
        select(
            extract("year", Paper.publish_date).label("year"),
            extract("month", Paper.publish_date).label("month"),
            func.count(Paper.id).label("count"),
        )
        .join(Paper.paper_topics)
        .join(PaperTopic.topic)
        .where(Topic.id == topic.id, Paper.publish_date.isnot(None))
        .group_by("year", "month")
        .order_by("year", "month")
    )

    trends = []
    for row in trend_data:
        year, month, count = int(row.year), int(row.month), row.count
        trends.append({
            "label": f"{year}-{month:02d}",
            "count": count,
        })

    return {"slug": slug, "trends": trends}


@router.get("/experiments/list", response_model=list[ExperimentResponse])
async def list_experiments(
    topic_slug: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    """列出所有实验组（可过滤专题）"""
    query = select(Experiment).where(Experiment.is_active == True)
    if topic_slug:
        t_result = await db.execute(select(Topic).where(Topic.slug == topic_slug))
        topic = t_result.scalar_one_or_none()
        if topic:
            query = query.where(Experiment.topic_id == topic.id)

    result = await db.execute(query.order_by(Experiment.name))
    experiments = result.scalars().all()
    return [
        ExperimentResponse(
            id=str(e.id),
            name=e.name,
            full_name=e.full_name,
            description=e.description,
            topic_id=str(e.topic_id) if e.topic_id else None,
            website=e.website,
            is_active=e.is_active,
            created_at=e.created_at.isoformat(),
        )
        for e in experiments
    ]
