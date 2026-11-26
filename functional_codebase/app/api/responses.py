from app.schemas.errors import ErrorEnvelope

ERROR_RESPONSES = {
    404: {"model": ErrorEnvelope, "description": "The requested entity was not found"},
    409: {"model": ErrorEnvelope, "description": "The request conflicts with existing data"},
    422: {"model": ErrorEnvelope, "description": "The request or referenced IDs are invalid"},
    500: {"model": ErrorEnvelope, "description": "An unexpected server or database error occurred"},
}

FORBIDDEN_RESPONSE = {
    "model": ErrorEnvelope,
    "description": "The user is not permitted to perform this operation",
}
