from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response, status
from pydantic import PositiveInt
from sqlalchemy.orm import Session

from app.api.responses import ERROR_RESPONSES
from app.db.database import get_db
from app.models.user import User
from app.schemas.queries import UserListQuery
from app.schemas.users import UserCreate, UserList, UserRead, UserUpdate
from app.services.users import UserService

router = APIRouter(prefix="/api/v1/users", tags=["users"])


def get_user_service(session: Session = Depends(get_db)) -> UserService:
    return UserService(session)


@router.get(
    "",
    response_model=UserList,
    summary="List users",
    description="Return users, optionally filtered by role or thread membership.",
    responses=ERROR_RESPONSES,
)
def list_users(
    query: Annotated[UserListQuery, Query()],
    service: UserService = Depends(get_user_service),
) -> UserList:
    count, users = service.list_users(query)
    return UserList(count=count, results=users)


@router.post(
    "",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a user",
    description="Create a user and assign the requested roles, defaulting to student.",
    responses={
        409: ERROR_RESPONSES[409],
        422: ERROR_RESPONSES[422],
        500: ERROR_RESPONSES[500],
    },
)
def create_user(
    payload: UserCreate,
    service: UserService = Depends(get_user_service),
) -> User:
    return service.create_user(payload)


@router.get(
    "/{user_id}",
    response_model=UserRead,
    summary="Get a user",
    description="Return a user by ID, including soft-deletion metadata.",
    responses={404: ERROR_RESPONSES[404], 500: ERROR_RESPONSES[500]},
)
def get_user(
    user_id: PositiveInt,
    service: UserService = Depends(get_user_service),
) -> User:
    return service.get_user(user_id)


@router.patch(
    "/{user_id}",
    response_model=UserRead,
    summary="Update a user",
    description="Partially update a user's profile or role assignments.",
    responses={
        404: ERROR_RESPONSES[404],
        409: ERROR_RESPONSES[409],
        422: ERROR_RESPONSES[422],
        500: ERROR_RESPONSES[500],
    },
)
def update_user(
    user_id: PositiveInt,
    payload: UserUpdate,
    service: UserService = Depends(get_user_service),
) -> User:
    return service.update_user(user_id, payload)


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    response_model=None,
    summary="Soft-delete a user",
    description=(
        "Set deleted_at and close the restriction levels of the user's "
        "created threads, posts, and comments."
    ),
    responses={404: ERROR_RESPONSES[404], 500: ERROR_RESPONSES[500]},
)
def delete_user(
    user_id: PositiveInt,
    service: UserService = Depends(get_user_service),
) -> Response:
    service.delete_user(user_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
