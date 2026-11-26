from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.content import Comment, Post
from app.models.enums import (
    CommentRestrictionLevel,
    ModerationStatus,
    PostRestrictionLevel,
    ThreadRestrictionLevel,
)
from app.models.user import User
from app.repositories.comments import CommentRepository
from app.repositories.posts import PostRepository
from app.repositories.threads import ThreadRepository
from app.repositories.users import UserRepository
from app.schemas.comments import CommentCreate, CommentUpdate
from app.schemas.queries import CommentListQuery
from app.services.content_access import require_content_access
from app.services.persistence import write_transaction


class CommentService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.comments = CommentRepository(session)
        self.posts = PostRepository(session)
        self.threads = ThreadRepository(session)
        self.users = UserRepository(session)

    def list_comments(
        self,
        post_id: int,
        query: CommentListQuery,
    ) -> tuple[int, list[Comment]]:
        self._get_post(post_id)
        return self.comments.list(
            post_id=post_id,
            keyword=query.keyword,
            user_id=query.user_id,
            mod_status=query.mod_status,
        )

    def get_comment(self, post_id: int, comment_id: int) -> Comment:
        comment = self.comments.get_by_id(post_id, comment_id)
        if comment is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Comment {comment_id} was not found on post {post_id}",
            )
        return comment

    def create_comment(self, post_id: int, payload: CommentCreate) -> Comment:
        post = self._get_post(post_id)
        author = self._get_active_user(payload.user_id)
        thread = self.threads.get_by_id(post.thread_id)
        if thread is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="The post references a thread that does not exist",
            )
        if payload.p_comment_id is not None and self.comments.get_for_post(
            post_id, payload.p_comment_id
        ) is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="p_comment_id must reference a comment on this post",
            )

        if post.restriction_level == PostRestrictionLevel.INHERITED:
            effective_restriction = ThreadRestrictionLevel(
                thread.restriction_level.value
            )
        else:
            effective_restriction = ThreadRestrictionLevel(
                post.restriction_level.value
            )
        require_content_access(
            author,
            effective_restriction,
            self.users.is_thread_member(author.user_id, thread.thread_id),
        )

        with write_transaction(self.session):
            comment = self.comments.create(
                post_id=post_id,
                user_id=payload.user_id,
                parent_comment_id=payload.p_comment_id,
                content=payload.content,
                restriction_level=CommentRestrictionLevel(
                    post.restriction_level.value
                ),
            )
            comment_id = comment.comment_id
        return self.get_comment(post_id, comment_id)

    def update_comment(
        self,
        post_id: int,
        comment_id: int,
        payload: CommentUpdate,
    ) -> Comment:
        comment = self.get_comment(post_id, comment_id)
        if "content" not in payload.model_fields_set:
            return comment
        if payload.content is None:
            raise HTTPException(status_code=422, detail="content cannot be null")

        with write_transaction(self.session):
            self.comments.update(comment, payload.content)
        return self.get_comment(post_id, comment_id)

    def delete_comment(self, post_id: int, comment_id: int) -> None:
        comment = self.get_comment(post_id, comment_id)
        with write_transaction(self.session):
            self.comments.delete(comment)

    def report_comment(self, post_id: int, comment_id: int) -> Comment:
        return self._set_moderation_status(
            post_id,
            comment_id,
            ModerationStatus.REPORTED,
        )

    def moderate_comment(
        self,
        post_id: int,
        comment_id: int,
        mod_status: ModerationStatus,
    ) -> Comment:
        return self._set_moderation_status(post_id, comment_id, mod_status)

    def export_comments(self, comments: list[Comment]) -> str:
        blocks = []
        for comment in comments:
            created_at = comment.created_at
            timestamp = (
                created_at.isoformat()
                if isinstance(created_at, datetime)
                else str(created_at)
            )
            blocks.append(
                f"Comment {comment.comment_id} | User {comment.user_id} | "
                f"Created {timestamp}\n{comment.content}"
            )
        return "\n\n".join(blocks)

    def _get_post(self, post_id: int) -> Post:
        post = self.posts.get_by_id(post_id)
        if post is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Post {post_id} was not found",
            )
        return post

    def _get_active_user(self, user_id: int) -> User:
        user = self.users.get_by_id(user_id)
        if user is None or user.deleted_at is not None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="user_id must reference an active user",
            )
        return user

    def _set_moderation_status(
        self,
        post_id: int,
        comment_id: int,
        mod_status: ModerationStatus,
    ) -> Comment:
        comment = self.get_comment(post_id, comment_id)
        with write_transaction(self.session):
            self.comments.set_moderation_status(comment, mod_status)
        return self.get_comment(post_id, comment_id)
