from pydantic import BaseModel


class SubscriptionCreate(BaseModel):
    type: str
    target_id: str | None = None
    keyword: str | None = None
    frequency: str = "daily"


class SubscriptionUpdate(BaseModel):
    is_active: bool | None = None
    frequency: str | None = None
    keyword: str | None = None


class SubscriptionResponse(BaseModel):
    id: str
    type: str
    target_id: str | None
    keyword: str | None
    frequency: str
    is_active: bool
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}
