from pydantic import BaseModel


class PaperInFavorite(BaseModel):
    id: str
    title: str
    arxiv_id: str | None
    publish_date: str | None

    model_config = {"from_attributes": True}


class FavoriteResponse(BaseModel):
    id: str
    note: str | None
    created_at: str
    paper: PaperInFavorite

    model_config = {"from_attributes": True}


class FavoriteCreate(BaseModel):
    paper_id: str
    note: str | None = None
