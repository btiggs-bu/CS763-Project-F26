from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Index,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base
from app.models.enums import RoleName
from app.models.mixins import TimestampMixin


class User(TimestampMixin, Base):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint(
            "length(username) BETWEEN 3 AND 50",
            name="ck_users_username_length",
        ),
        CheckConstraint(
            "length(display_name) BETWEEN 1 AND 100",
            name="ck_users_display_name_length",
        ),
    )

    user_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    email: Mapped[str] = mapped_column(String(254), nullable=False, unique=True)
    display_name: Mapped[str] = mapped_column(String(100), nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    role_assignments: Mapped[list["UserRole"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    roles: Mapped[list["Role"]] = relationship(
        secondary="user_roles",
        back_populates="users",
        viewonly=True,
    )
    memberships: Mapped[list["UserThread"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    member_threads: Mapped[list["Thread"]] = relationship(
        secondary="user_threads",
        back_populates="member_users",
        viewonly=True,
    )
    created_threads: Mapped[list["Thread"]] = relationship(
        back_populates="creator",
        foreign_keys="Thread.user_id",
    )
    posts: Mapped[list["Post"]] = relationship(
        back_populates="author",
        foreign_keys="Post.user_id",
    )
    comments: Mapped[list["Comment"]] = relationship(
        back_populates="author",
        foreign_keys="Comment.user_id",
    )


class Role(Base):
    __tablename__ = "roles"
    __table_args__ = (
        CheckConstraint(
            "role_name IN ('student', 'faculty', 'admin')",
            name="ck_roles_role_name",
        ),
    )

    role_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    role_name: Mapped[RoleName] = mapped_column(
        SAEnum(
            RoleName,
            name="role_name_value",
            native_enum=False,
            create_constraint=False,
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
            validate_strings=True,
            length=16,
        ),
        nullable=False,
        unique=True,
    )

    user_assignments: Mapped[list["UserRole"]] = relationship(
        back_populates="role",
        passive_deletes="all",
    )
    users: Mapped[list[User]] = relationship(
        secondary="user_roles",
        back_populates="roles",
        viewonly=True,
    )


class UserRole(Base):
    __tablename__ = "user_roles"
    __table_args__ = (
        UniqueConstraint("user_id", "role_id", name="uq_user_roles_user_role"),
        Index("ix_user_roles_role_id", "role_id"),
    )

    user_role_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
    )
    role_id: Mapped[int] = mapped_column(
        ForeignKey("roles.role_id", ondelete="RESTRICT"),
        nullable=False,
    )

    user: Mapped[User] = relationship(back_populates="role_assignments")
    role: Mapped[Role] = relationship(back_populates="user_assignments")


class UserThread(Base):
    __tablename__ = "user_threads"
    __table_args__ = (
        UniqueConstraint("user_id", "thread_id", name="uq_user_threads_user_thread"),
        Index("ix_user_threads_thread_id", "thread_id"),
    )

    user_thread_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
    )
    thread_id: Mapped[int] = mapped_column(
        ForeignKey("threads.thread_id", ondelete="CASCADE"),
        nullable=False,
    )

    user: Mapped[User] = relationship(back_populates="memberships")
    thread: Mapped["Thread"] = relationship(back_populates="memberships")
