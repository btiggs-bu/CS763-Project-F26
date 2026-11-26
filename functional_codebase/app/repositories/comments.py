from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.content import Comment
from app.models.enums import CommentRestrictionLevel, ModerationStatus
from app.repositories.base import BaseRepository
from app.repositories.search import full_text_filter


class CommentRepository(BaseRepository[Comment]):
    def __init__(self, session: Session) -> None:
        super().__init__(session, Comment)

    def get_by_id(self, post_id: int, comment_id: int) -> Comment | None:
        statement = select(Comment).where(
            Comment.post_id == post_id,
            Comment.comment_id == comment_id,
        )
        return self.session.scalar(statement)

    def get_for_post(self, post_id: int, comment_id: int) -> Comment | None:
        return self.get_by_id(post_id, comment_id)

    def list(
        self,
        *,
        post_id: int,
        keyword: str | None,
        user_id: int | None,
        mod_status: ModerationStatus | None,
    ) -> tuple[int, list[Comment]]:
        filters = [Comment.post_id == post_id]
        if keyword:
            filters.append(
                full_text_filter(self.session, (Comment.content,), keyword)
            )
        if user_id is not None:
            filters.append(Comment.user_id == user_id)
        if mod_status is not None:
            filters.append(Comment.mod_status == mod_status)

        total = self.session.scalar(
            select(func.count(Comment.comment_id)).where(*filters)
        ) or 0
        statement = (
            select(Comment)
            .where(*filters)
            .order_by(Comment.created_at, Comment.comment_id)
        )
        return total, list(self.session.scalars(statement).all())

    def create(
        self,
        *,
        post_id: int,
        user_id: int,
        parent_comment_id: int | None,
        content: str,
        restriction_level: CommentRestrictionLevel,
    ) -> Comment:
        comment = Comment(
            post_id=post_id,
            user_id=user_id,
            p_comment_id=parent_comment_id,
            content=content,
            restriction_level=restriction_level,
            mod_status=ModerationStatus.ACTIVE,
        )
        self.session.add(comment)
        self.session.flush()
        return comment

    def update(self, comment: Comment, content: str) -> Comment:
        comment.content = content
        comment.updated_at = datetime.now(timezone.utc)
        self.session.flush()
        return comment

    def set_moderation_status(
        self,
        comment: Comment,
        mod_status: ModerationStatus,
    ) -> Comment:
        comment.mod_status = mod_status
        comment.updated_at = datetime.now(timezone.utc)
        self.session.flush()
        return comment
