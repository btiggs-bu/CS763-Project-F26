from typing import Annotated, Literal, TypeAlias

from pydantic import Field, PositiveInt, model_validator

from app.models.thread import Thread as ThreadORM
from app.schemas.common import PatchSchema, Schema, TimestampedRead
from app.schemas.enums import ThreadRestrictionLevel, ThreadType
from app.schemas.tags import TagNames

from .common import ListResponse

ThreadName = Annotated[str, Field(min_length=1, max_length=200)]
ThreadDescription = Annotated[str, Field(max_length=5000)]


class ThreadBase(Schema):
    name: ThreadName
    description: ThreadDescription | None = None
    restriction_level: ThreadRestrictionLevel
    tags: TagNames = Field(default_factory=list)


class _ThreadCreateBase(ThreadBase):
    user_id: PositiveInt


class LabThreadCreate(_ThreadCreateBase):
    thread_type: Literal[ThreadType.LAB] = ThreadType.LAB


class CourseThreadCreate(_ThreadCreateBase):
    thread_type: Literal[ThreadType.COURSE] = ThreadType.COURSE
    parent_thread_id: PositiveInt | None = None


class ProjectThreadCreate(_ThreadCreateBase):
    thread_type: Literal[ThreadType.PROJECT] = ThreadType.PROJECT
    parent_thread_id: PositiveInt | None = None


ThreadCreate: TypeAlias = Annotated[
    LabThreadCreate | CourseThreadCreate | ProjectThreadCreate,
    Field(discriminator="thread_type"),
]


class ThreadUpdate(ThreadBase, PatchSchema):
    nullable_fields = frozenset({"description", "parent_thread_id"})

    name: ThreadName | None = None
    description: ThreadDescription | None = None
    restriction_level: ThreadRestrictionLevel | None = None
    parent_thread_id: PositiveInt | None = None
    tags: TagNames | None = None


class ThreadRead(ThreadBase, TimestampedRead):
    description: ThreadDescription | None
    tags: TagNames
    thread_id: PositiveInt
    user_id: PositiveInt
    thread_type: ThreadType
    parent_thread_id: PositiveInt | None

    @model_validator(mode="before")
    @classmethod
    def flatten_orm_thread(cls, value: object) -> object:
        if not isinstance(value, ThreadORM):
            return value

        if value.thread_type == ThreadType.LAB:
            subtype = value.lab
        elif value.thread_type == ThreadType.COURSE:
            subtype = value.course
        elif value.thread_type == ThreadType.PROJECT:
            subtype = value.project
        else:
            raise ValueError("Thread has an unsupported thread type")

        if subtype is None:
            raise ValueError("Thread is missing its matching subtype")

        parent_link = value.child_link
        return {
            "thread_id": value.thread_id,
            "user_id": value.user_id,
            "thread_type": value.thread_type,
            "name": subtype.name,
            "description": subtype.description,
            "restriction_level": value.restriction_level,
            "parent_thread_id": (
                parent_link.p_thread_id if parent_link is not None else None
            ),
            "tags": [tag.tag for tag in value.tags],
            "created_at": value.created_at,
            "updated_at": value.updated_at,
        }


ThreadList = ListResponse[ThreadRead]
