from collections.abc import Sequence
from datetime import datetime, timezone

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session, selectinload

from app.models.content import Comment, Post
from app.models.enums import (
    CommentRestrictionLevel,
    PostRestrictionLevel,
    ThreadRestrictionLevel,
)
from app.models.thread import Thread
from app.models.user import Role, User, UserRole, UserThread
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    def __init__(self, session: Session) -> None:
        super().__init__(session, User)

    def get_by_id(self, entity_id: int) -> User | None:
        statement = (
            select(User)
            .options(
                selectinload(User.roles),
                selectinload(User.role_assignments).selectinload(UserRole.role),
            )
            .where(User.user_id == entity_id)
        )
        return self.session.scalar(statement)

    def get_by_username(self, username: str) -> User | None:
        return self.session.scalar(select(User).where(User.username == username))

    def get_by_email(self, email: str) -> User | None:
        return self.session.scalar(select(User).where(User.email == email))

    def list(
        self,
        *,
        role_id: int | None,
        thread_id: int | None,
    ) -> tuple[int, list[User]]:
        filters = []
        if role_id is not None:
            filters.append(
                User.role_assignments.any(UserRole.role_id == role_id)
            )
        if thread_id is not None:
            filters.append(
                User.memberships.any(UserThread.thread_id == thread_id)
                | User.created_threads.any(Thread.thread_id == thread_id)
            )

        total = self.session.scalar(
            select(func.count(User.user_id)).where(*filters)
        ) or 0
        statement = (
            select(User)
            .options(selectinload(User.roles))
            .where(*filters)
            .order_by(User.user_id)
        )
        return total, list(self.session.scalars(statement).unique().all())

    def create(
        self,
        *,
        username: str,
        email: str,
        display_name: str,
        roles: Sequence[Role],
    ) -> User:
        user = User(
            username=username,
            email=email,
            display_name=display_name,
        )
        user.role_assignments = [UserRole(role=role) for role in roles]
        return self.add(user)

    def update_fields(
        self,
        user: User,
        *,
        email: str | None,
        display_name: str | None,
        roles: Sequence[Role] | None,
        update_roles: bool,
    ) -> User:
        if email is not None:
            user.email = email
        if display_name is not None:
            user.display_name = display_name
        if update_roles:
            if roles is None:
                raise ValueError("Roles must be resolved when updating roles")
            existing_assignments = {
                assignment.role.role_name: assignment
                for assignment in user.role_assignments
            }
            user.role_assignments = [
                existing_assignments.get(role.role_name) or UserRole(role=role)
                for role in roles
            ]
        user.updated_at = datetime.now(timezone.utc)
        self.session.flush()
        return user

    def soft_delete(self, user: User, deleted_at: datetime) -> None:
        if user.deleted_at is not None:
            return

        user.deleted_at = deleted_at
        self.session.execute(
            update(Thread)
            .where(Thread.user_id == user.user_id)
            .values(
                restriction_level=ThreadRestrictionLevel.CLOSED,
                updated_at=func.now(),
            )
        )
        self.session.execute(
            update(Post)
            .where(Post.user_id == user.user_id)
            .values(
                restriction_level=PostRestrictionLevel.CLOSED,
                updated_at=func.now(),
            )
        )
        self.session.execute(
            update(Comment)
            .where(Comment.user_id == user.user_id)
            .values(
                restriction_level=CommentRestrictionLevel.CLOSED,
                updated_at=func.now(),
            )
        )
        self.session.flush()
