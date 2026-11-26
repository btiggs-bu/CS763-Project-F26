from app.schemas.errors import ErrorEnvelope
from app.api.openapi_examples import json_error_example

ERROR_RESPONSES = {
    404: {
        "model": ErrorEnvelope,
        **json_error_example(
            "The requested entity was not found",
            "The requested resource was not found",
        ),
    },
    409: {
        "model": ErrorEnvelope,
        **json_error_example(
            "The request conflicts with existing data",
            "A record with the supplied unique value already exists",
        ),
    },
    422: {
        "model": ErrorEnvelope,
        **json_error_example(
            "The request or referenced IDs are invalid",
            "Request validation failed",
            code="VALIDATION_ERROR",
        ),
    },
    500: {
        "model": ErrorEnvelope,
        **json_error_example(
            "An unexpected server or database error occurred",
            "An unexpected error occurred",
            code="INTERNAL_SERVER_ERROR",
        ),
    },
}

FORBIDDEN_RESPONSE = {
    "model": ErrorEnvelope,
    **json_error_example(
        "The user is not permitted to perform this operation",
        "The user is not permitted to perform this operation",
    ),
}

SERVICE_UNAVAILABLE_RESPONSE = {
    "model": ErrorEnvelope,
    **json_error_example(
        "PostgreSQL is unavailable",
        "Database unavailable",
    ),
}
