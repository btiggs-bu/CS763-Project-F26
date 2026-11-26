from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.enums import RoleName
from app.models.user import Role, User
from app.repositories.roles import RoleRepository
from app.repositories.users import UserRepository
from app.schemas.queries import UserListQuery
from app.schemas.users import UserCreate, UserUpdate
from app.services.persistence import write_transaction


class UserService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.users = UserRepository(session)
        self.roles = RoleRepository(session)

    def list_users(self, query: UserListQuery) -> tuple[int, list[User]]:
        return self.users.list(role_id=query.role_id, thread_id=query.thread_id)

    def get_user(self, user_id: int) -> User:
        user = self.users.get_by_id(user_id)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User {user_id} was not found",
            )
        return user

    def create_user(self, payload: UserCreate) -> User:
        if self.users.get_by_username(payload.username) is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A user with this username already exists",
            )
        if self.users.get_by_email(str(payload.email)) is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A user with this email already exists",
            )

        roles = self._resolve_roles(payload.roles)
        with write_transaction(self.session):
            user = self.users.create(
                username=payload.username,
                email=str(payload.email),
                display_name=payload.display_name,
                roles=roles,
            )
            user_id = user.user_id
        return self.get_user(user_id)

    def update_user(self, user_id: int, payload: UserUpdate) -> User:
        user = self.get_user(user_id)
        supplied = payload.model_fields_set
        email = payload.email if "email" in supplied else None
        if email is not None:
            existing = self.users.get_by_email(str(email))
            if existing is not None and existing.user_id != user_id:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="A user with this email already exists",
                )

        update_roles = "roles" in payload.model_fields_set
        roles = self._resolve_roles(payload.roles or []) if update_roles else None
        with write_transaction(self.session):
            self.users.update_fields(
                user,
                email=str(email) if email is not None else None,
                display_name=(
                    payload.display_name if "display_name" in supplied else None
                ),
                roles=roles,
                update_roles=update_roles,
            )
        return self.get_user(user_id)

    def delete_user(self, user_id: int) -> None:
        user = self.get_user(user_id)
        with write_transaction(self.session):
            self.users.soft_delete(user, datetime.now(timezone.utc))

    def _resolve_roles(self, requested: list[RoleName]) -> list[Role]:
        requested_names = requested or [RoleName.STUDENT]
        roles = self.roles.get_by_names(requested_names)
        roles_by_name = {role.role_name: role for role in roles}
        missing = [name.value for name in requested_names if name not in roles_by_name]
        if missing:
            if not requested:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="The default student role is not configured",
                )
            raise HTTPException(
                status_code=422,
                detail=f"Role records are missing for: {', '.join(missing)}",
            )
        return [roles_by_name[name] for name in requested_names]
