from typing import Annotated

from pydantic import Field, PositiveInt

from app.schemas.common import PatchSchema, Schema, TimestampedRead
from app.schemas.enums import CommentRestrictionLevel, ModerationStatus

from .common import ListResponse

CommentContent = Annotated[str, Field(min_length=1, max_length=5000)]


class CommentBase(Schema):
    content: CommentContent


class CommentCreate(CommentBase):
    user_id: PositiveInt
    p_comment_id: PositiveInt | None = None


class CommentUpdate(CommentBase, PatchSchema):
    content: CommentContent | None = None


class CommentRead(CommentBase, TimestampedRead):
    comment_id: PositiveInt
    user_id: PositiveInt
    post_id: PositiveInt
    p_comment_id: PositiveInt | None
    restriction_level: CommentRestrictionLevel
    mod_status: ModerationStatus


CommentList = ListResponse[CommentRead]
