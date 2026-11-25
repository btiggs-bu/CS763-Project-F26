from fastapi import FastAPI

from api.health import router as health_router
from core.exceptions import register_exception_handlers

app = FastAPI(
    title="Research Blog & Project Discussion Board (RBPDB)",
    version="0.1.0",
)
register_exception_handlers(app)
app.include_router(health_router)
