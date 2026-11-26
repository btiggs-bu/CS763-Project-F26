from collections.abc import Sequence
from datetime import datetime, timezone
from typing_extensions import NotRequired, TypedDict

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models.content import Post
from app.models.enums import ModerationStatus, PostRestrictionLevel, PostType
from app.models.tag import PostTag
from app.models.user import User
from app.repositories.base import BaseRepository
from app.repositories.search import full_text_filter
from app.repositories.tags import TagRepository


class PostUpdateValues(TypedDict):
    title: NotRequired[str]
    content: NotRequired[str]
    restriction_level: NotRequired[PostRestrictionLevel]


_POST_LOAD_OPTIONS = (
    selectinload(Post.tags),
    selectinload(Post.author).selectinload(User.roles),
    selectinload(Post.thread),
)


class PostRepository(BaseRepository[Post]):
    def __init__(self, session: Session) -> None:
        super().__init__(session, Post)
        self.tags = TagRepository(session)

    def get_by_id(self, post_id: int) -> Post | None:
        statement = (
            select(Post)
            .options(*_POST_LOAD_OPTIONS)
            .where(Post.post_id == post_id)
        )
        return self.session.scalar(statement)

    def list(
        self,
        *,
        keyword: str | None,
        thread_id: int | None,
        user_id: int | None,
        post_type: PostType | None,
        tag_id: int | None,
        mod_status: ModerationStatus | None,
        chronological: bool = False,
    ) -> tuple[int, list[Post]]:
        filters = []
        if keyword:
            filters.append(
                full_text_filter(self.session, (Post.title, Post.content), keyword)
            )
        if thread_id is not None:
            filters.append(Post.thread_id == thread_id)
        if user_id is not None:
            filters.append(Post.user_id == user_id)
        if post_type is not None:
            filters.append(Post.post_type == post_type)
        if tag_id is not None:
            filters.append(Post.tag_assignments.any(PostTag.tag_id == tag_id))
        if mod_status is not None:
            filters.append(Post.mod_status == mod_status)

        total = self.session.scalar(
            select(func.count(Post.post_id)).where(*filters)
        ) or 0
        statement = (
            select(Post)
            .options(*_POST_LOAD_OPTIONS)
            .where(*filters)
        )
        if chronological:
            statement = statement.order_by(Post.created_at, Post.post_id)
        else:
            statement = statement.order_by(Post.created_at.desc(), Post.post_id.desc())
        return total, list(self.session.scalars(statement).unique().all())

    def create(
        self,
        *,
        post_type: PostType,
        user_id: int,
        thread_id: int,
        title: str,
        content: str,
        restriction_level: PostRestrictionLevel,
        tag_names: Sequence[str],
    ) -> Post:
        post = Post(
            post_type=post_type,
            user_id=user_id,
            thread_id=thread_id,
            title=title,
            content=content,
            restriction_level=restriction_level,
            mod_status=ModerationStatus.ACTIVE,
        )
        tags = self.tags.get_or_create_by_names(tag_names)
        post.tag_assignments = [PostTag(tag=tag) for tag in tags]
        self.session.add(post)
        self.session.flush()
        return post

    def update(self, post: Post, values: PostUpdateValues) -> Post:
        if "title" in values:
            post.title = values["title"]
        if "content" in values:
            post.content = values["content"]
        if "restriction_level" in values:
            post.restriction_level = values["restriction_level"]
        post.updated_at = datetime.now(timezone.utc)
        self.session.flush()
        return post

    def set_moderation_status(
        self,
        post: Post,
        mod_status: ModerationStatus,
    ) -> Post:
        post.mod_status = mod_status
        post.updated_at = datetime.now(timezone.utc)
        self.session.flush()
        return post
