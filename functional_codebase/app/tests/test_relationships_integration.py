import pytest
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError

from app.db.database import SessionLocal
from app.models import (
    Comment,
    Course,
    Lab,
    Post,
    PostTag,
    Project,
    Tag,
    User,
    UserThread,
)
from app.models.enums import RoleName
from app.seed import (
    SEED_POSTS,
    SEED_PROJECT_NAMES,
    SEED_TAG_NAMES,
    SEED_USER_EMAILS,
    populate_seed_data,
)

pytestmark = pytest.mark.integration


def test_orm_relationships_round_trip():
    populate_seed_data()
    with SessionLocal.begin() as session:
        student = session.scalar(
            select(User).where(User.email == SEED_USER_EMAILS[0])
        )
        project = session.scalar(
            select(Project).where(Project.name == SEED_PROJECT_NAMES[0])
        )
        project.thread.memberships.append(UserThread(user=student))

        discussion = session.scalar(
            select(Post).where(Post.title == SEED_POSTS[0][0])
        )
        project_tag = session.scalar(
            select(Tag).where(Tag.tag == SEED_TAG_NAMES[2])
        )
        discussion.tag_assignments.append(PostTag(tag=project_tag))

    with SessionLocal() as session:
        student = session.scalar(
            select(User).where(User.email == SEED_USER_EMAILS[0])
        )
        faculty = session.scalar(
            select(User).where(User.email == SEED_USER_EMAILS[1])
        )
        assert {role.role_name for role in student.roles} == {RoleName.STUDENT}
        assert student in student.roles[0].users
        assert student.role_assignments[0].role.role_name == RoleName.STUDENT

        project = session.scalar(
            select(Project).where(Project.name == SEED_PROJECT_NAMES[0])
        )
        project_thread = project.thread
        assert project_thread.project is project
        assert project_thread.creator is student
        assert project_thread in student.created_threads
        assert project_thread in student.member_threads
        assert student in project_thread.member_users
        assert student.memberships[0].thread is project_thread

        lab = session.scalar(select(Lab).where(Lab.name == "RBPDB Seed Lab"))
        course = session.scalar(
            select(Course).where(Course.name == "RBPDB Seed Course A")
        )
        assert lab.thread.lab is lab
        assert course.thread.course is course
        assert len(lab.thread.parent_links) == 2
        assert all(link.parent_thread is lab.thread for link in lab.thread.parent_links)
        assert project_thread.child_link.parent_thread.course is course

        discussion = session.scalar(
            select(Post).where(Post.title == SEED_POSTS[0][0])
        )
        assert discussion.author is student
        assert discussion in student.posts
        assert len(discussion.comments) == 2
        reply = next(
            comment
            for comment in discussion.comments
            if comment.parent_comment is not None
        )
        assert reply.parent_comment.post is discussion
        assert reply in reply.parent_comment.replies
        assert any(comment.author is faculty for comment in discussion.comments)

        project_tag = session.scalar(
            select(Tag).where(Tag.tag == SEED_TAG_NAMES[2])
        )
        assert project_tag in project_thread.tags
        assert project_thread in project_tag.threads
        assert project_thread.tag_assignments[0].tag is project_tag
        assert discussion in project_tag.posts
        assert project_tag.post_assignments[0].post is discussion


def test_database_constraints_and_triggers_enforce_erd_rules(database_engine):
    populate_seed_data()
    with SessionLocal() as session:
        student_id = session.scalar(
            select(User.user_id).where(User.email == SEED_USER_EMAILS[0])
        )
        discussion = session.scalar(
            select(Post).where(Post.title == SEED_POSTS[0][0])
        )
        announcement = session.scalar(
            select(Post).where(Post.title == SEED_POSTS[1][0])
        )
        parent_comment_id = session.scalar(
            select(Comment.comment_id).where(
                Comment.post_id == discussion.post_id,
                Comment.p_comment_id.is_(None),
            )
        )
        project_id = session.scalar(
            select(Project.thread_id).where(Project.name == SEED_PROJECT_NAMES[0])
        )
        lab_id = session.scalar(
            select(Lab.thread_id).where(Lab.name == "RBPDB Seed Lab")
        )
        discussion_id = discussion.post_id
        announcement_id = announcement.post_id

    with pytest.raises(IntegrityError):
        with database_engine.begin() as connection:
            connection.execute(
                text(
                    """
                    INSERT INTO comments (user_id, post_id, p_comment_id, content)
                    VALUES (:user_id, :post_id, :parent_id, 'invalid cross-post reply')
                    """
                ),
                {
                    "user_id": student_id,
                    "post_id": announcement_id,
                    "parent_id": parent_comment_id,
                },
            )

    with pytest.raises(IntegrityError):
        with database_engine.begin() as connection:
            connection.execute(
                text(
                    """
                    INSERT INTO threads_group (p_thread_id, c_thread_id)
                    VALUES (:parent_id, :child_id)
                    """
                ),
                {"parent_id": project_id, "child_id": lab_id},
            )

    with pytest.raises(IntegrityError):
        with database_engine.begin() as connection:
            mismatched_thread_id = connection.scalar(
                text(
                    """
                    INSERT INTO threads (user_id, thread_type, restriction_level)
                    VALUES (:user_id, 'project', 'restricted')
                    RETURNING thread_id
                    """
                ),
                {"user_id": student_id},
            )
            connection.execute(
                text(
                    "INSERT INTO course (thread_id, name) "
                    "VALUES (:thread_id, 'mismatched subtype')"
                ),
                {"thread_id": mismatched_thread_id},
            )

    with pytest.raises(IntegrityError):
        with database_engine.begin() as connection:
            connection.execute(
                text("DELETE FROM roles WHERE role_name = 'student'")
            )

    with database_engine.begin() as connection:
        rows = (
            ("users", "user_id", student_id),
            (
                "threads",
                "thread_id",
                project_id,
            ),
            ("posts", "post_id", discussion_id),
            ("comments", "comment_id", parent_comment_id),
        )
        for table_name, primary_key, row_id in rows:
            connection.execute(
                text(
                    f"UPDATE {table_name} SET updated_at = "
                    f"'2000-01-01 00:00:00+00' WHERE {primary_key} = :row_id"
                ),
                {"row_id": row_id},
            )
            updated_at = connection.scalar(
                text(
                    f"SELECT updated_at FROM {table_name} "
                    f"WHERE {primary_key} = :row_id"
                ),
                {"row_id": row_id},
            )
            assert updated_at.year > 2000
