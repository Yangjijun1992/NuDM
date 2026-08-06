import logging
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.models.paper import Paper
from app.schemas.paper import PaperListItem
from app.schemas.common import PaginatedResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/search", tags=["search"])


async def _db_search(
    q: str,
    author: str | None,
    date_from: str | None,
    date_to: str | None,
    page: int,
    page_size: int,
    sort: str,
    db: AsyncSession,
):
    from sqlalchemy import or_
    from app.models.author import Author, PaperAuthor

    query = select(Paper).where(Paper.is_hidden == False)

    if q:
        query = query.where(
            or_(
                Paper.title.ilike(f"%{q}%"),
                Paper.title_en.ilike(f"%{q}%"),
                Paper.abstract.ilike(f"%{q}%"),
                Paper.abstract_en.ilike(f"%{q}%"),
            )
        )

    if author:
        query = query.join(Paper.paper_authors).join(PaperAuthor.author).where(
            Author.name_normalized.ilike(f"%{author.lower()}%")
        )

    if date_from:
        query = query.where(Paper.publish_date >= date_from)
    if date_to:
        query = query.where(Paper.publish_date <= date_to)

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

    query = query.distinct().offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    papers = result.scalars().all()

    return papers, total


@router.get("", response_model=PaginatedResponse[PaperListItem])
async def search_papers(
    q: str = Query(""),
    topic: str | None = Query(None),
    author: str | None = Query(None),
    date_from: str | None = Query(None),
    date_to: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort: str = Query("date"),
    db: AsyncSession = Depends(get_db),
):
    use_es = q or author
    highlights: dict[str, dict] = {}
    if use_es:
        try:
            from app.services.search import search_papers as es_search
            paper_ids, total, highlights = await es_search(
                q=q or None,
                topic_slug=topic,
                author=author,
                date_from=date_from,
                date_to=date_to,
                page=page,
                page_size=page_size,
                sort=sort,
            )

            if paper_ids:
                result = await db.execute(
                    select(Paper).where(Paper.id.in_(paper_ids))
                )
                paper_map = {str(p.id): p for p in result.scalars().all()}
                papers = [paper_map[pid] for pid in paper_ids if pid in paper_map]
            else:
                papers = []
        except Exception as e:
            logger.warning(f"ES search failed, falling back to DB: {e}")
            papers, total = await _db_search(q, author, date_from, date_to, page, page_size, sort, db)
    else:
        papers, total = await _db_search(q, author, date_from, date_to, page, page_size, sort, db)

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
                highlights=highlights.get(str(p.id)) if highlights else None,
                created_at=p.created_at.isoformat(),
            )
            for p in papers
        ],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=max(1, (total + page_size - 1) // page_size),
    )
