from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response, status
from pydantic import PositiveInt
from sqlalchemy.orm import Session

from app.api.responses import ERROR_RESPONSES
from app.db.database import get_db
from app.models.thread import Thread
from app.schemas.queries import ThreadListQuery
from app.schemas.threads import ThreadCreate, ThreadList, ThreadRead, ThreadUpdate
from app.services.threads import ThreadService

router = APIRouter(prefix="/api/v1/discussions/threads", tags=["threads"])


def get_thread_service(session: Session = Depends(get_db)) -> ThreadService:
    return ThreadService(session)


@router.get(
    "",
    response_model=ThreadList,
    summary="List threads",
    description=(
        "Return threads filtered by creator, type, restriction, tag, or parent."
    ),
    responses=ERROR_RESPONSES,
)
def list_threads(
    query: Annotated[ThreadListQuery, Query()],
    service: ThreadService = Depends(get_thread_service),
) -> ThreadList:
    count, threads = service.list_threads(query)
    return ThreadList(count=count, results=threads)


@router.post(
    "",
    response_model=ThreadRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a thread",
    description=(
        "Create a lab, course, or project thread with its matching subtype, "
        "optional parent, and tags."
    ),
    responses={
        409: ERROR_RESPONSES[409],
        422: ERROR_RESPONSES[422],
        500: ERROR_RESPONSES[500],
    },
)
def create_thread(
    payload: ThreadCreate,
    service: ThreadService = Depends(get_thread_service),
) -> Thread:
    return service.create_thread(payload)


@router.get(
    "/{thread_id}",
    response_model=ThreadRead,
    summary="Get a thread",
    description="Return a thread with its subtype, parent, and tags.",
    responses={404: ERROR_RESPONSES[404], 500: ERROR_RESPONSES[500]},
)
def get_thread(
    thread_id: PositiveInt,
    service: ThreadService = Depends(get_thread_service),
) -> Thread:
    return service.get_thread(thread_id)


@router.patch(
    "/{thread_id}",
    response_model=ThreadRead,
    summary="Update a thread",
    description="Partially update thread details, parent relationship, or tags.",
    responses={
        404: ERROR_RESPONSES[404],
        409: ERROR_RESPONSES[409],
        422: ERROR_RESPONSES[422],
        500: ERROR_RESPONSES[500],
    },
)
def update_thread(
    thread_id: PositiveInt,
    payload: ThreadUpdate,
    service: ThreadService = Depends(get_thread_service),
) -> Thread:
    return service.update_thread(thread_id, payload)


@router.delete(
    "/{thread_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    response_model=None,
    summary="Delete a thread",
    description="Delete a thread and its dependent records.",
    responses={404: ERROR_RESPONSES[404], 500: ERROR_RESPONSES[500]},
)
def delete_thread(
    thread_id: PositiveInt,
    service: ThreadService = Depends(get_thread_service),
) -> Response:
    service.delete_thread(thread_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
