from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.enums import ThreadType
from app.models.thread import Thread
from app.repositories.threads import ThreadRepository, ThreadUpdateValues
from app.repositories.users import UserRepository
from app.schemas.queries import ThreadListQuery
from app.schemas.threads import (
    CourseThreadCreate,
    LabThreadCreate,
    ProjectThreadCreate,
    ThreadCreate,
    ThreadUpdate,
)
from app.services.persistence import write_transaction


class ThreadService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.threads = ThreadRepository(session)
        self.users = UserRepository(session)

    def list_threads(self, query: ThreadListQuery) -> tuple[int, list[Thread]]:
        return self.threads.list(
            user_id=query.user_id,
            thread_type=query.thread_type,
            restriction_level=query.restriction_level,
            tag_id=query.tag_id,
            parent_thread_id=query.parent_thread_id,
        )

    def get_thread(self, thread_id: int) -> Thread:
        thread = self.threads.get_by_id(thread_id)
        if thread is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Thread {thread_id} was not found",
            )
        return thread

    def create_thread(self, payload: ThreadCreate) -> Thread:
        user = self.users.get_by_id(payload.user_id)
        if user is None or user.deleted_at is not None:
            raise HTTPException(
                status_code=422,
                detail="user_id must reference an active user",
            )

        if isinstance(payload, LabThreadCreate):
            parent_thread_id = None
        elif isinstance(payload, (CourseThreadCreate, ProjectThreadCreate)):
            parent_thread_id = payload.parent_thread_id
        else:
            raise HTTPException(
                status_code=422,
                detail="Unsupported thread type",
            )

        if parent_thread_id is not None:
            self._validate_parent(payload.thread_type, parent_thread_id)

        with write_transaction(self.session):
            thread = self.threads.create(
                user_id=payload.user_id,
                thread_type=payload.thread_type,
                name=payload.name,
                description=payload.description,
                restriction_level=payload.restriction_level,
                parent_thread_id=parent_thread_id,
                tag_names=payload.tags,
            )
            thread_id = thread.thread_id
        return self.get_thread(thread_id)

    def update_thread(self, thread_id: int, payload: ThreadUpdate) -> Thread:
        thread = self.get_thread(thread_id)
        changes: ThreadUpdateValues = {}
        supplied = payload.model_fields_set

        if "name" in supplied:
            if payload.name is None:
                raise HTTPException(
                    status_code=422,
                    detail="name cannot be null",
                )
            changes["name"] = payload.name
        if "description" in supplied:
            changes["description"] = payload.description
        if "restriction_level" in supplied:
            if payload.restriction_level is None:
                raise HTTPException(
                    status_code=422,
                    detail="restriction_level cannot be null",
                )
            changes["restriction_level"] = payload.restriction_level
        if "parent_thread_id" in supplied:
            changes["parent_thread_id"] = payload.parent_thread_id
            if payload.parent_thread_id is not None:
                self._validate_parent(thread.thread_type, payload.parent_thread_id)
        if "tags" in supplied:
            if payload.tags is None:
                raise HTTPException(
                    status_code=422,
                    detail="tags cannot be null",
                )
            changes["tags"] = payload.tags

        with write_transaction(self.session):
            self.threads.update(thread, changes)
        return self.get_thread(thread_id)

    def delete_thread(self, thread_id: int) -> None:
        thread = self.get_thread(thread_id)
        with write_transaction(self.session):
            self.threads.delete(thread)

    def _validate_parent(self, child_type: ThreadType, parent_thread_id: int) -> None:
        parent = self.threads.get_by_id(parent_thread_id)
        if parent is None:
            raise HTTPException(
                status_code=422,
                detail=f"Parent thread {parent_thread_id} was not found",
            )
        expected_parent_type = {
            ThreadType.COURSE: ThreadType.LAB,
            ThreadType.PROJECT: ThreadType.COURSE,
        }.get(child_type)
        if expected_parent_type is None or parent.thread_type != expected_parent_type:
            raise HTTPException(
                status_code=422,
                detail=(
                    f"A {child_type.value} thread cannot use a "
                    f"{parent.thread_type.value} thread as its parent"
                ),
            )
