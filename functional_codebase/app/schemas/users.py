from datetime import datetime
from typing import Annotated

from pydantic import AfterValidator, EmailStr, Field, PositiveInt, field_validator

from app.models.user import Role as RoleORM
from app.schemas.common import (
    PatchSchema,
    Schema,
    TimestampedRead,
    ensure_unique_values,
)
from app.schemas.enums import RoleName

from .common import ListResponse

Username = Annotated[str, Field(min_length=3, max_length=50)]
DisplayName = Annotated[str, Field(min_length=1, max_length=100)]
EmailAddress = Annotated[EmailStr, Field(max_length=254)]
RoleNames = Annotated[list[RoleName], AfterValidator(ensure_unique_values)]


class UserProfileBase(Schema):
    email: EmailAddress
    display_name: DisplayName


class UserBase(UserProfileBase):
    username: Username


class UserCreate(UserBase):
    roles: RoleNames = Field(default_factory=list)


class UserUpdate(UserProfileBase, PatchSchema):
    email: EmailAddress | None = None
    display_name: DisplayName | None = None
    roles: RoleNames | None = None


class UserRead(UserBase, TimestampedRead):
    user_id: PositiveInt
    roles: RoleNames
    deleted_at: datetime | None

    @field_validator("roles", mode="before")
    @classmethod
    def read_role_names(cls, value: object) -> object:
        if isinstance(value, list):
            return [
                role.role_name if isinstance(role, RoleORM) else role
                for role in value
            ]
        return value


UserList = ListResponse[UserRead]
