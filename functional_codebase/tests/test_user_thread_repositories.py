import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from app.models.enums import ThreadRestrictionLevel, ThreadType, RoleName
from app.models.tag import Tag
from app.models.user import UserThread
from app.repositories.roles import RoleRepository
from app.repositories.threads import ThreadRepository
from app.repositories.users import UserRepository
from app.schemas.threads import ThreadRead


def test_repositories_load_and_filter_user_thread_associations(
    session_factory: sessionmaker[Session],
) -> None:
    with session_factory() as session:
        roles = RoleRepository(session).get_by_names(
            [RoleName.STUDENT, RoleName.FACULTY]
        )
        roles_by_name = {role.role_name: role for role in roles}
        users = UserRepository(session)
        owner = users.create(
            username="repository_owner",
            email="repository_owner@example.edu",
            display_name="Owner",
            roles=[roles_by_name[RoleName.FACULTY]],
        )
        member = users.create(
            username="repository_member",
            email="repository_member@example.edu",
            display_name="Member",
            roles=[roles_by_name[RoleName.STUDENT]],
        )
        thread_repository = ThreadRepository(session)
        lab = thread_repository.create(
            user_id=owner.user_id,
            thread_type=ThreadType.LAB,
            name="Repository Lab",
            description=None,
            restriction_level=ThreadRestrictionLevel.OPEN,
            parent_thread_id=None,
            tag_names=["repository", "security"],
        )
        course = thread_repository.create(
            user_id=owner.user_id,
            thread_type=ThreadType.COURSE,
            name="Repository Course",
            description=None,
            restriction_level=ThreadRestrictionLevel.OPEN,
            parent_thread_id=lab.thread_id,
            tag_names=[],
        )
        project = thread_repository.create(
            user_id=owner.user_id,
            thread_type=ThreadType.PROJECT,
            name="Repository Project",
            description="Project description",
            restriction_level=ThreadRestrictionLevel.RESTRICTED,
            parent_thread_id=course.thread_id,
            tag_names=["security"],
        )
        session.add(UserThread(user=member, thread=lab))
        session.commit()

        count, users_for_thread = users.list(role_id=None, thread_id=lab.thread_id)
        assert count == 2
        assert {user.user_id for user in users_for_thread} == {
            owner.user_id,
            member.user_id,
        }
        count, students_in_thread = users.list(
            role_id=roles_by_name[RoleName.STUDENT].role_id,
            thread_id=lab.thread_id,
        )
        assert count == 1
        assert students_in_thread[0].user_id == member.user_id

        security_tag_id = session.scalar(
            select(Tag.tag_id).where(Tag.tag == "security")
        )
        count, child_threads = thread_repository.list(
            user_id=owner.user_id,
            thread_type=ThreadType.PROJECT,
            restriction_level=ThreadRestrictionLevel.RESTRICTED,
            tag_id=security_tag_id,
            parent_thread_id=course.thread_id,
        )
        assert count == 1
        assert child_threads[0].thread_id == project.thread_id

        other_course = thread_repository.create(
            user_id=owner.user_id,
            thread_type=ThreadType.COURSE,
            name="Other Repository Course",
            description=None,
            restriction_level=ThreadRestrictionLevel.OPEN,
            parent_thread_id=lab.thread_id,
            tag_names=[],
        )
        thread_repository.update(
            project,
            {"parent_thread_id": other_course.thread_id, "tags": ["security", "new"]},
        )
        session.commit()

        reloaded = thread_repository.get_by_id(project.thread_id)
        assert reloaded is not None
        serialized = ThreadRead.model_validate(reloaded)
        assert serialized.parent_thread_id == other_course.thread_id
        assert serialized.tags == ["security", "new"]


def test_user_repository_database_unique_constraints(
    session_factory: sessionmaker[Session],
) -> None:
    with session_factory() as session:
        student = RoleRepository(session).get_by_names([RoleName.STUDENT])[0]
        users = UserRepository(session)
        users.create(
            username="unique_repository_user",
            email="unique_repository_user@example.edu",
            display_name="First",
            roles=[student],
        )
        session.commit()

        with pytest.raises(IntegrityError):
            users.create(
                username="another_repository_user",
                email="unique_repository_user@example.edu",
                display_name="Duplicate",
                roles=[student],
            )
        session.rollback()
