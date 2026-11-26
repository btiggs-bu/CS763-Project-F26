from fastapi import FastAPI

from app.api.comments import router as comments_router
from app.api.health import router as health_router
from app.api.posts import router as posts_router
from app.api.timeline import router as timeline_router
from app.api.threads import router as threads_router
from app.api.users import router as users_router
from app.core.exceptions import register_exception_handlers

app = FastAPI(
    title="Research Blog & Project Discussion Board (RBPDB)",
    version="0.1.0",
)
register_exception_handlers(app)
app.include_router(health_router)
app.include_router(users_router)
app.include_router(threads_router)
app.include_router(posts_router)
app.include_router(comments_router)
app.include_router(timeline_router)
