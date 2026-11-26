from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response, status
from pydantic import PositiveInt
from sqlalchemy.orm import Session

from app.api.responses import ERROR_RESPONSES, FORBIDDEN_RESPONSE
from app.db.database import get_db
from app.models.content import Post
from app.schemas.moderation import (
    ModerationStatusUpdate,
    PostModerationResult,
)
from app.schemas.posts import PostCreate, PostList, PostRead, PostUpdate
from app.schemas.queries import PostListQuery
from app.services.posts import PostService

router = APIRouter(prefix="/api/v1/discussions/posts", tags=["posts"])


def get_post_service(session: Session = Depends(get_db)) -> PostService:
    return PostService(session)


@router.get(
    "",
    response_model=PostList,
    summary="List posts",
    description=(
        "Return posts filtered by keyword, thread, author, type, tag, or "
        "moderation status."
    ),
    responses=ERROR_RESPONSES,
)
def list_posts(
    query: Annotated[PostListQuery, Query()],
    service: PostService = Depends(get_post_service),
) -> PostList:
    count, posts = service.list_posts(query)
    return PostList(count=count, results=posts)


@router.post(
    "",
    response_model=PostRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a post",
    description=(
        "Create a discussion or announcement in an existing thread. The supplied "
        "user_id identifies the author and is checked against role and thread "
        "restrictions."
    ),
    responses={
        403: FORBIDDEN_RESPONSE,
        409: ERROR_RESPONSES[409],
        422: ERROR_RESPONSES[422],
        500: ERROR_RESPONSES[500],
    },
)
def create_post(
    payload: PostCreate,
    service: PostService = Depends(get_post_service),
) -> Post:
    return service.create_post(payload)


@router.get(
    "/{post_id}",
    response_model=PostRead,
    summary="Get a post",
    description="Return a post, including its tags and moderation metadata.",
    responses={404: ERROR_RESPONSES[404], 500: ERROR_RESPONSES[500]},
)
def get_post(
    post_id: PositiveInt,
    service: PostService = Depends(get_post_service),
) -> Post:
    return service.get_post(post_id)


@router.patch(
    "/{post_id}",
    response_model=PostRead,
    summary="Update a post",
    description="Partially update a post's title, content, or restriction level.",
    responses={
        403: FORBIDDEN_RESPONSE,
        404: ERROR_RESPONSES[404],
        422: ERROR_RESPONSES[422],
        500: ERROR_RESPONSES[500],
    },
)
def update_post(
    post_id: PositiveInt,
    payload: PostUpdate,
    service: PostService = Depends(get_post_service),
) -> Post:
    return service.update_post(post_id, payload)


@router.delete(
    "/{post_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    response_model=None,
    summary="Delete a post",
    description="Delete a post and its dependent comments and tag associations.",
    responses={404: ERROR_RESPONSES[404], 500: ERROR_RESPONSES[500]},
)
def delete_post(
    post_id: PositiveInt,
    service: PostService = Depends(get_post_service),
) -> Response:
    service.delete_post(post_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.patch(
    "/{post_id}/report",
    response_model=PostModerationResult,
    summary="Report a post",
    description="Mark a post as reported for moderator review.",
    responses={404: ERROR_RESPONSES[404], 500: ERROR_RESPONSES[500]},
)
def report_post(
    post_id: PositiveInt,
    service: PostService = Depends(get_post_service),
) -> Post:
    return service.report_post(post_id)


@router.patch(
    "/{post_id}/moderation",
    response_model=PostModerationResult,
    summary="Moderate a post",
    description="Update a post's moderation status.",
    responses={
        404: ERROR_RESPONSES[404],
        422: ERROR_RESPONSES[422],
        500: ERROR_RESPONSES[500],
    },
)
def moderate_post(
    post_id: PositiveInt,
    payload: ModerationStatusUpdate,
    service: PostService = Depends(get_post_service),
) -> Post:
    return service.moderate_post(post_id, payload.mod_status)
