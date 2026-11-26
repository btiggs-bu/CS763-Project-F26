import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session, sessionmaker

from app.models.enums import ModerationStatus, ThreadType
from app.schemas.comments import CommentCreate, CommentUpdate
from app.schemas.enums import PostType, ThreadRestrictionLevel
from app.schemas.posts import PostCreate, PostUpdate
from app.schemas.threads import LabThreadCreate
from app.schemas.users import UserCreate
from app.services.comments import CommentService
from app.services.posts import PostService
from app.services.threads import ThreadService
from app.services.users import UserService


def _create_content_fixture(session: Session) -> tuple[int, int]:
    user = UserService(session).create_user(
        UserCreate(
            username="content_service_user",
            email="content_service_user@example.edu",
            display_name="Content Service User",
        )
    )
    thread = ThreadService(session).create_thread(
        LabThreadCreate(
            user_id=user.user_id,
            name="Content Service Lab",
            restriction_level=ThreadRestrictionLevel.OPEN,
        )
    )
    return user.user_id, thread.thread_id


def test_post_service_validates_references_and_runs_lifecycle(
    session_factory: sessionmaker[Session],
) -> None:
    with session_factory() as session:
        user_id, thread_id = _create_content_fixture(session)
        service = PostService(session)

        with pytest.raises(HTTPException) as missing_user:
            service.create_post(
                PostCreate(
                    post_type=PostType.DISCUSSION,
                    user_id=99999,
                    thread_id=thread_id,
                    title="Missing author",
                    content="This must be rejected.",
                )
            )
        assert missing_user.value.status_code == 422

        with pytest.raises(HTTPException) as missing_thread:
            service.create_post(
                PostCreate(
                    post_type=PostType.DISCUSSION,
                    user_id=user_id,
                    thread_id=99999,
                    title="Missing thread",
                    content="This must be rejected.",
                )
            )
        assert missing_thread.value.status_code == 422

        post = service.create_post(
            PostCreate(
                post_type=PostType.DISCUSSION,
                user_id=user_id,
                thread_id=thread_id,
                title="Initial title",
                content="Initial content",
                tags=["service", "testing"],
            )
        )
        updated = service.update_post(
            post.post_id,
            PostUpdate(title="Updated title"),
        )
        assert updated.title == "Updated title"

        reported = service.report_post(post.post_id)
        assert reported.mod_status is ModerationStatus.REPORTED
        moderated = service.moderate_post(
            post.post_id,
            ModerationStatus.HIDDEN_BY_MODERATOR,
        )
        assert moderated.mod_status is ModerationStatus.HIDDEN_BY_MODERATOR

        count, timeline = service.get_timeline(ThreadType.LAB, thread_id)
        assert count == 1
        assert timeline[0].post_id == post.post_id
        with pytest.raises(HTTPException) as wrong_type:
            service.get_timeline(ThreadType.COURSE, thread_id)
        assert wrong_type.value.status_code == 404

        service.delete_post(post.post_id)
        with pytest.raises(HTTPException) as missing_post:
            service.get_post(post.post_id)
        assert missing_post.value.status_code == 404


def test_comment_service_validates_references_and_runs_nested_lifecycle(
    session_factory: sessionmaker[Session],
) -> None:
    with session_factory() as session:
        user_id, thread_id = _create_content_fixture(session)
        post = PostService(session).create_post(
            PostCreate(
                post_type=PostType.DISCUSSION,
                user_id=user_id,
                thread_id=thread_id,
                title="Comment service post",
                content="A post used by service tests.",
            )
        )
        service = CommentService(session)

        with pytest.raises(HTTPException) as missing_post:
            service.create_comment(
                99999,
                CommentCreate(user_id=user_id, content="Missing post"),
            )
        assert missing_post.value.status_code == 404

        with pytest.raises(HTTPException) as missing_user:
            service.create_comment(
                post.post_id,
                CommentCreate(user_id=99999, content="Missing author"),
            )
        assert missing_user.value.status_code == 422

        with pytest.raises(HTTPException) as missing_parent:
            service.create_comment(
                post.post_id,
                CommentCreate(
                    user_id=user_id,
                    p_comment_id=99999,
                    content="Missing parent",
                ),
            )
        assert missing_parent.value.status_code == 422

        root = service.create_comment(
            post.post_id,
            CommentCreate(user_id=user_id, content="Root comment"),
        )
        reply = service.create_comment(
            post.post_id,
            CommentCreate(
                user_id=user_id,
                p_comment_id=root.comment_id,
                content="Nested reply",
            ),
        )
        updated = service.update_comment(
            post.post_id,
            reply.comment_id,
            CommentUpdate(content="Updated nested reply"),
        )
        assert updated.content == "Updated nested reply"

        assert (
            service.report_comment(post.post_id, reply.comment_id).mod_status
            is ModerationStatus.REPORTED
        )
        assert (
            service.moderate_comment(
                post.post_id,
                reply.comment_id,
                ModerationStatus.HIDDEN_BY_MODERATOR,
            ).mod_status
            is ModerationStatus.HIDDEN_BY_MODERATOR
        )

        root_id = root.comment_id
        reply_id = reply.comment_id
        service.delete_comment(post.post_id, root_id)
        with pytest.raises(HTTPException) as deleted_reply:
            service.get_comment(post.post_id, reply_id)
        assert deleted_reply.value.status_code == 404
