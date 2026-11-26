from datetime import datetime, timezone

import pytest
from pydantic import TypeAdapter, ValidationError

from app.models.enums import (
    ModerationStatus,
    PostRestrictionLevel,
    PostType,
    RoleName,
    ThreadRestrictionLevel,
    ThreadType,
)
from app.models.content import Post
from app.models.tag import Tag
from app.models.thread import Course, Thread, ThreadGroup
from app.models.user import Role, User
from app.schemas import (
    CommentCreate,
    CommentListQuery,
    CommentRead,
    CommentUpdate,
    ErrorEnvelope,
    HealthRead,
    ModerationStatusUpdate,
    PostCreate,
    PostRead,
    PostUpdate,
    TagCreate,
    TagUpdate,
    ThreadCreate,
    ThreadRead,
    ThreadUpdate,
    UserCreate,
    UserRead,
    UserUpdate,
)


def test_user_schemas_validate_fields_and_partial_updates() -> None:
    user = UserCreate(
        username="researcher",
        email="researcher@example.edu",
        display_name="Researcher",
    )
    assert user.roles == []

    with pytest.raises(ValidationError):
        UserCreate(
            username="ab",
            email="reader@example.edu",
            display_name="Researcher",
        )
    with pytest.raises(ValidationError):
        UserCreate(
            username="researcher",
            email="not-an-email",
            display_name="Researcher",
        )
    with pytest.raises(ValidationError):
        UserCreate(
            username="researcher",
            email="reader@example.edu",
            display_name="x" * 101,
        )
    with pytest.raises(ValidationError):
        UserCreate(
            username="researcher",
            email="reader@example.edu",
            display_name="Researcher",
            roles=["invalid-role"],
        )
    with pytest.raises(ValidationError):
        UserCreate(
            username="researcher",
            email="reader@example.edu",
            display_name="Researcher",
            roles=["student", "student"],
        )

    with pytest.raises(ValidationError):
        UserUpdate()

    with pytest.raises(ValidationError):
        UserUpdate(email=None)


def test_thread_create_discriminates_types_and_validates_parent_shape() -> None:
    course = TypeAdapter(ThreadCreate).validate_python(
        {
            "thread_type": "course",
            "user_id": 1,
            "name": "Secure Software Development",
            "restriction_level": "open",
        }
    )
    assert course.thread_type is ThreadType.COURSE
    assert course.parent_thread_id is None

    with pytest.raises(ValidationError):
        TypeAdapter(ThreadCreate).validate_python(
            {
                "thread_type": "lab",
                "user_id": 1,
                "name": "Research Lab",
                "restriction_level": "open",
                "parent_thread_id": 5,
            }
        )
    with pytest.raises(ValidationError):
        TypeAdapter(ThreadCreate).validate_python(
            {
                "thread_type": "unknown",
                "user_id": 1,
                "name": "Research Lab",
                "restriction_level": "open",
            }
        )
    with pytest.raises(ValidationError):
        TypeAdapter(ThreadCreate).validate_python(
            {
                "thread_type": "lab",
                "user_id": 1,
                "name": "x" * 201,
                "restriction_level": "open",
            }
        )
    with pytest.raises(ValidationError):
        TypeAdapter(ThreadCreate).validate_python(
            {
                "thread_type": "lab",
                "user_id": 1,
                "name": "Research Lab",
                "description": "x" * 5001,
                "restriction_level": "open",
            }
        )

    with pytest.raises(ValidationError):
        ThreadUpdate()

    assert ThreadUpdate(description=None, parent_thread_id=None).description is None
    with pytest.raises(ValidationError):
        ThreadUpdate(name=None)


def test_post_comment_and_tag_field_constraints() -> None:
    PostCreate(
        post_type=PostType.DISCUSSION,
        user_id=1,
        thread_id=2,
        title="T",
        content="C",
    )
    with pytest.raises(ValidationError):
        PostCreate(
            post_type=PostType.DISCUSSION,
            user_id=1,
            thread_id=2,
            title="",
            content="C",
        )
    with pytest.raises(ValidationError):
        PostCreate(
            post_type=PostType.DISCUSSION,
            user_id=1,
            thread_id=2,
            title="T" * 201,
            content="C",
        )
    with pytest.raises(ValidationError):
        PostCreate(
            post_type=PostType.DISCUSSION,
            user_id=1,
            thread_id=2,
            title="T",
            content="x" * 10001,
        )
    with pytest.raises(ValidationError):
        PostCreate(
            post_type=PostType.DISCUSSION,
            user_id=1,
            thread_id=2,
            title="T",
            content="C",
            tags=["research", "research"],
        )
    with pytest.raises(ValidationError):
        PostUpdate()
    with pytest.raises(ValidationError):
        PostUpdate(title=None)

    CommentCreate(user_id=1, content="C")
    with pytest.raises(ValidationError):
        CommentCreate(user_id=1, content="x" * 5001)
    with pytest.raises(ValidationError):
        CommentCreate(user_id=1, post_id=2, content="C")
    with pytest.raises(ValidationError):
        CommentUpdate()

    with pytest.raises(ValidationError):
        TagCreate(tag="")
    with pytest.raises(ValidationError):
        TagCreate(tag="x" * 51)
    with pytest.raises(ValidationError):
        TagUpdate()
    with pytest.raises(ValidationError):
        TagUpdate(tag=None)


def test_comment_list_query_defaults_and_restricts_format() -> None:
    assert CommentListQuery().format == "json"
    assert CommentListQuery(format="txt").format == "txt"

    with pytest.raises(ValidationError):
        CommentListQuery(format="csv")
    with pytest.raises(ValidationError):
        CommentListQuery(format=None)


def test_response_schemas_read_orm_attributes_and_flatten_relationships() -> None:
    now = datetime.now(timezone.utc)
    user = User(
        user_id=1,
        username="reader",
        email="reader@example.edu",
        display_name="Reader",
        created_at=now,
        updated_at=now,
    )
    user.roles = [Role(role_id=1, role_name=RoleName.STUDENT)]
    assert UserRead.model_validate(user).roles == [RoleName.STUDENT]

    post = Post(
        post_id=2,
        post_type=PostType.DISCUSSION,
        user_id=1,
        thread_id=3,
        title="Title",
        content="Body",
        restriction_level=PostRestrictionLevel.INHERITED,
        mod_status=ModerationStatus.ACTIVE,
        created_at=now,
        updated_at=now,
    )
    post.tags = [Tag(tag_id=1, tag="research")]
    assert PostRead.model_validate(post).tags == ["research"]

    thread = Thread(
        thread_id=3,
        user_id=1,
        thread_type=ThreadType.COURSE,
        restriction_level=ThreadRestrictionLevel.OPEN,
        created_at=now,
        updated_at=now,
    )
    thread.course = Course(thread_id=3, name="Course", description=None)
    thread.child_link = ThreadGroup(
        p_thread_id=1,
        c_thread_id=3,
    )
    thread.tags = [Tag(tag_id=2, tag="semester")]

    response = ThreadRead.model_validate(thread)
    assert response.name == "Course"
    assert response.parent_thread_id == 1
    assert response.tags == ["semester"]


def test_common_response_and_moderation_schemas() -> None:
    now = datetime.now(timezone.utc)
    comment = CommentRead(
        comment_id=1,
        user_id=2,
        post_id=3,
        p_comment_id=None,
        content="Reply",
        restriction_level="inherited",
        mod_status="active",
        created_at=now,
        updated_at=now,
    )
    assert comment.restriction_level.value == "inherited"
    assert HealthRead(status="healthy").status == "healthy"
    assert ModerationStatusUpdate(mod_status="hidden_by_moderator").mod_status.value == (
        "hidden_by_moderator"
    )

    envelope = ErrorEnvelope.model_validate(
        {
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Request validation failed",
            },
            "timestamp": now,
            "request_id": "0f45ef7d-790a-4b82-b9fc-fd2c8afc8d5b",
        }
    )
    assert envelope.error.code.value == "VALIDATION_ERROR"
    with pytest.raises(ValidationError):
        ErrorEnvelope.model_validate(
            {
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Request validation failed",
                    "details": [],
                },
                "timestamp": now,
                "request_id": "0f45ef7d-790a-4b82-b9fc-fd2c8afc8d5b",
            }
        )
