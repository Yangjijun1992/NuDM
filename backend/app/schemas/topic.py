from pydantic import BaseModel


class TopicBrief(BaseModel):
    id: str
    name: str
    slug: str

    model_config = {"from_attributes": True}


class TopicResponse(BaseModel):
    id: str
    name: str
    slug: str
    description: str | None
    parent_id: str | None
    sort_order: int
    icon: str | None
    keywords: list[str] | None
    paper_count: int
    is_active: bool
    created_at: str

    model_config = {"from_attributes": True}


class TopicDetail(BaseModel):
    id: str
    name: str
    slug: str
    description: str | None
    parent_id: str | None
    sort_order: int
    icon: str | None
    keywords: list[str] | None
    paper_count: int
    is_active: bool
    created_at: str
    experiments: list["ExperimentResponse"] = []

    model_config = {"from_attributes": True}


class TopicCreate(BaseModel):
    name: str
    slug: str
    description: str | None = None
    parent_id: str | None = None
    sort_order: int = 0
    icon: str | None = None
    keywords: list[str] | None = None


class TopicUpdate(BaseModel):
    name: str | None = None
    slug: str | None = None
    description: str | None = None
    parent_id: str | None = None
    sort_order: int | None = None
    icon: str | None = None
    keywords: list[str] | None = None
    is_active: bool | None = None


class ExperimentResponse(BaseModel):
    id: str
    name: str
    full_name: str | None
    description: str | None
    topic_id: str | None
    website: str | None
    is_active: bool
    created_at: str

    model_config = {"from_attributes": True}
