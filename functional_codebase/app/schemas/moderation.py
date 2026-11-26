from datetime import datetime

from pydantic import PositiveInt

from app.schemas.common import Schema
from app.schemas.enums import ModerationStatus


class ModerationStatusUpdate(Schema):
    mod_status: ModerationStatus


class PostModerationResult(Schema):
    post_id: PositiveInt
    mod_status: ModerationStatus
    updated_at: datetime


class CommentModerationResult(Schema):
    comment_id: PositiveInt
    mod_status: ModerationStatus
    updated_at: datetime
