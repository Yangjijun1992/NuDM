from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite+aiosqlite:///./nudm.db"
    DATABASE_URL_SYNC: str = "sqlite:///./nudm.db"
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    SECRET_KEY: str = "change-me-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    ELASTICSEARCH_URL: str = "http://localhost:9200"
    OPENAI_API_KEY: str = ""
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"
    OPENAI_MODEL: str = "gpt-4o-mini"

    ARXIV_API_URL: str = "https://export.arxiv.org/api/query"
    INSPIRE_API_URL: str = "https://inspirehep.net/api"

    CORS_ORIGINS: List[str] = ["http://localhost:3001", "http://localhost:3000", "http://localhost:8080"]
    LOG_LEVEL: str = "INFO"

    USE_SQLITE: bool = False

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
    }

    def is_sqlite(self) -> bool:
        return "sqlite" in self.DATABASE_URL or self.USE_SQLITE


settings = Settings()
