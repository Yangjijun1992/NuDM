from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "nudm",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    beat_schedule={
        "crawl-arxiv-daily": {
            "task": "app.tasks.crawl.crawl_arxiv",
            "schedule": 86400.0,
        },
        "crawl-inspire-daily": {
            "task": "app.tasks.crawl.crawl_inspire",
            "schedule": 86400.0,
        },
        "process-new-papers": {
            "task": "app.tasks.ai_tasks.process_new_papers",
            "schedule": 3600.0,
        },
    },
)

celery_app.autodiscover_tasks(["app.tasks"])
