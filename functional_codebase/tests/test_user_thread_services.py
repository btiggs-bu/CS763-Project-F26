import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session, sessionmaker

from app.models.enums import ThreadType
from app.schemas.threads import (
    CourseThreadCreate,
    LabThreadCreate,
    ProjectThreadCreate,
    ThreadUpdate,
)
from app.schemas.users import UserCreate, UserUpdate
from app.services.threads import ThreadService
from app.services.users import UserService


def test_user_service_role_fallback_conflicts_and_soft_delete(
    session_factory: sessionmaker[Session],
) -> None:
    with session_factory() as session:
        service = UserService(session)
        payload = UserCreate(
            username="service_user",
            email="service_user@example.edu",
            display_name="Service User",
        )
        user = service.create_user(payload)
        assert [role.role_name.value for role in user.roles] == ["student"]

        with pytest.raises(HTTPException) as duplicate:
            service.create_user(payload)
        assert duplicate.value.status_code == 409

        updated = service.update_user(
            user.user_id,
            UserUpdate(roles=["faculty"], display_name="Updated"),
        )
        assert {role.role_name.value for role in updated.roles} == {"faculty"}

        service.delete_user(user.user_id)
        assert service.get_user(user.user_id).deleted_at is not None


def test_thread_service_validates_references_and_parent_types(
    session_factory: sessionmaker[Session],
) -> None:
    with session_factory() as session:
        user = UserService(session).create_user(
            UserCreate(
                username="thread_service_user",
                email="thread_service_user@example.edu",
                display_name="Thread Service User",
            )
        )
        service = ThreadService(session)

        with pytest.raises(HTTPException) as missing_user:
            service.create_thread(
                LabThreadCreate(
                    user_id=99999,
                    name="Missing Creator Lab",
                    restriction_level="open",
                )
            )
        assert missing_user.value.status_code == 422

        lab = service.create_thread(
            LabThreadCreate(
                user_id=user.user_id,
                name="Service Lab",
                restriction_level="open",
            )
        )
        course = service.create_thread(
            CourseThreadCreate(
                user_id=user.user_id,
                name="Service Course",
                restriction_level="open",
                parent_thread_id=lab.thread_id,
            )
        )
        with pytest.raises(HTTPException) as invalid_parent:
            service.create_thread(
                ProjectThreadCreate(
                    user_id=user.user_id,
                    name="Invalid Parent Project",
                    restriction_level="open",
                    parent_thread_id=lab.thread_id,
                )
            )
        assert invalid_parent.value.status_code == 422

        project = service.create_thread(
            ProjectThreadCreate(
                user_id=user.user_id,
                name="Service Project",
                restriction_level="restricted",
                parent_thread_id=course.thread_id,
            )
        )
        updated = service.update_thread(
            project.thread_id,
            ThreadUpdate(parent_thread_id=None, description="Updated description"),
        )
        assert updated.thread_type is ThreadType.PROJECT
        assert updated.child_link is None
        assert updated.project.description == "Updated description"

        service.delete_thread(project.thread_id)
        with pytest.raises(HTTPException) as missing_thread:
            service.get_thread(project.thread_id)
        assert missing_thread.value.status_code == 404
