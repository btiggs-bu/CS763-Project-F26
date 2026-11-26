from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from app.models.content import Comment, Post
from app.models.enums import (
    CommentRestrictionLevel,
    ModerationStatus,
    PostRestrictionLevel,
    PostType,
    RoleName,
    ThreadRestrictionLevel,
    ThreadType,
)
from app.models.tag import Tag
from app.repositories.comments import CommentRepository
from app.repositories.posts import PostRepository
from app.repositories.roles import RoleRepository
from app.repositories.threads import ThreadRepository
from app.repositories.users import UserRepository


def test_post_repository_create_filter_update_moderate_and_delete(
    session_factory: sessionmaker[Session],
) -> None:
    with session_factory() as session:
        student = RoleRepository(session).get_by_names([RoleName.STUDENT])[0]
        user = UserRepository(session).create(
            username="post_repository_user",
            email="post_repository_user@example.edu",
            display_name="Post Repository User",
            roles=[student],
        )
        thread = ThreadRepository(session).create(
            user_id=user.user_id,
            thread_type=ThreadType.LAB,
            name="Post Repository Lab",
            description=None,
            restriction_level=ThreadRestrictionLevel.OPEN,
            parent_thread_id=None,
            tag_names=[],
        )
        posts = PostRepository(session)
        first = posts.create(
            post_type=PostType.DISCUSSION,
            user_id=user.user_id,
            thread_id=thread.thread_id,
            title="Repository search term",
            content="The first post body.",
            restriction_level=PostRestrictionLevel.INHERITED,
            tag_names=["repository-tag"],
        )
        second = posts.create(
            post_type=PostType.ANNOUNCEMENT,
            user_id=user.user_id,
            thread_id=thread.thread_id,
            title="Another post",
            content="An announcement body.",
            restriction_level=PostRestrictionLevel.INHERITED,
            tag_names=[],
        )
        session.commit()

        tag_id = session.scalar(
            select(Tag.tag_id).where(Tag.tag == "repository-tag")
        )
        count, filtered = posts.list(
            keyword="search term",
            thread_id=thread.thread_id,
            user_id=user.user_id,
            post_type=PostType.DISCUSSION,
            tag_id=tag_id,
            mod_status=ModerationStatus.ACTIVE,
        )
        assert count == 1
        assert filtered[0].post_id == first.post_id
        assert posts.get_by_id(first.post_id).tags[0].tag == "repository-tag"

        posts.update(first, {"title": "Updated repository post"})
        posts.set_moderation_status(first, ModerationStatus.REPORTED)
        session.commit()
        assert posts.get_by_id(first.post_id).title == "Updated repository post"
        assert posts.get_by_id(first.post_id).mod_status is ModerationStatus.REPORTED

        posts.delete(second)
        session.commit()
        assert posts.get_by_id(second.post_id) is None


def test_comment_repository_scopes_nested_comments_and_filters(
    session_factory: sessionmaker[Session],
) -> None:
    with session_factory() as session:
        student = RoleRepository(session).get_by_names([RoleName.STUDENT])[0]
        user = UserRepository(session).create(
            username="comment_repository_user",
            email="comment_repository_user@example.edu",
            display_name="Comment Repository User",
            roles=[student],
        )
        thread = ThreadRepository(session).create(
            user_id=user.user_id,
            thread_type=ThreadType.LAB,
            name="Comment Repository Lab",
            description=None,
            restriction_level=ThreadRestrictionLevel.OPEN,
            parent_thread_id=None,
            tag_names=[],
        )
        post = PostRepository(session).create(
            post_type=PostType.DISCUSSION,
            user_id=user.user_id,
            thread_id=thread.thread_id,
            title="Comment repository post",
            content="Post body.",
            restriction_level=PostRestrictionLevel.INHERITED,
            tag_names=[],
        )
        other_post = PostRepository(session).create(
            post_type=PostType.DISCUSSION,
            user_id=user.user_id,
            thread_id=thread.thread_id,
            title="Other comment post",
            content="Another body.",
            restriction_level=PostRestrictionLevel.INHERITED,
            tag_names=[],
        )
        comments = CommentRepository(session)
        root = comments.create(
            post_id=post.post_id,
            user_id=user.user_id,
            parent_comment_id=None,
            content="Root repository comment.",
            restriction_level=CommentRestrictionLevel.INHERITED,
        )
        reply = comments.create(
            post_id=post.post_id,
            user_id=user.user_id,
            parent_comment_id=root.comment_id,
            content="Nested repository reply.",
            restriction_level=CommentRestrictionLevel.INHERITED,
        )
        unrelated = comments.create(
            post_id=other_post.post_id,
            user_id=user.user_id,
            parent_comment_id=None,
            content="Other post comment.",
            restriction_level=CommentRestrictionLevel.INHERITED,
        )
        session.commit()

        count, filtered = comments.list(
            post_id=post.post_id,
            keyword="Nested",
            user_id=user.user_id,
            mod_status=ModerationStatus.ACTIVE,
        )
        assert count == 1
        assert filtered[0].comment_id == reply.comment_id
        assert comments.get_by_id(post.post_id, unrelated.comment_id) is None
        assert comments.get_by_id(post.post_id, reply.comment_id).p_comment_id == (
            root.comment_id
        )

        comments.update(reply, "Updated nested reply.")
        comments.set_moderation_status(reply, ModerationStatus.REPORTED)
        session.commit()
        assert comments.get_by_id(post.post_id, reply.comment_id).content == (
            "Updated nested reply."
        )
        assert comments.get_by_id(
            post.post_id, reply.comment_id
        ).mod_status is ModerationStatus.REPORTED

        root_id = root.comment_id
        reply_id = reply.comment_id
        comments.delete(root)
        session.commit()
        assert session.get(Comment, root_id) is None
        assert session.get(Comment, reply_id) is None
