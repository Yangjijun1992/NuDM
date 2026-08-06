from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.logging_middleware import RequestLogMiddleware
from app.api.auth import router as auth_router
from app.api.users import router as users_router
from app.api.topics import router as topics_router
from app.api.papers import router as papers_router
from app.api.search import router as search_router
from app.api.favorites import router as favorites_router
from app.api.subscriptions import router as subscriptions_router
from app.api.notifications import router as notifications_router
from app.api.admin import router as admin_router
from app.api.feedback import router as feedback_router

app = FastAPI(
    title="NuDM API",
    version="0.1.0",
    description="Particle Physics Paper Tracker",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(RequestLogMiddleware)

app.include_router(auth_router)
app.include_router(users_router)
app.include_router(topics_router)
app.include_router(papers_router)
app.include_router(search_router)
app.include_router(favorites_router)
app.include_router(subscriptions_router)
app.include_router(notifications_router)
app.include_router(admin_router)
app.include_router(feedback_router)


@app.get("/health")
async def health_check():
    return {"status": "ok"}
