
from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    email: str
    username: str
    password: str


class UserLogin(BaseModel):
    email: str
    password: str


class UserUpdate(BaseModel):
    email: str | None = None
    username: str | None = None
    avatar_url: str | None = None
    password: str | None = None


class UserResponse(BaseModel):
    id: str
    email: str
    username: str
    avatar_url: str | None
    role: str
    created_at: str

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
