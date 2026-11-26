# Research Blog & Project Discussion Board (RBPDB)

RBPDB is a FastAPI backend for research, course, and project discussions. It
provides user and thread management, posts and nested comments, moderation
operations, and chronological timelines. PostgreSQL stores the data; SQLAlchemy
defines persistence mappings and Alembic manages schema migrations.

The current API accepts author `user_id` values in request bodies. Authentication
and authorization based on signed-in identities are not implemented.

## Architecture

The service lives in [`functional_codebase/`](functional_codebase):

- `app/api/` — FastAPI routers and OpenAPI documentation.
- `app/services/` — application operations and validation.
- `app/repositories/` — database access.
- `app/models/` — SQLAlchemy entities and relationships.
- `app/schemas/` — Pydantic request, response, query, and error schemas.
- `app/core/` — configuration and exception handling.
- `app/db/` — SQLAlchemy engine and session setup.
- `app/tests/` and `tests/` — database integration and API/service/repository tests.
- `alembic/` — schema migrations.
- `docker/` — Docker-related project assets.

## Prerequisites

- Docker Engine with Docker Compose.
- Python 3.12+ and pip for local test execution.
- Git.

## Environment configuration

Run commands below from `functional_codebase`. Copy the example environment
file, then adjust the credentials if needed:

```powershell
Copy-Item .env.example .env
```

`.env` configures the PostgreSQL user, password, database, host, port,
`DATABASE_URL`, and a separate `TEST_DATABASE_URL`. Do not commit `.env` or use
the test URL for application data. If a password contains URL-reserved
characters, URL-encode it in the connection URLs.

## Docker setup

```powershell
Set-Location functional_codebase
Copy-Item .env.example .env
docker compose up -d --build
docker compose exec app alembic upgrade head
```

The API listens on <http://localhost:8000>. To stop the services:

```powershell
docker compose down
```

To also delete the PostgreSQL data volume and all data in it, use
`docker compose down -v`. This is destructive.

## Database migrations

With the Compose services running, apply migrations inside the app container:

```powershell
docker compose exec app alembic upgrade head
```

For local development with Python installed and PostgreSQL reachable at the
host configured by `.env`, run from `functional_codebase`:

```powershell
python -m pip install -r requirements.txt
alembic upgrade head
```

## Seed data

After applying migrations, populate the small repeatable fixture set:

```powershell
docker compose exec app python -m app.seed
```

The seed data includes three roles and users, a Lab → Course → Project thread
hierarchy, three tags, two posts with tag associations, and four comments
including a two-level reply chain. Re-running the command is safe.

Reset and recreate only the seed fixtures:

```powershell
docker compose exec app python -m app.seed --reset
```

Remove only the seed fixtures:

```powershell
docker compose exec app python -m app.seed --clean
```

Cleanup retains shared role records. See
[`functional_codebase/SEEDING.md`](functional_codebase/SEEDING.md) for fixture
identifiers and cleanup behavior.

## Tests

The test suite includes unit-level service and repository tests, API tests, and
PostgreSQL integration checks for migrations, schema constraints, and seed
repeatability. The integration harness resets the schema in its configured
test database; ensure `TEST_DATABASE_URL` names a dedicated database containing
`_test` and is not the application database.

Install test dependencies and run the suite from `functional_codebase`:

```powershell
python -m pip install -r requirements-dev.txt
python -m pytest
```

The example `.env` uses `rbpdb_test` on the local PostgreSQL port. Create that
database once if it does not exist:

```powershell
docker compose up -d db
docker compose exec db sh -c 'createdb -U "$POSTGRES_USER" rbpdb_test'
```

For more on the database safety checks and test configuration, see
[`functional_codebase/TESTING.md`](functional_codebase/TESTING.md).

## API documentation

When the API is running:

- Swagger UI: <http://localhost:8000/docs>
- ReDoc: <http://localhost:8000/redoc>
- OpenAPI JSON: <http://localhost:8000/openapi.json>

The OpenAPI document includes operation descriptions, request and response
examples, and documented error responses.
