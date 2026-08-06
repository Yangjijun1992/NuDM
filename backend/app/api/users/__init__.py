from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.auth import UserResponse, UserUpdate
from app.core.database import get_db
from app.core.security import get_password_hash

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return UserResponse(
        id=str(current_user.id),
        email=current_user.email,
        username=current_user.username,
        avatar_url=current_user.avatar_url,
        role=current_user.role,
        created_at=current_user.created_at.isoformat(),
    )


@router.patch("/me", response_model=UserResponse)
async def update_me(
    data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if data.email is not None:
        from sqlalchemy import select
        existing = await db.execute(
            select(User).where(User.email == data.email, User.id != current_user.id)
        )
        if existing.scalar_one_or_none():
            from fastapi import HTTPException
            raise HTTPException(status_code=400, detail="Email already in use")

    if data.username is not None:
        from sqlalchemy import select
        existing = await db.execute(
            select(User).where(User.username == data.username, User.id != current_user.id)
        )
        if existing.scalar_one_or_none():
            from fastapi import HTTPException
            raise HTTPException(status_code=400, detail="Username already in use")

    if data.email is not None:
        current_user.email = data.email
    if data.username is not None:
        current_user.username = data.username
    if data.avatar_url is not None:
        current_user.avatar_url = data.avatar_url
    if data.password is not None:
        current_user.password_hash = get_password_hash(data.password)

    await db.commit()
    await db.refresh(current_user)

    return UserResponse(
        id=str(current_user.id),
        email=current_user.email,
        username=current_user.username,
        avatar_url=current_user.avatar_url,
        role=current_user.role,
        created_at=current_user.created_at.isoformat(),
    )
