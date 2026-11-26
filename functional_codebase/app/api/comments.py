from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response, status
from fastapi.responses import PlainTextResponse
from pydantic import PositiveInt
from sqlalchemy.orm import Session

from app.api.responses import ERROR_RESPONSES, FORBIDDEN_RESPONSE
from app.db.database import get_db
from app.models.content import Comment
from app.schemas.comments import CommentCreate, CommentList, CommentRead, CommentUpdate
from app.schemas.moderation import (
    CommentModerationResult,
    ModerationStatusUpdate,
)
from app.schemas.queries import CommentListQuery
from app.services.comments import CommentService

router = APIRouter(
    prefix="/api/v1/discussions/posts/{post_id}/comments",
    tags=["comments"],
)


def get_comment_service(session: Session = Depends(get_db)) -> CommentService:
    return CommentService(session)


@router.get(
    "",
    response_model=CommentList,
    summary="List comments",
    description=(
        "Return comments for a post as JSON, or as a downloadable text archive "
        "when format=txt."
    ),
    responses={
        200: {
            "content": {
                "text/plain": {
                    "schema": {"type": "string"},
                    "example": (
                        "Comment 12 | User 4 | Created 2026-11-02T11:06:07\\n"
                        "A useful reply."
                    ),
                }
            }
        },
        404: ERROR_RESPONSES[404],
        500: ERROR_RESPONSES[500],
    },
)
def list_comments(
    post_id: PositiveInt,
    query: Annotated[CommentListQuery, Query()],
    service: CommentService = Depends(get_comment_service),
) -> CommentList | PlainTextResponse:
    count, comments = service.list_comments(post_id, query)
    if query.format == "txt":
        return PlainTextResponse(
            service.export_comments(comments),
            headers={"Content-Disposition": 'attachment; filename="comments.txt"'},
        )
    return CommentList(count=count, results=comments)


@router.post(
    "",
    response_model=CommentRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a comment",
    description=(
        "Create a comment on the specified post or reply to a comment on that "
        "same post. The supplied user_id identifies the author."
    ),
    responses={
        403: FORBIDDEN_RESPONSE,
        404: ERROR_RESPONSES[404],
        422: ERROR_RESPONSES[422],
        500: ERROR_RESPONSES[500],
    },
)
def create_comment(
    post_id: PositiveInt,
    payload: CommentCreate,
    service: CommentService = Depends(get_comment_service),
) -> Comment:
    return service.create_comment(post_id, payload)


@router.get(
    "/{comment_id}",
    response_model=CommentRead,
    summary="Get a comment",
    description="Return one comment belonging to the specified post.",
    responses={404: ERROR_RESPONSES[404], 500: ERROR_RESPONSES[500]},
)
def get_comment(
    post_id: PositiveInt,
    comment_id: PositiveInt,
    service: CommentService = Depends(get_comment_service),
) -> Comment:
    return service.get_comment(post_id, comment_id)


@router.patch(
    "/{comment_id}",
    response_model=CommentRead,
    summary="Update a comment",
    description="Partially update a comment's content.",
    responses={
        404: ERROR_RESPONSES[404],
        422: ERROR_RESPONSES[422],
        500: ERROR_RESPONSES[500],
    },
)
def update_comment(
    post_id: PositiveInt,
    comment_id: PositiveInt,
    payload: CommentUpdate,
    service: CommentService = Depends(get_comment_service),
) -> Comment:
    return service.update_comment(post_id, comment_id, payload)


@router.delete(
    "/{comment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    response_model=None,
    summary="Delete a comment",
    description="Delete a comment and its dependent replies.",
    responses={404: ERROR_RESPONSES[404], 500: ERROR_RESPONSES[500]},
)
def delete_comment(
    post_id: PositiveInt,
    comment_id: PositiveInt,
    service: CommentService = Depends(get_comment_service),
) -> Response:
    service.delete_comment(post_id, comment_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.patch(
    "/{comment_id}/report",
    response_model=CommentModerationResult,
    summary="Report a comment",
    description="Mark a comment as reported for moderator review.",
    responses={404: ERROR_RESPONSES[404], 500: ERROR_RESPONSES[500]},
)
def report_comment(
    post_id: PositiveInt,
    comment_id: PositiveInt,
    service: CommentService = Depends(get_comment_service),
) -> Comment:
    return service.report_comment(post_id, comment_id)


@router.patch(
    "/{comment_id}/moderation",
    response_model=CommentModerationResult,
    summary="Moderate a comment",
    description="Update a comment's moderation status.",
    responses={
        404: ERROR_RESPONSES[404],
        422: ERROR_RESPONSES[422],
        500: ERROR_RESPONSES[500],
    },
)
def moderate_comment(
    post_id: PositiveInt,
    comment_id: PositiveInt,
    payload: ModerationStatusUpdate,
    service: CommentService = Depends(get_comment_service),
) -> Comment:
    return service.moderate_comment(post_id, comment_id, payload.mod_status)
