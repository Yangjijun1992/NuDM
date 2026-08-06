from pydantic import BaseModel


class NotificationResponse(BaseModel):
    id: str
    type: str
    title: str
    content: str | None
    reference_id: str | None
    reference_type: str | None
    is_read: bool
    created_at: str
    read_at: str | None

    model_config = {"from_attributes": True}


class UnreadCountResponse(BaseModel):
    count: int
