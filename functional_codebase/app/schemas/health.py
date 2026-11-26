from typing import Literal

from app.schemas.common import Schema


class HealthRead(Schema):
    status: Literal["healthy"]
