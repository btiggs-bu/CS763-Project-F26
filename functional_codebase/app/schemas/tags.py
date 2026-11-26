from typing import Annotated

from pydantic import AfterValidator, Field, PositiveInt

from app.schemas.common import PatchSchema, Schema, ensure_unique_values

TagName = Annotated[str, Field(min_length=1, max_length=50)]
TagNames = Annotated[list[TagName], AfterValidator(ensure_unique_values)]


class TagBase(Schema):
    tag: TagName


class TagCreate(TagBase):
    pass


class TagUpdate(TagBase, PatchSchema):
    tag: TagName | None = None


class TagRead(TagBase):
    tag_id: PositiveInt
