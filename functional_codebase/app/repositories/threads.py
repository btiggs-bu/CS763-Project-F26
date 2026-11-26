from collections.abc import Sequence
from datetime import datetime, timezone
from typing_extensions import NotRequired, TypedDict

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models.enums import ThreadRestrictionLevel, ThreadType
from app.models.tag import ThreadTag
from app.models.thread import (
    Course,
    Lab,
    Project,
    Thread,
    ThreadGroup,
)
from app.repositories.base import BaseRepository
from app.repositories.tags import TagRepository

_THREAD_LOAD_OPTIONS = (
    selectinload(Thread.project),
    selectinload(Thread.course),
    selectinload(Thread.lab),
    selectinload(Thread.child_link),
    selectinload(Thread.tags),
    selectinload(Thread.tag_assignments).selectinload(ThreadTag.tag),
)


class ThreadUpdateValues(TypedDict):
    name: NotRequired[str]
    description: NotRequired[str | None]
    restriction_level: NotRequired[ThreadRestrictionLevel]
    parent_thread_id: NotRequired[int | None]
    tags: NotRequired[list[str]]


class ThreadRepository(BaseRepository[Thread]):
    def __init__(self, session: Session) -> None:
        super().__init__(session, Thread)
        self.tags = TagRepository(session)

    def get_by_id(self, entity_id: int) -> Thread | None:
        statement = (
            select(Thread)
            .options(*_THREAD_LOAD_OPTIONS)
            .where(Thread.thread_id == entity_id)
        )
        return self.session.scalar(statement)

    def list(
        self,
        *,
        user_id: int | None,
        thread_type: ThreadType | None,
        restriction_level: ThreadRestrictionLevel | None,
        tag_id: int | None,
        parent_thread_id: int | None,
    ) -> tuple[int, list[Thread]]:
        filters = []
        if user_id is not None:
            filters.append(Thread.user_id == user_id)
        if thread_type is not None:
            filters.append(Thread.thread_type == thread_type)
        if restriction_level is not None:
            filters.append(Thread.restriction_level == restriction_level)
        if tag_id is not None:
            filters.append(
                Thread.tag_assignments.any(ThreadTag.tag_id == tag_id)
            )
        if parent_thread_id is not None:
            filters.append(
                Thread.child_link.has(
                    ThreadGroup.p_thread_id == parent_thread_id
                )
            )

        total = self.session.scalar(
            select(func.count(Thread.thread_id)).where(*filters)
        ) or 0
        statement = (
            select(Thread)
            .options(*_THREAD_LOAD_OPTIONS)
            .where(*filters)
            .order_by(Thread.thread_id)
        )
        return total, list(self.session.scalars(statement).unique().all())

    def create(
        self,
        *,
        user_id: int,
        thread_type: ThreadType,
        name: str,
        description: str | None,
        restriction_level: ThreadRestrictionLevel,
        parent_thread_id: int | None,
        tag_names: Sequence[str],
    ) -> Thread:
        thread = Thread(
            user_id=user_id,
            thread_type=thread_type,
            restriction_level=restriction_level,
        )
        if thread_type == ThreadType.LAB:
            thread.lab = Lab(name=name, description=description)
        elif thread_type == ThreadType.COURSE:
            thread.course = Course(name=name, description=description)
        elif thread_type == ThreadType.PROJECT:
            thread.project = Project(name=name, description=description)
        else:
            raise ValueError(f"Unsupported thread type: {thread_type}")

        if parent_thread_id is not None:
            thread.child_link = ThreadGroup(p_thread_id=parent_thread_id)
        self._replace_tags(thread, tag_names)
        return self.add(thread)

    def update(
        self,
        thread: Thread,
        values: ThreadUpdateValues,
    ) -> Thread:
        subtype = self._get_subtype(thread)
        if "name" in values:
            subtype.name = values["name"]
        if "description" in values:
            subtype.description = values["description"]
        if "restriction_level" in values:
            thread.restriction_level = values["restriction_level"]
        if "parent_thread_id" in values:
            parent_thread_id = values["parent_thread_id"]
            current_parent_id = (
                thread.child_link.p_thread_id if thread.child_link is not None else None
            )
            if parent_thread_id != current_parent_id:
                if thread.child_link is not None:
                    thread.child_link = None
                    self.session.flush()
                if parent_thread_id is not None:
                    thread.child_link = ThreadGroup(p_thread_id=parent_thread_id)
        if "tags" in values:
            self._replace_tags(thread, values["tags"])
        thread.updated_at = datetime.now(timezone.utc)
        self.session.flush()
        return thread

    def _replace_tags(self, thread: Thread, tag_names: Sequence[str]) -> None:
        existing_assignments = {
            assignment.tag.tag: assignment for assignment in thread.tag_assignments
        }
        tags = self.tags.get_or_create_by_names(tag_names)
        thread.tag_assignments = [
            existing_assignments.get(tag.tag) or ThreadTag(tag=tag)
            for tag in tags
        ]

    @staticmethod
    def _get_subtype(thread: Thread) -> Lab | Course | Project:
        if thread.thread_type == ThreadType.LAB and thread.lab is not None:
            return thread.lab
        if thread.thread_type == ThreadType.COURSE and thread.course is not None:
            return thread.course
        if thread.thread_type == ThreadType.PROJECT and thread.project is not None:
            return thread.project
        raise ValueError("Thread is missing its matching subtype")
