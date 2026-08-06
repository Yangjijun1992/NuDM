from pydantic import BaseModel
from app.schemas.topic import TopicBrief


class AuthorBrief(BaseModel):
    id: str
    name: str
    name_normalized: str
    affiliation: str | None
    orcid: str | None

    model_config = {"from_attributes": True}


class AuthorOnPaper(BaseModel):
    id: str
    name: str
    name_normalized: str
    affiliation: str | None
    orcid: str | None
    order: int

    model_config = {"from_attributes": True}


class AISummaryBrief(BaseModel):
    summary_cn: str | None
    summary_en: str | None
    contribution: str | None
    method: str | None
    result: str | None
    keywords_extracted: list[str] | None

    model_config = {"from_attributes": True}


class PaperListItem(BaseModel):
    id: str
    title: str
    title_en: str | None
    abstract: str | None
    doi: str | None
    arxiv_id: str | None
    publish_date: str | None
    citation_count: int
    language: str
    relevance_score: float | None
    hot_score: float | None
    highlights: dict | None = None
    created_at: str

    model_config = {"from_attributes": True}


class PaperDetail(BaseModel):
    id: str
    title: str
    title_en: str | None
    abstract: str | None
    abstract_en: str | None
    doi: str | None
    arxiv_id: str | None
    publish_date: str | None
    citation_count: int
    pdf_url: str | None
    source_url: str | None
    language: str
    relevance_score: float | None
    hot_score: float | None
    created_at: str
    updated_at: str
    authors: list[AuthorOnPaper] = []
    topics: list[TopicBrief] = []
    ai_summary: AISummaryBrief | None = None

    model_config = {"from_attributes": True}


class PaperUpdate(BaseModel):
    title: str | None = None
    title_en: str | None = None
    abstract: str | None = None
    abstract_en: str | None = None
    doi: str | None = None
    arxiv_id: str | None = None
    publish_date: str | None = None
    pdf_url: str | None = None
    source_url: str | None = None
    is_hidden: bool | None = None


class PaperCreate(BaseModel):
    title: str
    title_en: str | None = None
    abstract: str | None = None
    abstract_en: str | None = None
    doi: str | None = None
    arxiv_id: str | None = None
    publish_date: str | None = None
    pdf_url: str | None = None
    source_url: str | None = None
    language: str = "en"
