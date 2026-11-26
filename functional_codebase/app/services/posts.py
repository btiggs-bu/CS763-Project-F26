from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.content import Post
from app.models.enums import (
    ModerationStatus,
    PostRestrictionLevel,
    PostType,
)
from app.models.user import User
from app.repositories.posts import PostRepository, PostUpdateValues
from app.repositories.threads import ThreadRepository
from app.repositories.users import UserRepository
from app.schemas.posts import PostCreate, PostUpdate
from app.schemas.queries import PostListQuery
from app.schemas.enums import ThreadType
from app.services.content_access import has_staff_role, require_thread_access
from app.services.persistence import write_transaction


class PostService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.posts = PostRepository(session)
        self.threads = ThreadRepository(session)
        self.users = UserRepository(session)

    def list_posts(self, query: PostListQuery) -> tuple[int, list[Post]]:
        return self.posts.list(
            keyword=query.keyword,
            thread_id=query.thread_id,
            user_id=query.user_id,
            post_type=query.post_type,
            tag_id=query.tag_id,
            mod_status=query.mod_status,
        )

    def get_post(self, post_id: int) -> Post:
        post = self.posts.get_by_id(post_id)
        if post is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Post {post_id} was not found",
            )
        return post

    def create_post(self, payload: PostCreate) -> Post:
        author = self._get_active_user(payload.user_id)
        thread = self.threads.get_by_id(payload.thread_id)
        if thread is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Thread {payload.thread_id} was not found",
            )

        if (
            payload.post_type == PostType.ANNOUNCEMENT
            and not has_staff_role(author)
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only Faculty or Admin users may create announcement posts",
            )
        if (
            "restriction_level" in payload.model_fields_set
            and payload.restriction_level != PostRestrictionLevel.INHERITED
            and not has_staff_role(author)
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only Faculty or Admin users may override post restrictions",
            )

        require_thread_access(
            author,
            thread,
            self.users.is_thread_member(author.user_id, thread.thread_id),
        )

        with write_transaction(self.session):
            post = self.posts.create(
                post_type=payload.post_type,
                user_id=payload.user_id,
                thread_id=payload.thread_id,
                title=payload.title,
                content=payload.content,
                restriction_level=payload.restriction_level,
                tag_names=payload.tags,
            )
            post_id = post.post_id
        return self.get_post(post_id)

    def update_post(self, post_id: int, payload: PostUpdate) -> Post:
        post = self.get_post(post_id)
        supplied = payload.model_fields_set
        changes: PostUpdateValues = {}
        if "title" in supplied:
            if payload.title is None:
                raise HTTPException(status_code=422, detail="title cannot be null")
            changes["title"] = payload.title
        if "content" in supplied:
            if payload.content is None:
                raise HTTPException(status_code=422, detail="content cannot be null")
            changes["content"] = payload.content
        if "restriction_level" in supplied:
            if payload.restriction_level is None:
                raise HTTPException(
                    status_code=422,
                    detail="restriction_level cannot be null",
                )
            if (
                payload.restriction_level != PostRestrictionLevel.INHERITED
                and not has_staff_role(post.author)
            ):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Only Faculty or Admin post authors may override restrictions",
                )
            changes["restriction_level"] = payload.restriction_level
        if not changes:
            return post

        with write_transaction(self.session):
            self.posts.update(post, changes)
        return self.get_post(post_id)

    def delete_post(self, post_id: int) -> None:
        post = self.get_post(post_id)
        with write_transaction(self.session):
            self.posts.delete(post)

    def report_post(self, post_id: int) -> Post:
        return self._set_moderation_status(post_id, ModerationStatus.REPORTED)

    def moderate_post(
        self,
        post_id: int,
        mod_status: ModerationStatus,
    ) -> Post:
        return self._set_moderation_status(post_id, mod_status)

    def get_timeline(
        self,
        thread_type: ThreadType,
        thread_id: int,
    ) -> tuple[int, list[Post]]:
        thread = self.threads.get_by_id(thread_id)
        if thread is None or thread.thread_type.value != thread_type.value:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="The requested thread was not found",
            )
        return self.posts.list(
            keyword=None,
            thread_id=thread_id,
            user_id=None,
            post_type=None,
            tag_id=None,
            mod_status=None,
            chronological=True,
        )

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
        mod_status: ModerationStatus,
    ) -> Post:
        post = self.get_post(post_id)
        with write_transaction(self.session):
            self.posts.set_moderation_status(post, mod_status)
        return self.get_post(post_id)
