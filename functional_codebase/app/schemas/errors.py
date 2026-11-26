from datetime import datetime
from enum import Enum
from uuid import UUID

from app.schemas.common import Schema


class ErrorCode(str, Enum):
    VALIDATION_ERROR = "VALIDATION_ERROR"
    HTTP_ERROR = "HTTP_ERROR"
    DATABASE_ERROR = "DATABASE_ERROR"
    INTERNAL_SERVER_ERROR = "INTERNAL_SERVER_ERROR"


class ErrorInfo(Schema):
    code: ErrorCode
    message: str


class ErrorEnvelope(Schema):
    error: ErrorInfo
    timestamp: datetime
    request_id: UUID
