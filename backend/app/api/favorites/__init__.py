from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.social import Favorite
from app.models.paper import Paper
from app.schemas.favorite import FavoriteResponse

router = APIRouter(prefix="/favorites", tags=["favorites"])


@router.get("", response_model=list[FavoriteResponse])
async def list_favorites(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Favorite, Paper)
        .join(Paper, Favorite.paper_id == Paper.id)
        .where(Favorite.user_id == current_user.id)
        .order_by(Favorite.created_at.desc())
    )
    rows = result.all()
    return [
        FavoriteResponse(
            id=str(fav.id),
            note=fav.note,
            created_at=fav.created_at.isoformat(),
            paper={
                "id": str(paper.id),
                "title": paper.title,
                "arxiv_id": paper.arxiv_id,
                "publish_date": paper.publish_date.isoformat() if paper.publish_date else None,
            },
        )
        for fav, paper in rows
    ]


@router.post("/{paper_id}")
async def add_favorite(
    paper_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    existing = await db.execute(
        select(Favorite).where(
            Favorite.user_id == current_user.id, Favorite.paper_id == paper_id
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Already favorited")

    fav = Favorite(user_id=current_user.id, paper_id=paper_id)
    db.add(fav)
    await db.commit()
    return {"message": "Favorited", "id": str(fav.id)}


@router.delete("/{paper_id}")
async def remove_favorite(
    paper_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await db.execute(
        delete(Favorite).where(
            Favorite.user_id == current_user.id, Favorite.paper_id == paper_id
        )
    )
    await db.commit()
    return {"message": "Removed"}
