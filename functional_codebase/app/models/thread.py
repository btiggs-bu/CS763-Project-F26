from sqlalchemy import (
    CheckConstraint,
    Enum as SAEnum,
    ForeignKey,
    Index,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base
from app.models.enums import ThreadRestrictionLevel, ThreadType
from app.models.mixins import TimestampMixin


class Thread(TimestampMixin, Base):
    __tablename__ = "threads"
    __table_args__ = (
        CheckConstraint(
            "thread_type IN ('lab', 'course', 'project')",
            name="ck_threads_thread_type",
        ),
        CheckConstraint(
            "restriction_level IN ('open', 'restricted', 'closed')",
            name="ck_threads_restriction_level",
        ),
        Index("ix_threads_user_id", "user_id"),
        Index("ix_threads_type_restriction", "thread_type", "restriction_level"),
    )

    thread_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.user_id", ondelete="RESTRICT"),
        nullable=False,
    )
    thread_type: Mapped[ThreadType] = mapped_column(
        SAEnum(
            ThreadType,
            name="thread_type_value",
            native_enum=False,
            create_constraint=False,
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
            validate_strings=True,
            length=16,
        ),
        nullable=False,
    )
    restriction_level: Mapped[ThreadRestrictionLevel] = mapped_column(
        SAEnum(
            ThreadRestrictionLevel,
            name="thread_restriction_level_value",
            native_enum=False,
            create_constraint=False,
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
            validate_strings=True,
            length=16,
        ),
        nullable=False,
    )

    creator: Mapped["User"] = relationship(
        back_populates="created_threads",
        foreign_keys=[user_id],
    )
    project: Mapped["Project | None"] = relationship(
        back_populates="thread",
        uselist=False,
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    course: Mapped["Course | None"] = relationship(
        back_populates="thread",
        uselist=False,
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    lab: Mapped["Lab | None"] = relationship(
        back_populates="thread",
        uselist=False,
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    memberships: Mapped[list["UserThread"]] = relationship(
        back_populates="thread",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    member_users: Mapped[list["User"]] = relationship(
        secondary="user_threads",
        back_populates="member_threads",
        viewonly=True,
    )
    posts: Mapped[list["Post"]] = relationship(
        back_populates="thread",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    parent_links: Mapped[list["ThreadGroup"]] = relationship(
        back_populates="parent_thread",
        foreign_keys="ThreadGroup.p_thread_id",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    child_link: Mapped["ThreadGroup | None"] = relationship(
        back_populates="child_thread",
        foreign_keys="ThreadGroup.c_thread_id",
        uselist=False,
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    tag_assignments: Mapped[list["ThreadTag"]] = relationship(
        back_populates="thread",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    tags: Mapped[list["Tag"]] = relationship(
        secondary="threads_tag",
        back_populates="threads",
        viewonly=True,
    )


class Project(Base):
    __tablename__ = "project"
    __table_args__ = (
        CheckConstraint(
            "length(name) BETWEEN 1 AND 200",
            name="ck_project_name_length",
        ),
        CheckConstraint(
            "description IS NULL OR length(description) <= 5000",
            name="ck_project_description_length",
        ),
    )

    thread_id: Mapped[int] = mapped_column(
        ForeignKey("threads.thread_id", ondelete="CASCADE"),
        primary_key=True,
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(String(5000), nullable=True)

    thread: Mapped[Thread] = relationship(back_populates="project")


class Course(Base):
    __tablename__ = "course"
    __table_args__ = (
        CheckConstraint(
            "length(name) BETWEEN 1 AND 200",
            name="ck_course_name_length",
        ),
        CheckConstraint(
            "description IS NULL OR length(description) <= 5000",
            name="ck_course_description_length",
        ),
    )

    thread_id: Mapped[int] = mapped_column(
        ForeignKey("threads.thread_id", ondelete="CASCADE"),
        primary_key=True,
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(String(5000), nullable=True)

    thread: Mapped[Thread] = relationship(back_populates="course")


class Lab(Base):
    __tablename__ = "lab"
    __table_args__ = (
        CheckConstraint(
            "length(name) BETWEEN 1 AND 200",
            name="ck_lab_name_length",
        ),
        CheckConstraint(
            "description IS NULL OR length(description) <= 5000",
            name="ck_lab_description_length",
        ),
    )

    thread_id: Mapped[int] = mapped_column(
        ForeignKey("threads.thread_id", ondelete="CASCADE"),
        primary_key=True,
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(String(5000), nullable=True)

    thread: Mapped[Thread] = relationship(back_populates="lab")


class ThreadGroup(Base):
    __tablename__ = "threads_group"
    __table_args__ = (
        CheckConstraint("p_thread_id <> c_thread_id", name="ck_threads_group_not_self"),
        UniqueConstraint("p_thread_id", "c_thread_id", name="uq_threads_group_parent_child"),
        UniqueConstraint("c_thread_id", name="uq_threads_group_child"),
        Index("ix_threads_group_parent_id", "p_thread_id"),
    )

    thread_group_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    p_thread_id: Mapped[int] = mapped_column(
        ForeignKey("threads.thread_id", ondelete="CASCADE"),
        nullable=False,
    )
    c_thread_id: Mapped[int] = mapped_column(
        ForeignKey("threads.thread_id", ondelete="CASCADE"),
        nullable=False,
    )

    parent_thread: Mapped[Thread] = relationship(
        back_populates="parent_links",
        foreign_keys=[p_thread_id],
    )
    child_thread: Mapped[Thread] = relationship(
        back_populates="child_link",
        foreign_keys=[c_thread_id],
    )
