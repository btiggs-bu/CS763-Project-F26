from collections.abc import Hashable
from datetime import datetime
from typing import ClassVar, Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field, model_validator
from typing_extensions import Self


class Schema(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")


class PatchSchema(Schema):
    nullable_fields: ClassVar[frozenset[str]] = frozenset()

    @model_validator(mode="after")
    def validate_patch(self) -> Self:
        if not self.model_fields_set:
            raise ValueError("At least one field must be provided")

        invalid_null_fields = sorted(
            field
            for field in self.model_fields_set
            if field not in self.nullable_fields and getattr(self, field) is None
        )
        if invalid_null_fields:
            fields = ", ".join(invalid_null_fields)
            raise ValueError(f"{fields} cannot be null")

        return self


class TimestampedRead(Schema):
    created_at: datetime
    updated_at: datetime


ItemT = TypeVar("ItemT")


class ListResponse(Schema, Generic[ItemT]):
    count: int = Field(ge=0)
    results: list[ItemT]


UniqueT = TypeVar("UniqueT", bound=Hashable)


def ensure_unique_values(values: list[UniqueT]) -> list[UniqueT]:
    if len(values) != len(set(values)):
        raise ValueError("Items must not contain duplicates")
    return values
