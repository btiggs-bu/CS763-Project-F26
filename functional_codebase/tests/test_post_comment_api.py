from datetime import datetime, timezone

from sqlalchemy import select, update

from app.models.content import Comment, Post
from app.models.tag import Tag


def _create_user(client, suffix: str, role: str = "student") -> dict:
    response = client.post(
        "/api/v1/users",
        json={
            "username": f"content_{suffix}",
            "email": f"content_{suffix}@example.edu",
            "display_name": f"Content {suffix}",
        },
    )
    assert response.status_code == 201
    user = response.json()
    if role != "student":
        response = client.patch(
            f"/api/v1/users/{user['user_id']}",
            json={"roles": [role]},
        )
        assert response.status_code == 200
        user = response.json()
    return user


def _create_thread(client, user_id: int, restriction_level: str = "open") -> dict:
    response = client.post(
        "/api/v1/discussions/threads",
        json={
            "thread_type": "lab",
            "user_id": user_id,
            "name": "Systems Lab",
            "restriction_level": restriction_level,
        },
    )
    assert response.status_code == 201
    return response.json()


def test_post_comment_crud_filters_timeline_and_exports(api_context) -> None:
    client, session_factory = api_context
    user = _create_user(client, "crud")
    thread = _create_thread(client, user["user_id"])

    created_post = client.post(
        "/api/v1/discussions/posts",
        json={
            "post_type": "discussion",
            "user_id": user["user_id"],
            "thread_id": thread["thread_id"],
            "title": "Quantum systems",
            "content": "A discussion about distributed systems.",
            "tags": ["systems", "research"],
        },
    )
    assert created_post.status_code == 201
    post = created_post.json()
    assert post["restriction_level"] == "inherited"
    assert post["mod_status"] == "active"
    assert post["tags"] == ["systems", "research"]
    assert client.get(
        f"/api/v1/discussions/posts/{post['post_id']}"
    ).json()["post_id"] == post["post_id"]
    missing_author = client.post(
        "/api/v1/discussions/posts",
        json={
            "post_type": "discussion",
            "user_id": 99999,
            "thread_id": thread["thread_id"],
            "title": "Missing author",
            "content": "The author ID must reference an active user.",
        },
    )
    assert missing_author.status_code == 422
    missing_thread = client.post(
        "/api/v1/discussions/posts",
        json={
            "post_type": "discussion",
            "user_id": user["user_id"],
            "thread_id": 99999,
            "title": "Missing thread",
            "content": "The thread ID must reference an existing thread.",
        },
    )
    assert missing_thread.status_code == 422

    with session_factory() as session:
        systems_tag_id = session.scalar(
            select(Tag.tag_id).where(Tag.tag == "systems")
        )
    tagged_posts = client.get(
        "/api/v1/discussions/posts",
        params={
            "tag_id": systems_tag_id,
            "post_type": "discussion",
            "user_id": user["user_id"],
        },
    )
    assert [item["post_id"] for item in tagged_posts.json()["results"]] == [
        post["post_id"]
    ]

    updated_post = client.patch(
        f"/api/v1/discussions/posts/{post['post_id']}",
        json={"content": "Updated distributed systems discussion."},
    )
    assert updated_post.status_code == 200
    assert updated_post.json()["content"].startswith("Updated")
    assert updated_post.json()["updated_at"] != post["updated_at"]

    first_comment_response = client.post(
        f"/api/v1/discussions/posts/{post['post_id']}/comments",
        json={
            "user_id": user["user_id"],
            "content": "First comment.",
        },
    )
    assert first_comment_response.status_code == 201
    first_comment = first_comment_response.json()
    missing_comment_author = client.post(
        f"/api/v1/discussions/posts/{post['post_id']}/comments",
        json={
            "user_id": 99999,
            "content": "The author ID must reference an active user.",
        },
    )
    assert missing_comment_author.status_code == 422
    assert first_comment["restriction_level"] == "inherited"

    reply_response = client.post(
        f"/api/v1/discussions/posts/{post['post_id']}/comments",
        json={
            "user_id": user["user_id"],
            "p_comment_id": first_comment["comment_id"],
            "content": "A reply.",
        },
    )
    assert reply_response.status_code == 201
    reply = reply_response.json()
    assert reply["p_comment_id"] == first_comment["comment_id"]
    assert client.get(
        f"/api/v1/discussions/posts/{post['post_id']}/comments/{reply['comment_id']}"
    ).json()["comment_id"] == reply["comment_id"]

    wrong_parent = client.post(
        f"/api/v1/discussions/posts/{post['post_id']}/comments",
        json={"user_id": user["user_id"], "p_comment_id": 99999, "content": "No parent"},
    )
    assert wrong_parent.status_code == 422

    wrong_post_scope = client.get(
        f"/api/v1/discussions/posts/{post['post_id']}/comments/99999"
    )
    assert wrong_post_scope.status_code == 404

    updated_comment = client.patch(
        f"/api/v1/discussions/posts/{post['post_id']}/comments/{reply['comment_id']}",
        json={"content": "Edited reply."},
    )
    assert updated_comment.status_code == 200
    assert updated_comment.json()["content"] == "Edited reply."

    comment_list = client.get(
        f"/api/v1/discussions/posts/{post['post_id']}/comments",
        params={"keyword": "Edited"},
    )
    assert comment_list.status_code == 200
    assert comment_list.json()["count"] == 1
    assert comment_list.json()["results"][0]["comment_id"] == reply["comment_id"]

    text_export = client.get(
        f"/api/v1/discussions/posts/{post['post_id']}/comments",
        params={"format": "txt"},
    )
    assert text_export.status_code == 200
    assert text_export.headers["content-type"] == "text/plain; charset=utf-8"
    assert text_export.headers["content-disposition"] == (
        'attachment; filename="comments.txt"'
    )
    assert "Comment " + str(first_comment["comment_id"]) in text_export.text
    assert "Edited reply." in text_export.text

    post_list = client.get(
        "/api/v1/discussions/posts",
        params={"keyword": "Quantum", "thread_id": thread["thread_id"]},
    )
    assert post_list.status_code == 200
    assert post_list.json()["count"] == 1
    assert post_list.json()["results"][0]["post_id"] == post["post_id"]

    second_post = client.post(
        "/api/v1/discussions/posts",
        json={
            "post_type": "discussion",
            "user_id": user["user_id"],
            "thread_id": thread["thread_id"],
            "title": "Second timeline item",
            "content": "A later-created post.",
        },
    )
    assert second_post.status_code == 201
    second_post_id = second_post.json()["post_id"]
    with session_factory.begin() as session:
        session.execute(
            update(Post)
            .where(Post.post_id == post["post_id"])
            .values(created_at=datetime(2026, 11, 2, tzinfo=timezone.utc))
        )
        session.execute(
            update(Post)
            .where(Post.post_id == second_post_id)
            .values(created_at=datetime(2026, 11, 1, tzinfo=timezone.utc))
        )

    timeline = client.get(
        f"/api/v1/discussions/scopes/lab/{thread['thread_id']}/timeline"
    )
    assert timeline.status_code == 200
    timeline_results = timeline.json()["results"]
    assert timeline.json()["count"] == 2
    assert [item["post_id"] for item in timeline_results] == [
        second_post_id,
        post["post_id"],
    ]
    assert [item["created_at"] for item in timeline_results] == sorted(
        item["created_at"] for item in timeline_results
    )
    assert client.get(
        f"/api/v1/discussions/scopes/course/{thread['thread_id']}/timeline"
    ).status_code == 404
    assert client.get(
        f"/api/v1/discussions/scopes/unknown/{thread['thread_id']}/timeline"
    ).status_code == 422

    foreign_comment = client.post(
        f"/api/v1/discussions/posts/{second_post_id}/comments",
        json={"user_id": user["user_id"], "content": "Scoped to another post."},
    )
    assert foreign_comment.status_code == 201
    wrong_scope_report = client.patch(
        f"/api/v1/discussions/posts/{post['post_id']}/comments/"
        f"{foreign_comment.json()['comment_id']}/report"
    )
    assert wrong_scope_report.status_code == 404

    reported_comment = client.patch(
        f"/api/v1/discussions/posts/{post['post_id']}/comments/"
        f"{reply['comment_id']}/report"
    )
    assert reported_comment.status_code == 200
    assert reported_comment.json()["mod_status"] == "reported"
    assert set(reported_comment.json()) == {
        "comment_id",
        "mod_status",
        "updated_at",
    }
    assert reported_comment.json()["updated_at"] != updated_comment.json()["updated_at"]
    moderated_comment = client.patch(
        f"/api/v1/discussions/posts/{post['post_id']}/comments/"
        f"{reply['comment_id']}/moderation",
        json={"mod_status": "hidden_by_moderator"},
    )
    assert moderated_comment.status_code == 200
    assert moderated_comment.json()["mod_status"] == "hidden_by_moderator"
    hidden_comments = client.get(
        f"/api/v1/discussions/posts/{post['post_id']}/comments",
        params={"mod_status": "hidden_by_moderator", "user_id": user["user_id"]},
    )
    assert hidden_comments.json()["count"] == 1
    deleted_comment = client.delete(
        f"/api/v1/discussions/posts/{post['post_id']}/comments/{reply['comment_id']}"
    )
    assert deleted_comment.status_code == 204
    assert client.get(
        f"/api/v1/discussions/posts/{post['post_id']}/comments/{reply['comment_id']}"
    ).status_code == 404

    reported_post = client.patch(
        f"/api/v1/discussions/posts/{post['post_id']}/report"
    )
    assert reported_post.status_code == 200
    assert reported_post.json()["mod_status"] == "reported"
    assert set(reported_post.json()) == {"post_id", "mod_status", "updated_at"}
    assert reported_post.json()["updated_at"] != updated_post.json()["updated_at"]
    moderated_post = client.patch(
        f"/api/v1/discussions/posts/{post['post_id']}/moderation",
        json={"mod_status": "active"},
    )
    assert moderated_post.status_code == 200
    assert moderated_post.json()["mod_status"] == "active"
    assert moderated_post.json()["updated_at"] != reported_post.json()["updated_at"]
    assert client.patch(
        "/api/v1/discussions/posts/99999/report"
    ).status_code == 404
    assert client.patch(
        f"/api/v1/discussions/posts/{post['post_id']}/moderation",
        json={"mod_status": "unknown"},
    ).status_code == 422
    assert client.patch(
        f"/api/v1/discussions/posts/{post['post_id']}/comments/99999/moderation",
        json={"mod_status": "hidden_by_moderator"},
    ).status_code == 404

    deleted = client.delete(f"/api/v1/discussions/posts/{post['post_id']}")
    assert deleted.status_code == 204
    assert deleted.content == b""
    with session_factory() as session:
        assert session.scalar(
            select(Post).where(Post.post_id == post["post_id"])
        ) is None
        assert session.scalars(
            select(Comment).where(Comment.post_id == post["post_id"])
        ).all() == []

    openapi = client.get("/openapi.json").json()
    comment_path = "/api/v1/discussions/posts/{post_id}/comments"
    assert openapi["paths"][comment_path]["get"]["summary"] == "List comments"
    assert "text/plain" in openapi["paths"][comment_path]["get"]["responses"]["200"][
        "content"
    ]
    moderation_paths = {
        "/api/v1/discussions/posts/{post_id}/report": "patch",
        "/api/v1/discussions/posts/{post_id}/moderation": "patch",
        "/api/v1/discussions/posts/{post_id}/comments/{comment_id}/report": "patch",
        "/api/v1/discussions/posts/{post_id}/comments/{comment_id}/moderation": "patch",
        "/api/v1/discussions/scopes/{thread_type}/{thread_id}/timeline": "get",
    }
    for path, method in moderation_paths.items():
        assert path in openapi["paths"]
        assert "200" in openapi["paths"][path][method]["responses"]


def test_post_and_comment_restrictions_and_announcement_role(api_context) -> None:
    client, _ = api_context
    owner = _create_user(client, "restricted-owner")
    other_student = _create_user(client, "restricted-other")
    faculty = _create_user(client, "restricted-faculty", "faculty")
    thread = _create_thread(
        client,
        owner["user_id"],
        restriction_level="restricted",
    )

    denied_post = client.post(
        "/api/v1/discussions/posts",
        json={
            "post_type": "discussion",
            "user_id": other_student["user_id"],
            "thread_id": thread["thread_id"],
            "title": "Not allowed",
            "content": "Not a member",
        },
    )
    assert denied_post.status_code == 403

    student_announcement = client.post(
        "/api/v1/discussions/posts",
        json={
            "post_type": "announcement",
            "user_id": owner["user_id"],
            "thread_id": thread["thread_id"],
            "title": "Student announcement",
            "content": "Not allowed",
        },
    )
    assert student_announcement.status_code == 403

    faculty_post = client.post(
        "/api/v1/discussions/posts",
        json={
            "post_type": "announcement",
            "user_id": faculty["user_id"],
            "thread_id": thread["thread_id"],
            "title": "Faculty announcement",
            "content": "Faculty can post here.",
            "restriction_level": "restricted",
        },
    )
    assert faculty_post.status_code == 201
    post_id = faculty_post.json()["post_id"]

    denied_comment = client.post(
        f"/api/v1/discussions/posts/{post_id}/comments",
        json={
            "user_id": other_student["user_id"],
            "content": "Not a member.",
        },
    )
    assert denied_comment.status_code == 403

    open_post = client.post(
        "/api/v1/discussions/posts",
        json={
            "post_type": "discussion",
            "user_id": faculty["user_id"],
            "thread_id": thread["thread_id"],
            "title": "Open override",
            "content": "Faculty may override the thread restriction.",
            "restriction_level": "open",
        },
    )
    assert open_post.status_code == 201
    allowed_comment = client.post(
        f"/api/v1/discussions/posts/{open_post.json()['post_id']}/comments",
        json={
            "user_id": other_student["user_id"],
            "content": "Open post override permits this.",
        },
    )
    assert allowed_comment.status_code == 201
