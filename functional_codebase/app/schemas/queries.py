from typing import Literal

from pydantic import Field, PositiveInt

from app.schemas.common import Schema
from app.schemas.enums import (
    ModerationStatus,
    PostType,
    ThreadRestrictionLevel,
    ThreadType,
)


class UserListQuery(Schema):
    role_id: PositiveInt | None = Field(default=None, examples=[2])
    thread_id: PositiveInt | None = Field(default=None, examples=[1001])


class ThreadListQuery(Schema):
    user_id: PositiveInt | None = Field(default=None, examples=[123])
    thread_type: ThreadType | None = Field(default=None, examples=["project"])
    restriction_level: ThreadRestrictionLevel | None = Field(
        default=None,
        examples=["restricted"],
    )
    tag_id: PositiveInt | None = Field(default=None, examples=[7])
    parent_thread_id: PositiveInt | None = Field(default=None, examples=[900])


class PostListQuery(Schema):
    keyword: str | None = Field(default=None, examples=["threat modeling"])
    thread_id: PositiveInt | None = Field(default=None, examples=[1001])
    user_id: PositiveInt | None = Field(default=None, examples=[123])
    post_type: PostType | None = Field(default=None, examples=["discussion"])
    tag_id: PositiveInt | None = Field(default=None, examples=[7])
    mod_status: ModerationStatus | None = Field(
        default=None,
        examples=["active"],
    )


class CommentListQuery(Schema):
    keyword: str | None = Field(default=None, examples=["trust boundaries"])
    user_id: PositiveInt | None = Field(default=None, examples=[456])
    mod_status: ModerationStatus | None = Field(
        default=None,
        examples=["active"],
    )
    format: Literal["json", "txt"] = Field(default="json", examples=["json", "txt"])
