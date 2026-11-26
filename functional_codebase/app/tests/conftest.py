import os
import sys
from pathlib import Path

import pytest
from dotenv import dotenv_values
from sqlalchemy import inspect
from sqlalchemy.engine import URL, make_url

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))
environment = dotenv_values(PROJECT_ROOT / ".env")


def _configured_database_url():
    raw_url = os.environ.get("DATABASE_URL") or environment.get("DATABASE_URL")
    if raw_url:
        return make_url(raw_url)

    return URL.create(
        drivername="postgresql+psycopg",
        username=os.environ.get(
            "POSTGRES_USER",
            environment.get("POSTGRES_USER", "rbpdb"),
        ),
        password=os.environ.get(
            "POSTGRES_PASSWORD",
            environment.get("POSTGRES_PASSWORD", "rbpdb"),
        ),
        host=os.environ.get("DB_HOST", environment.get("DB_HOST", "localhost")),
        port=int(os.environ.get("DB_PORT", environment.get("DB_PORT", "5432"))),
        database=os.environ.get(
            "POSTGRES_DB",
            environment.get("POSTGRES_DB", "rbpdb"),
        ),
    )


def _same_database(first, second):
    return first.database == second.database


raw_test_url = os.environ.get("TEST_DATABASE_URL") or environment.get(
    "TEST_DATABASE_URL"
)
if not raw_test_url:
    raise pytest.UsageError(
        "Set TEST_DATABASE_URL to a dedicated PostgreSQL database whose name "
        "contains '_test'. See TESTING.md."
    )

test_url = make_url(raw_test_url)
if test_url.drivername == "postgresql":
    test_url = test_url.set(drivername="postgresql+psycopg")
if test_url.drivername != "postgresql+psycopg":
    raise pytest.UsageError("TEST_DATABASE_URL must use PostgreSQL with psycopg.")
if not test_url.database or "_test" not in test_url.database.lower():
    raise pytest.UsageError(
        "TEST_DATABASE_URL must point to a dedicated database with '_test' in its name."
    )
if _same_database(test_url, _configured_database_url()):
    raise pytest.UsageError(
        "TEST_DATABASE_URL must not point to the application's configured database."
    )

os.environ["DATABASE_URL"] = test_url.render_as_string(hide_password=False)


@pytest.fixture(scope="session", autouse=True)
def database_engine():
    from alembic import command
    from alembic.config import Config
    from app.db.database import Base, engine

    config = Config(str(PROJECT_ROOT / "alembic.ini"))
    if "alembic_version" in inspect(engine).get_table_names():
        command.downgrade(config, "base")
    command.upgrade(config, "head")
    Base.registry.configure()

    yield engine
    engine.dispose()


@pytest.fixture(autouse=True)
def clean_seed_fixtures():
    from app.seed import populate_seed_data

    populate_seed_data(clean=True)
    try:
        yield
    finally:
        populate_seed_data(clean=True)
