from typing import Literal

from pydantic import PositiveInt

from app.schemas.common import Schema
from app.schemas.enums import (
    ModerationStatus,
    PostType,
    ThreadRestrictionLevel,
    ThreadType,
)


class UserListQuery(Schema):
    role_id: PositiveInt | None = None
    thread_id: PositiveInt | None = None


class ThreadListQuery(Schema):
    user_id: PositiveInt | None = None
    thread_type: ThreadType | None = None
    restriction_level: ThreadRestrictionLevel | None = None
    tag_id: PositiveInt | None = None
    parent_thread_id: PositiveInt | None = None


class PostListQuery(Schema):
    keyword: str | None = None
    thread_id: PositiveInt | None = None
    user_id: PositiveInt | None = None
    post_type: PostType | None = None
    tag_id: PositiveInt | None = None
    mod_status: ModerationStatus | None = None


class CommentListQuery(Schema):
    keyword: str | None = None
    user_id: PositiveInt | None = None
    mod_status: ModerationStatus | None = None
    format: Literal["json", "txt"] = "json"
