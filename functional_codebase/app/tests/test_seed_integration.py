import pytest
from sqlalchemy import func, select

from app.db.database import SessionLocal
from app.models import (
    Comment,
    Post,
    Role,
    Tag,
    Thread,
    ThreadGroup,
    ThreadTag,
    User,
    UserRole,
)
from app.models.enums import (
    CommentRestrictionLevel,
    ModerationStatus,
    PostRestrictionLevel,
    PostType,
)
from app.seed import (
    populate_seed_data,
)

pytestmark = pytest.mark.integration


def _counts():
    models = {
        "roles": Role,
        "users": User,
        "user_roles": UserRole,
        "threads": Thread,
        "thread_groups": ThreadGroup,
        "thread_tags": ThreadTag,
        "tags": Tag,
        "posts": Post,
        "comments": Comment,
    }
    with SessionLocal() as session:
        return {
            name: session.scalar(select(func.count()).select_from(model))
            for name, model in models.items()
        }


def test_seed_data_is_idempotent_and_resettable():
    expected = {
        "roles": 3,
        "users": 3,
        "user_roles": 3,
        "threads": 5,
        "thread_groups": 4,
        "thread_tags": 3,
        "tags": 3,
        "posts": 2,
        "comments": 3,
    }

    populate_seed_data()
    assert _counts() == expected

    populate_seed_data()
    assert _counts() == expected

    with SessionLocal() as session:
        posts = session.scalars(select(Post)).all()
        assert {post.post_type for post in posts} == {
            PostType.DISCUSSION,
            PostType.ANNOUNCEMENT,
        }
        assert all(
            post.restriction_level == PostRestrictionLevel.INHERITED
            and post.mod_status == ModerationStatus.ACTIVE
            for post in posts
        )

        comments = session.scalars(select(Comment)).all()
        assert all(
            comment.restriction_level == CommentRestrictionLevel.INHERITED
            and comment.mod_status == ModerationStatus.ACTIVE
            for comment in comments
        )
        reply = next(comment for comment in comments if comment.parent_comment is not None)
        assert reply.parent_comment.post_id == reply.post_id

    populate_seed_data(reset=True)
    assert _counts() == expected

    populate_seed_data(clean=True)
    cleaned = _counts()
    assert cleaned == {
        **expected,
        "users": 0,
        "user_roles": 0,
        "threads": 0,
        "thread_groups": 0,
        "thread_tags": 0,
        "tags": 0,
        "posts": 0,
        "comments": 0,
    }
