from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.social import Subscription
from app.schemas.subscription import SubscriptionCreate, SubscriptionResponse, SubscriptionUpdate

router = APIRouter(prefix="/subscriptions", tags=["subscriptions"])


@router.get("", response_model=list[SubscriptionResponse])
async def list_subscriptions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Subscription)
        .where(Subscription.user_id == current_user.id)
        .order_by(Subscription.created_at.desc())
    )
    subs = result.scalars().all()
    return [
        SubscriptionResponse(
            id=str(s.id),
            type=s.type,
            target_id=str(s.target_id) if s.target_id else None,
            keyword=s.keyword,
            frequency=s.frequency,
            is_active=s.is_active,
            created_at=s.created_at.isoformat(),
            updated_at=s.updated_at.isoformat(),
        )
        for s in subs
    ]


@router.post("", status_code=201)
async def create_subscription(
    data: SubscriptionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    sub = Subscription(
        user_id=current_user.id,
        type=data.type,
        target_id=data.target_id,
        keyword=data.keyword,
        frequency=data.frequency,
    )
    db.add(sub)
    await db.commit()
    await db.refresh(sub)
    return SubscriptionResponse(
        id=str(sub.id),
        type=sub.type,
        target_id=str(sub.target_id) if sub.target_id else None,
        keyword=sub.keyword,
        frequency=sub.frequency,
        is_active=sub.is_active,
        created_at=sub.created_at.isoformat(),
        updated_at=sub.updated_at.isoformat(),
    )


@router.patch("/{sub_id}", response_model=SubscriptionResponse)
async def update_subscription(
    sub_id: str,
    data: SubscriptionUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Subscription).where(
            Subscription.id == sub_id, Subscription.user_id == current_user.id
        )
    )
    sub = result.scalar_one_or_none()
    if not sub:
        raise HTTPException(status_code=404, detail="Subscription not found")

    if data.is_active is not None:
        sub.is_active = data.is_active
    if data.frequency is not None:
        sub.frequency = data.frequency
    if data.keyword is not None:
        sub.keyword = data.keyword

    await db.commit()
    await db.refresh(sub)
    return SubscriptionResponse(
        id=str(sub.id),
        type=sub.type,
        target_id=str(sub.target_id) if sub.target_id else None,
        keyword=sub.keyword,
        frequency=sub.frequency,
        is_active=sub.is_active,
        created_at=sub.created_at.isoformat(),
        updated_at=sub.updated_at.isoformat(),
    )


@router.delete("/{sub_id}")
async def delete_subscription(
    sub_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await db.execute(
        delete(Subscription).where(
            Subscription.id == sub_id, Subscription.user_id == current_user.id
        )
    )
    await db.commit()
    return {"message": "Deleted"}
