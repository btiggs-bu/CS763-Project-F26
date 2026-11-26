from typing import Annotated

from pydantic import Field, PositiveInt, field_validator

from app.models.tag import Tag as TagORM
from app.schemas.common import PatchSchema, Schema, TimestampedRead
from app.schemas.enums import ModerationStatus, PostRestrictionLevel, PostType
from app.schemas.tags import TagNames

from .common import ListResponse

PostTitle = Annotated[str, Field(min_length=1, max_length=200)]
PostContent = Annotated[str, Field(min_length=1, max_length=10000)]


class PostBase(Schema):
    title: PostTitle
    content: PostContent
    restriction_level: PostRestrictionLevel = PostRestrictionLevel.INHERITED


class PostCreate(PostBase):
    post_type: PostType
    user_id: PositiveInt
    thread_id: PositiveInt
    tags: TagNames = Field(default_factory=list)


class PostUpdate(PostBase, PatchSchema):
    title: PostTitle | None = None
    content: PostContent | None = None
    restriction_level: PostRestrictionLevel | None = None


class PostRead(PostBase, TimestampedRead):
    post_id: PositiveInt
    post_type: PostType
    user_id: PositiveInt
    thread_id: PositiveInt
    restriction_level: PostRestrictionLevel
    mod_status: ModerationStatus
    tags: TagNames

    @field_validator("tags", mode="before")
    @classmethod
    def read_tag_names(cls, value: object) -> object:
        if isinstance(value, list):
            return [tag.tag if isinstance(tag, TagORM) else tag for tag in value]
        return value


PostList = ListResponse[PostRead]
