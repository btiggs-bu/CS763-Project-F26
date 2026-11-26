from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.users import get_db
from app.db.database import Base
from app.main import app
from app.models.enums import RoleName
from app.models.user import Role


@pytest.fixture
def session_factory() -> Iterator[sessionmaker[Session]]:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def enable_foreign_keys(connection, _) -> None:
        connection.execute("PRAGMA foreign_keys=ON")

    Base.metadata.create_all(engine)
    Base.registry.configure()
    factory = sessionmaker(bind=engine, autoflush=False)
    with factory.begin() as session:
        session.add_all(
            [
                Role(role_name=RoleName.STUDENT),
                Role(role_name=RoleName.FACULTY),
                Role(role_name=RoleName.ADMIN),
            ]
        )

    try:
        yield factory
    finally:
        Base.metadata.drop_all(engine)
        engine.dispose()


@pytest.fixture
def api_context(
    session_factory: sessionmaker[Session],
) -> Iterator[tuple[TestClient, sessionmaker[Session]]]:
    def override_get_db() -> Iterator[Session]:
        with session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(app) as client:
            yield client, session_factory
    finally:
        app.dependency_overrides.pop(get_db, None)
