import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.api.openapi_examples import HEALTH, json_response_documentation
from app.api.responses import SERVICE_UNAVAILABLE_RESPONSE
from app.schemas.health import HealthRead

logger = logging.getLogger(__name__)

router = APIRouter(tags=["health"])


@router.get(
    "/health",
    response_model=HealthRead,
    summary="Check API health",
    description="Return a healthy status when the FastAPI application is running.",
    responses={
        200: json_response_documentation(
            "The API is running.",
            HEALTH,
        )
    },
)
def health_check() -> dict[str, str]:
    return {"status": "healthy"}


@router.get(
    "/health/db",
    response_model=HealthRead,
    summary="Check database health",
    description="Execute a lightweight query to verify database connectivity.",
    responses={
        200: json_response_documentation(
            "The API can reach PostgreSQL.",
            HEALTH,
        ),
        503: SERVICE_UNAVAILABLE_RESPONSE,
    },
)
def database_health_check(db: Session = Depends(get_db)) -> dict[str, str]:
    try:
        db.execute(text("SELECT 1")).scalar_one()
    except SQLAlchemyError as exc:
        logger.exception("Database health check failed")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database unavailable",
        ) from exc

    return {"status": "healthy"}
