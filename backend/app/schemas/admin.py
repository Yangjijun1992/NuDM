from pydantic import BaseModel


class AdminStatsResponse(BaseModel):
    paper_count: int
    user_count: int
    source_count: int


class CrawlTaskResponse(BaseModel):
    id: str
    source_id: str
    keyword: str
    status: str
    papers_fetched: int
    papers_new: int
    error_message: str | None
    started_at: str | None
    finished_at: str | None
    created_at: str

    model_config = {"from_attributes": True}


class DataSourceResponse(BaseModel):
    id: str
    name: str
    base_url: str
    api_type: str
    rate_limit: int
    is_active: bool
    config: dict | None
    created_at: str

    model_config = {"from_attributes": True}


class DataSourceCreate(BaseModel):
    name: str
    base_url: str
    api_type: str
    rate_limit: int = 60
    config: dict | None = None


class DataSourceUpdate(BaseModel):
    name: str | None = None
    base_url: str | None = None
    api_type: str | None = None
    rate_limit: int | None = None
    is_active: bool | None = None
    config: dict | None = None


class AISummaryResponse(BaseModel):
    id: str
    paper_id: str
    summary_cn: str | None
    summary_en: str | None
    contribution: str | None
    method: str | None
    result: str | None
    keywords_extracted: list[str] | None
    quality_flag: str
    model: str | None
    tokens_used: int | None
    generated_at: str
    reviewed_by: str | None
    reviewed_at: str | None

    model_config = {"from_attributes": True}


class AISummaryUpdate(BaseModel):
    summary_cn: str | None = None
    summary_en: str | None = None
    contribution: str | None = None
    method: str | None = None
    result: str | None = None
    keywords_extracted: list[str] | None = None
    quality_flag: str | None = None


class TaskTriggerResponse(BaseModel):
    task_id: str
    message: str
