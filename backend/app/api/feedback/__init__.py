from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.social import HumanFeedback

router = APIRouter(prefix="/feedback", tags=["feedback"])


@router.post("")
async def submit_feedback(
    data: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    fb = HumanFeedback(
        user_id=current_user.id,
        entity_type=data.get("entity_type", "paper"),
        entity_id=data["entity_id"],
        feedback_type=data.get("feedback_type", "correction"),
        content=data["content"],
    )
    db.add(fb)
    await db.commit()
    await db.refresh(fb)
    return {"id": str(fb.id), "message": "Feedback submitted"}
