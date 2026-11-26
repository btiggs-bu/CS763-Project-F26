from fastapi import APIRouter, Depends
from pydantic import PositiveInt
from sqlalchemy.orm import Session

from app.api.responses import ERROR_RESPONSES
from app.db.database import get_db
from app.schemas.enums import ThreadType
from app.schemas.posts import PostList
from app.services.posts import PostService

router = APIRouter(
    prefix="/api/v1/discussions/scopes",
    tags=["timeline"],
)


def get_timeline_service(session: Session = Depends(get_db)) -> PostService:
    return PostService(session)


@router.get(
    "/{thread_type}/{thread_id}/timeline",
    response_model=PostList,
    summary="Get a thread timeline",
    description=(
        "Return posts in chronological order for a project, course, or lab "
        "thread."
    ),
    responses={404: ERROR_RESPONSES[404], 500: ERROR_RESPONSES[500]},
)
def get_timeline(
    thread_type: ThreadType,
    thread_id: PositiveInt,
    service: PostService = Depends(get_timeline_service),
) -> PostList:
    count, posts = service.get_timeline(thread_type, thread_id)
    return PostList(count=count, results=posts)
