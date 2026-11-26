from typing import Any

from fastapi import Body, Path
from fastapi.params import Body as BodyField
from fastapi.params import Path as PathField

TIMESTAMP = "2026-11-02T11:06:07.235541Z"

USER = {
    "user_id": 123,
    "username": "jdoe",
    "email": "jdoe@university.edu",
    "display_name": "Jordan Doe",
    "roles": ["student"],
    "created_at": TIMESTAMP,
    "updated_at": TIMESTAMP,
    "deleted_at": None,
}
USER_LIST = {"count": 1, "results": [USER]}
USER_CREATE = {
    "username": "jdoe",
    "email": "jdoe@university.edu",
    "display_name": "Jordan Doe",
    "roles": ["student"],
}
USER_UPDATE = {"display_name": "Jordan A. Doe"}

THREAD = {
    "thread_id": 1001,
    "user_id": 123,
    "thread_type": "project",
    "name": "Secure Research Project",
    "description": "A project investigating secure software practices.",
    "restriction_level": "restricted",
    "parent_thread_id": 900,
    "tags": ["security", "research"],
    "created_at": TIMESTAMP,
    "updated_at": TIMESTAMP,
}
THREAD_LIST = {"count": 1, "results": [THREAD]}
THREAD_LAB_CREATE = {
    "thread_type": "lab",
    "user_id": 456,
    "name": "Applied Security Lab",
    "description": "Research in secure systems.",
    "restriction_level": "open",
    "tags": ["security"],
}
THREAD_COURSE_CREATE = {
    "thread_type": "course",
    "user_id": 456,
    "name": "Secure Software Development",
    "restriction_level": "restricted",
    "parent_thread_id": 700,
}
THREAD_PROJECT_CREATE = {
    "thread_type": "project",
    "user_id": 123,
    "name": "Secure Research Project",
    "description": "A project investigating secure software practices.",
    "restriction_level": "restricted",
    "parent_thread_id": 900,
    "tags": ["security", "research"],
}
THREAD_UPDATE = {"description": "Updated project scope."}

POST = {
    "post_id": 64368473,
    "post_type": "discussion",
    "user_id": 123,
    "thread_id": 1001,
    "title": "Threat modeling review",
    "content": "Which threat scenarios should we prioritize?",
    "restriction_level": "inherited",
    "mod_status": "active",
    "tags": ["security", "research"],
    "created_at": TIMESTAMP,
    "updated_at": TIMESTAMP,
}
POST_LIST = {"count": 1, "results": [POST]}
POST_CREATE = {
    "post_type": "discussion",
    "user_id": 123,
    "thread_id": 1001,
    "title": "Threat modeling review",
    "content": "Which threat scenarios should we prioritize?",
    "tags": ["security", "research"],
}
POST_UPDATE = {"content": "Please review the updated threat scenarios."}

COMMENT = {
    "comment_id": 50413740,
    "user_id": 456,
    "post_id": 64368473,
    "p_comment_id": None,
    "content": "Start with the trust boundaries and external inputs.",
    "restriction_level": "inherited",
    "mod_status": "active",
    "created_at": TIMESTAMP,
    "updated_at": TIMESTAMP,
}
COMMENT_LIST = {"count": 1, "results": [COMMENT]}
COMMENT_CREATE = {
    "user_id": 456,
    "content": "Start with the trust boundaries and external inputs.",
}
COMMENT_UPDATE = {"content": "Review the trust boundaries and external inputs."}

MODERATION_UPDATE = {"mod_status": "hidden_by_moderator"}
POST_MODERATION = {
    "post_id": 64368473,
    "mod_status": "reported",
    "updated_at": TIMESTAMP,
}
COMMENT_MODERATION = {
    "comment_id": 50413740,
    "mod_status": "reported",
    "updated_at": TIMESTAMP,
}
COMMENT_MODERATION_HIDDEN = {
    "comment_id": 50413740,
    "mod_status": "hidden_by_moderator",
    "updated_at": TIMESTAMP,
}
POST_MODERATION_HIDDEN = {
    "post_id": 64368473,
    "mod_status": "hidden_by_moderator",
    "updated_at": TIMESTAMP,
}
HEALTH = {"status": "healthy"}

ERROR = {
    "error": {
        "code": "HTTP_ERROR",
        "message": "The requested resource was not found",
    },
    "timestamp": TIMESTAMP,
    "request_id": "0f45ef7d-790a-4b82-b9fc-fd2c8afc8d5b",
}


def request_body_examples(
    examples: dict[str, dict[str, Any]],
) -> BodyField:
    return Body(openapi_examples=examples)


def path_parameter_example(value: int | str) -> PathField:
    return Path(examples=[value])


def json_response_documentation(
    description: str,
    example: Any,
) -> dict[str, Any]:
    return {
        "description": description,
        "content": {
            "application/json": {
                "examples": {
                    "success": {
                        "summary": "Successful response",
                        "value": example,
                    }
                }
            }
        },
    }


def json_error_example(
    description: str,
    message: str,
    code: str = "HTTP_ERROR",
) -> dict[str, Any]:
    return {
        "description": description,
        "content": {
            "application/json": {
                "examples": {
                    "error": {
                        "summary": description,
                        "value": {
                            **ERROR,
                            "error": {"code": code, "message": message},
                        },
                    }
                }
            }
        },
    }
