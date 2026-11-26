from fastapi.testclient import TestClient
from sqlalchemy import select

from app.models.content import Comment, Post
from app.models.enums import (
    CommentRestrictionLevel,
    ModerationStatus,
    PostRestrictionLevel,
    PostType,
    RoleName,
    ThreadRestrictionLevel,
)
from app.models.tag import Tag
from app.models.thread import Thread
from app.models.user import Role


def _create_user(client: TestClient, suffix: str = "one") -> dict:
    response = client.post(
        "/api/v1/users",
        json={
            "username": f"researcher_{suffix}",
            "email": f"researcher_{suffix}@example.edu",
            "display_name": f"Researcher {suffix}",
        },
    )
    assert response.status_code == 201
    return response.json()


def test_user_crud_duplicate_checks_role_filters_and_soft_delete(api_context) -> None:
    client, session_factory = api_context
    user = _create_user(client)
    user_id = user["user_id"]
    assert user["roles"] == ["student"]

    duplicate = client.post(
        "/api/v1/users",
        json={
            "username": "researcher_one",
            "email": "other@example.edu",
            "display_name": "Duplicate",
        },
    )
    assert duplicate.status_code == 409
    assert duplicate.json()["error"]["code"] == "HTTP_ERROR"
    invalid_request = client.post(
        "/api/v1/users",
        json={
            "username": "invalid_email",
            "email": "not-an-email",
            "display_name": "Invalid Email",
        },
    )
    assert invalid_request.status_code == 422
    assert invalid_request.json()["error"]["code"] == "VALIDATION_ERROR"

    second_user = _create_user(client, "two")
    duplicate_email = client.post(
        "/api/v1/users",
        json={
            "username": "researcher_three",
            "email": "researcher_two@example.edu",
            "display_name": "Duplicate Email",
        },
    )
    assert duplicate_email.status_code == 409

    update = client.patch(
        f"/api/v1/users/{user_id}",
        json={
            "email": "updated@example.edu",
            "display_name": "Updated Researcher",
            "roles": ["faculty"],
        },
    )
    assert update.status_code == 200
    assert update.json()["email"] == "updated@example.edu"
    assert update.json()["roles"] == ["faculty"]
    assert update.json()["updated_at"] != user["updated_at"]

    duplicate_email = client.patch(
        f"/api/v1/users/{second_user['user_id']}",
        json={"email": "updated@example.edu"},
    )
    assert duplicate_email.status_code == 409

    with session_factory() as session:
        faculty_role_id = session.scalar(
            select(Role.role_id).where(Role.role_name == RoleName.FACULTY)
        )
    filtered_users = client.get(
        "/api/v1/users",
        params={"role_id": faculty_role_id},
    )
    assert filtered_users.status_code == 200
    assert [item["user_id"] for item in filtered_users.json()["results"]] == [user_id]
    keep_faculty_role = client.patch(
        f"/api/v1/users/{user_id}",
        json={"roles": ["faculty", "student"]},
    )
    assert keep_faculty_role.status_code == 200
    assert set(keep_faculty_role.json()["roles"]) == {"faculty", "student"}
    reset_roles = client.patch(
        f"/api/v1/users/{user_id}",
        json={"roles": []},
    )
    assert reset_roles.status_code == 200
    assert reset_roles.json()["roles"] == ["student"]

    thread_response = client.post(
        "/api/v1/discussions/threads",
        json={
            "thread_type": "lab",
            "user_id": user_id,
            "name": "Research Lab",
            "restriction_level": "open",
        },
    )
    assert thread_response.status_code == 201
    thread_id = thread_response.json()["thread_id"]
    associated_users = client.get(
        "/api/v1/users",
        params={"thread_id": thread_id},
    )
    assert [item["user_id"] for item in associated_users.json()["results"]] == [
        user_id
    ]
    with session_factory.begin() as session:
        post = Post(
            post_type=PostType.DISCUSSION,
            user_id=user_id,
            thread_id=thread_id,
            title="Research discussion",
            content="Discussion content",
            restriction_level=PostRestrictionLevel.INHERITED,
            mod_status=ModerationStatus.ACTIVE,
        )
        session.add(post)
        session.flush()
        session.add(
            Comment(
                user_id=user_id,
                post_id=post.post_id,
                content="Comment content",
                restriction_level=CommentRestrictionLevel.INHERITED,
                mod_status=ModerationStatus.ACTIVE,
            )
        )

    deleted = client.delete(f"/api/v1/users/{user_id}")
    assert deleted.status_code == 204
    assert deleted.content == b""
    assert client.delete(f"/api/v1/users/{user_id}").status_code == 204
    assert client.get(f"/api/v1/users/{user_id}").json()["deleted_at"] is not None

    with session_factory() as session:
        assert session.get(Thread, thread_id).restriction_level is ThreadRestrictionLevel.CLOSED
        assert session.scalar(
            select(Post).where(Post.user_id == user_id)
        ).restriction_level is PostRestrictionLevel.CLOSED
        assert session.scalar(
            select(Comment).where(Comment.user_id == user_id)
        ).restriction_level is CommentRestrictionLevel.CLOSED


def test_thread_crud_parent_hierarchy_tags_filters_and_cascade(api_context) -> None:
    client, session_factory = api_context
    user = _create_user(client, "threads")
    user_id = user["user_id"]

    invalid_creator = client.post(
        "/api/v1/discussions/threads",
        json={
            "thread_type": "lab",
            "user_id": 99999,
            "name": "Orphan Lab",
            "restriction_level": "open",
        },
    )
    assert invalid_creator.status_code == 422

    lab_response = client.post(
        "/api/v1/discussions/threads",
        json={
            "thread_type": "lab",
            "user_id": user_id,
            "name": "Research Lab",
            "restriction_level": "open",
            "tags": ["systems", "security"],
        },
    )
    assert lab_response.status_code == 201
    lab = lab_response.json()
    assert lab["tags"] == ["systems", "security"]

    course_response = client.post(
        "/api/v1/discussions/threads",
        json={
            "thread_type": "course",
            "user_id": user_id,
            "name": "Secure Software",
            "restriction_level": "restricted",
            "parent_thread_id": lab["thread_id"],
        },
    )
    assert course_response.status_code == 201
    course = course_response.json()
    second_course_response = client.post(
        "/api/v1/discussions/threads",
        json={
            "thread_type": "course",
            "user_id": user_id,
            "name": "Advanced Secure Software",
            "restriction_level": "open",
            "parent_thread_id": lab["thread_id"],
        },
    )
    assert second_course_response.status_code == 201
    second_course = second_course_response.json()

    invalid_parent = client.post(
        "/api/v1/discussions/threads",
        json={
            "thread_type": "project",
            "user_id": user_id,
            "name": "Invalid Project",
            "restriction_level": "open",
            "parent_thread_id": lab["thread_id"],
        },
    )
    assert invalid_parent.status_code == 422

    project_response = client.post(
        "/api/v1/discussions/threads",
        json={
            "thread_type": "project",
            "user_id": user_id,
            "name": "Research Project",
            "description": "Initial description",
            "restriction_level": "open",
            "parent_thread_id": course["thread_id"],
            "tags": ["security"],
        },
    )
    assert project_response.status_code == 201
    project = project_response.json()
    assert project["parent_thread_id"] == course["thread_id"]
    assert client.get(
        f"/api/v1/discussions/threads/{project['thread_id']}"
    ).json()["thread_id"] == project["thread_id"]
    invalid_parent_update = client.patch(
        f"/api/v1/discussions/threads/{project['thread_id']}",
        json={"parent_thread_id": lab["thread_id"]},
    )
    assert invalid_parent_update.status_code == 422
    reparented = client.patch(
        f"/api/v1/discussions/threads/{project['thread_id']}",
        json={"parent_thread_id": second_course["thread_id"]},
    )
    assert reparented.status_code == 200
    assert reparented.json()["parent_thread_id"] == second_course["thread_id"]

    with session_factory() as session:
        security_tag_id = session.scalar(
            select(Tag.tag_id).where(Tag.tag == "security")
        )
    children = client.get(
        "/api/v1/discussions/threads",
        params={
            "parent_thread_id": second_course["thread_id"],
            "tag_id": security_tag_id,
        },
    )
    assert children.status_code == 200
    assert [item["thread_id"] for item in children.json()["results"]] == [
        project["thread_id"]
    ]

    update = client.patch(
        f"/api/v1/discussions/threads/{project['thread_id']}",
        json={
            "description": None,
            "parent_thread_id": None,
            "tags": ["security", "updated"],
        },
    )
    assert update.status_code == 200
    assert update.json()["description"] is None
    assert update.json()["parent_thread_id"] is None
    assert update.json()["tags"] == ["security", "updated"]
    assert update.json()["updated_at"] != project["updated_at"]

    with session_factory.begin() as session:
        post = Post(
            post_type=PostType.DISCUSSION,
            user_id=user_id,
            thread_id=project["thread_id"],
            title="Dependent post",
            content="This post should cascade",
        )
        session.add(post)
        session.flush()
        session.add(
            Comment(
                user_id=user_id,
                post_id=post.post_id,
                content="Dependent comment",
            )
        )
    deleted = client.delete(f"/api/v1/discussions/threads/{project['thread_id']}")
    assert deleted.status_code == 204
    assert deleted.content == b""

    with session_factory() as session:
        assert session.get(Thread, project["thread_id"]) is None
        assert session.scalar(
            select(Post).where(Post.title == "Dependent post")
        ) is None
        assert session.scalar(
            select(Comment).where(Comment.content == "Dependent comment")
        ) is None

    assert client.get("/api/v1/discussions/threads/99999").status_code == 404
    openapi = client.get("/openapi.json").json()
    assert openapi["paths"]["/api/v1/users"]["get"]["summary"] == "List users"
    assert (
        openapi["paths"]["/api/v1/discussions/threads"]["post"]["summary"]
        == "Create a thread"
    )
    assert "409" in openapi["paths"]["/api/v1/discussions/threads"]["post"]["responses"]
