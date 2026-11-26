from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response, status
from pydantic import PositiveInt
from sqlalchemy.orm import Session

from app.api.openapi_examples import (
    THREAD,
    THREAD_COURSE_CREATE,
    THREAD_LAB_CREATE,
    THREAD_LIST,
    THREAD_PROJECT_CREATE,
    THREAD_UPDATE,
    json_response_documentation,
    path_parameter_example,
    request_body_examples,
)
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
    responses={
        200: json_response_documentation(
            "The matching threads and total count.",
            THREAD_LIST,
        ),
        **ERROR_RESPONSES,
    },
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
        201: json_response_documentation("The created thread.", THREAD),
        409: ERROR_RESPONSES[409],
        422: ERROR_RESPONSES[422],
        500: ERROR_RESPONSES[500],
    },
)
def create_thread(
    payload: Annotated[
        ThreadCreate,
        request_body_examples(
            {
                "lab": {
                    "summary": "Create a lab thread",
                    "value": THREAD_LAB_CREATE,
                },
                "course": {
                    "summary": "Create a course under a lab",
                    "value": THREAD_COURSE_CREATE,
                },
                "project": {
                    "summary": "Create a project under a course",
                    "value": THREAD_PROJECT_CREATE,
                },
            }
        ),
    ],
    service: ThreadService = Depends(get_thread_service),
) -> Thread:
    return service.create_thread(payload)


@router.get(
    "/{thread_id}",
    response_model=ThreadRead,
    summary="Get a thread",
    description="Return a thread with its subtype, parent, and tags.",
    responses={
        200: json_response_documentation("The requested thread.", THREAD),
        404: ERROR_RESPONSES[404],
        500: ERROR_RESPONSES[500],
    },
)
def get_thread(
    thread_id: Annotated[PositiveInt, path_parameter_example(1001)],
    service: ThreadService = Depends(get_thread_service),
) -> Thread:
    return service.get_thread(thread_id)


@router.patch(
    "/{thread_id}",
    response_model=ThreadRead,
    summary="Update a thread",
    description="Partially update thread details, parent relationship, or tags.",
    responses={
        200: json_response_documentation("The updated thread.", THREAD),
        404: ERROR_RESPONSES[404],
        409: ERROR_RESPONSES[409],
        422: ERROR_RESPONSES[422],
        500: ERROR_RESPONSES[500],
    },
)
def update_thread(
    thread_id: Annotated[PositiveInt, path_parameter_example(1001)],
    payload: Annotated[
        ThreadUpdate,
        request_body_examples(
            {
                "project": {
                    "summary": "Update a project thread",
                    "value": THREAD_UPDATE,
                }
            }
        ),
    ],
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
    responses={
        204: {"description": "The thread and dependent records were deleted."},
        404: ERROR_RESPONSES[404],
        500: ERROR_RESPONSES[500],
    },
)
def delete_thread(
    thread_id: Annotated[PositiveInt, path_parameter_example(1001)],
    service: ThreadService = Depends(get_thread_service),
) -> Response:
    service.delete_thread(thread_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
