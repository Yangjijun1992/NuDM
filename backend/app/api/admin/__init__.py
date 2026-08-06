from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.api.deps import get_admin_user
from app.models.datasource import DataSource, CrawlTask
from app.models.paper import Paper
from app.models.social import AISummary
from app.models.user import User
from app.schemas.admin import (
    AdminStatsResponse,
    CrawlTaskResponse,
    DataSourceResponse,
    DataSourceCreate,
    DataSourceUpdate,
    AISummaryResponse,
    AISummaryUpdate,
    TaskTriggerResponse,
)

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/stats", response_model=AdminStatsResponse)
async def get_stats(_: User = Depends(get_admin_user), db: AsyncSession = Depends(get_db)):
    from sqlalchemy import func

    paper_count = (await db.execute(select(func.count()).select_from(Paper))).scalar()
    user_count = (await db.execute(select(func.count()).select_from(User))).scalar()
    source_count = (await db.execute(select(func.count()).select_from(DataSource))).scalar()

    return AdminStatsResponse(
        paper_count=paper_count or 0,
        user_count=user_count or 0,
        source_count=source_count or 0,
    )


@router.get("/crawl-tasks", response_model=list[CrawlTaskResponse])
async def list_crawl_tasks(
    _: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(CrawlTask).order_by(CrawlTask.created_at.desc()).limit(50)
    )
    tasks = result.scalars().all()
    return [
        CrawlTaskResponse(
            id=str(t.id),
            source_id=str(t.source_id),
            keyword=t.keyword,
            status=t.status,
            papers_fetched=t.papers_fetched,
            papers_new=t.papers_new,
            error_message=t.error_message,
            started_at=t.started_at.isoformat() if t.started_at else None,
            finished_at=t.finished_at.isoformat() if t.finished_at else None,
            created_at=t.created_at.isoformat(),
        )
        for t in tasks
    ]


@router.get("/data-sources", response_model=list[DataSourceResponse])
async def list_data_sources(
    _: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(DataSource).order_by(DataSource.created_at))
    sources = result.scalars().all()
    return [
        DataSourceResponse(
            id=str(s.id),
            name=s.name,
            base_url=s.base_url,
            api_type=s.api_type,
            rate_limit=s.rate_limit,
            is_active=s.is_active,
            config=s.config,
            created_at=s.created_at.isoformat(),
        )
        for s in sources
    ]


@router.post("/data-sources", status_code=201, response_model=DataSourceResponse)
async def create_data_source(
    data: DataSourceCreate,
    _: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    ds = DataSource(
        name=data.name,
        base_url=data.base_url,
        api_type=data.api_type,
        rate_limit=data.rate_limit,
        config=data.config,
    )
    db.add(ds)
    await db.commit()
    await db.refresh(ds)
    return DataSourceResponse(
        id=str(ds.id),
        name=ds.name,
        base_url=ds.base_url,
        api_type=ds.api_type,
        rate_limit=ds.rate_limit,
        is_active=ds.is_active,
        config=ds.config,
        created_at=ds.created_at.isoformat(),
    )


@router.patch("/data-sources/{source_id}", response_model=DataSourceResponse)
async def update_data_source(
    source_id: str,
    data: DataSourceUpdate,
    _: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    from fastapi import HTTPException
    result = await db.execute(select(DataSource).where(DataSource.id == source_id))
    ds = result.scalar_one_or_none()
    if not ds:
        raise HTTPException(status_code=404, detail="Data source not found")

    if data.name is not None:
        ds.name = data.name
    if data.base_url is not None:
        ds.base_url = data.base_url
    if data.api_type is not None:
        ds.api_type = data.api_type
    if data.rate_limit is not None:
        ds.rate_limit = data.rate_limit
    if data.is_active is not None:
        ds.is_active = data.is_active
    if data.config is not None:
        ds.config = data.config

    await db.commit()
    await db.refresh(ds)
    return DataSourceResponse(
        id=str(ds.id),
        name=ds.name,
        base_url=ds.base_url,
        api_type=ds.api_type,
        rate_limit=ds.rate_limit,
        is_active=ds.is_active,
        config=ds.config,
        created_at=ds.created_at.isoformat(),
    )


@router.post("/crawl/arxiv", response_model=TaskTriggerResponse)
async def trigger_arxiv_crawl(_: User = Depends(get_admin_user)):
    from app.tasks.crawl import crawl_arxiv
    task = crawl_arxiv.delay()
    return TaskTriggerResponse(task_id=task.id, message="arXiv crawl triggered")


@router.post("/crawl/inspire", response_model=TaskTriggerResponse)
async def trigger_inspire_crawl(_: User = Depends(get_admin_user)):
    from app.tasks.crawl import crawl_inspire
    task = crawl_inspire.delay()
    return TaskTriggerResponse(task_id=task.id, message="INSPIRE crawl triggered")


@router.post("/crawl/all", response_model=TaskTriggerResponse)
async def trigger_full_crawl(_: User = Depends(get_admin_user)):
    from app.tasks.crawl import crawl_all
    task = crawl_all.delay()
    return TaskTriggerResponse(task_id=task.id, message="Full crawl triggered")


@router.post("/ai/summarize", response_model=TaskTriggerResponse)
async def trigger_summarize(
    limit: int = 20,
    _: User = Depends(get_admin_user),
):
    from app.tasks.ai_tasks import generate_summaries
    task = generate_summaries.delay(limit=limit)
    return TaskTriggerResponse(
        task_id=task.id, message=f"Summary generation triggered for {limit} papers"
    )


@router.post("/ai/regenerate-summaries", response_model=TaskTriggerResponse)
async def regenerate_summaries(
    limit: int = 20,
    _: User = Depends(get_admin_user),
):
    from app.tasks.ai_tasks import regenerate_summaries
    task = regenerate_summaries.delay(limit=limit)
    return TaskTriggerResponse(
        task_id=task.id, message=f"Regeneration triggered for {limit} papers"
    )


@router.post("/ai/classify", response_model=TaskTriggerResponse)
async def trigger_classify(
    limit: int = 50,
    _: User = Depends(get_admin_user),
):
    from app.tasks.ai_tasks import classify_and_score
    task = classify_and_score.delay(limit=limit)
    return TaskTriggerResponse(
        task_id=task.id, message=f"Classification triggered for {limit} papers"
    )


@router.get("/ai-summaries", response_model=list[AISummaryResponse])
async def list_ai_summaries(
    quality_flag: str | None = None,
    _: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(AISummary)
    if quality_flag:
        query = query.where(AISummary.quality_flag == quality_flag)
    result = await db.execute(query.order_by(AISummary.generated_at.desc()).limit(50))
    summaries = result.scalars().all()
    return [
        AISummaryResponse(
            id=str(s.id),
            paper_id=str(s.paper_id),
            summary_cn=s.summary_cn,
            summary_en=s.summary_en,
            contribution=s.contribution,
            method=s.method,
            result=s.result,
            keywords_extracted=s.keywords_extracted,
            quality_flag=s.quality_flag,
            model=s.model,
            tokens_used=s.tokens_used,
            generated_at=s.generated_at.isoformat(),
            reviewed_by=str(s.reviewed_by) if s.reviewed_by else None,
            reviewed_at=s.reviewed_at.isoformat() if s.reviewed_at else None,
        )
        for s in summaries
    ]


@router.patch("/ai-summaries/{summary_id}", response_model=AISummaryResponse)
async def update_ai_summary(
    summary_id: str,
    data: AISummaryUpdate,
    _: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    from fastapi import HTTPException
    result = await db.execute(select(AISummary).where(AISummary.id == summary_id))
    s = result.scalar_one_or_none()
    if not s:
        raise HTTPException(status_code=404, detail="AI summary not found")

    if data.summary_cn is not None:
        s.summary_cn = data.summary_cn
    if data.summary_en is not None:
        s.summary_en = data.summary_en
    if data.contribution is not None:
        s.contribution = data.contribution
    if data.method is not None:
        s.method = data.method
    if data.result is not None:
        s.result = data.result
    if data.keywords_extracted is not None:
        s.keywords_extracted = data.keywords_extracted
    if data.quality_flag is not None:
        s.quality_flag = data.quality_flag
        if data.quality_flag in ("approved", "rejected"):
            s.reviewed_by = _.id

    await db.commit()
    await db.refresh(s)
    return AISummaryResponse(
        id=str(s.id),
        paper_id=str(s.paper_id),
        summary_cn=s.summary_cn,
        summary_en=s.summary_en,
        contribution=s.contribution,
        method=s.method,
        result=s.result,
        keywords_extracted=s.keywords_extracted,
        quality_flag=s.quality_flag,
        model=s.model,
        tokens_used=s.tokens_used,
        generated_at=s.generated_at.isoformat(),
        reviewed_by=str(s.reviewed_by) if s.reviewed_by else None,
        reviewed_at=s.reviewed_at.isoformat() if s.reviewed_at else None,
    )


@router.get("/papers")
async def list_all_papers(
    include_hidden: bool = False,
    page: int = 1,
    page_size: int = 20,
    _: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    from sqlalchemy import func
    from app.schemas.paper import PaperListItem
    from app.schemas.common import PaginatedResponse

    query = select(Paper)
    if not include_hidden:
        query = query.where(Paper.is_hidden == False)

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    query = query.order_by(Paper.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    papers = result.scalars().all()

    return PaginatedResponse(
        items=[
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
        ],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=max(1, (total + page_size - 1) // page_size),
    )


@router.patch("/papers/{paper_id}")
async def update_paper(
    paper_id: str,
    data: dict,
    _: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    from fastapi import HTTPException
    result = await db.execute(select(Paper).where(Paper.id == paper_id))
    paper = result.scalar_one_or_none()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")

    allowed_fields = {"title", "title_en", "abstract", "abstract_en", "doi",
                      "arxiv_id", "publish_date", "pdf_url", "source_url", "is_hidden"}
    for key, value in data.items():
        if key in allowed_fields and hasattr(paper, key):
            setattr(paper, key, value)

    await db.commit()
    return {"message": "Updated"}


@router.patch("/papers/{paper_id}/topics")
async def update_paper_topics(
    paper_id: str,
    topic_ids: list[str],
    _: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    from fastapi import HTTPException
    from sqlalchemy import delete
    from app.models.topic import PaperTopic, Topic as TopicModel
    from sqlalchemy import func

    pr = await db.execute(select(Paper).where(Paper.id == paper_id))
    if not pr.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Paper not found")

    await db.execute(
        delete(PaperTopic).where(PaperTopic.paper_id == paper_id)
    )

    for tid in topic_ids:
        db.add(PaperTopic(paper_id=paper_id, topic_id=tid, confidence=1.0))

    await db.flush()

    for tid in topic_ids:
        cnt = await db.execute(
            select(func.count()).select_from(PaperTopic).where(PaperTopic.topic_id == tid)
        )
        count = cnt.scalar() or 0
        tr = await db.execute(select(TopicModel).where(TopicModel.id == tid))
        t = tr.scalar_one_or_none()
        if t:
            t.paper_count = count

    await db.commit()
    return {"message": "Topics updated"}


@router.post("/topics", status_code=201)
async def create_topic(
    data: dict,
    _: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    from app.models.topic import Topic as TopicModel
    topic = TopicModel(
        name=data["name"],
        slug=data["slug"],
        description=data.get("description"),
        sort_order=data.get("sort_order", 0),
        keywords=data.get("keywords", []),
    )
    db.add(topic)
    await db.commit()
    await db.refresh(topic)
    return {"id": str(topic.id), "message": "Created"}


@router.patch("/topics/{topic_id}")
async def update_topic(
    topic_id: str,
    data: dict,
    _: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    from fastapi import HTTPException
    from app.models.topic import Topic as TopicModel
    result = await db.execute(select(TopicModel).where(TopicModel.id == topic_id))
    topic = result.scalar_one_or_none()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")

    allowed_fields = {"name", "slug", "description", "sort_order", "icon", "keywords", "is_active"}
    for key, value in data.items():
        if key in allowed_fields and hasattr(topic, key):
            setattr(topic, key, value)

    await db.commit()
    return {"message": "Updated"}


@router.delete("/topics/{topic_id}")
async def delete_topic(
    topic_id: str,
    _: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    from fastapi import HTTPException
    from app.models.topic import Topic as TopicModel
    result = await db.execute(select(TopicModel).where(TopicModel.id == topic_id))
    topic = result.scalar_one_or_none()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")

    topic.is_active = False
    await db.commit()
    return {"message": "Topic deactivated"}


@router.get("/feedback")
async def list_feedback(
    status: str | None = None,
    _: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    from app.models.social import HumanFeedback
    query = select(HumanFeedback)
    if status:
        query = query.where(HumanFeedback.status == status)
    result = await db.execute(query.order_by(HumanFeedback.created_at.desc()).limit(50))
    feedbacks = result.scalars().all()
    return [
        {
            "id": str(f.id),
            "user_id": str(f.user_id),
            "entity_type": f.entity_type,
            "entity_id": str(f.entity_id),
            "feedback_type": f.feedback_type,
            "content": f.content,
            "status": f.status,
            "created_at": f.created_at.isoformat(),
            "resolved_at": f.resolved_at.isoformat() if f.resolved_at else None,
        }
        for f in feedbacks
    ]


@router.patch("/feedback/{feedback_id}")
async def resolve_feedback(
    feedback_id: str,
    status: str = "resolved",
    _: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    from fastapi import HTTPException
    from app.models.social import HumanFeedback
    from datetime import datetime

    result = await db.execute(select(HumanFeedback).where(HumanFeedback.id == feedback_id))
    fb = result.scalar_one_or_none()
    if not fb:
        raise HTTPException(status_code=404, detail="Feedback not found")

    fb.status = status
    fb.resolved_by = _.id
    fb.resolved_at = datetime.utcnow()
    await db.commit()
    return {"message": f"Feedback {status}"}
