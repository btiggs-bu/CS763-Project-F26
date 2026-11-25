# Integration tests

The integration suite validates SQLAlchemy mappings, the PostgreSQL schema,
Alembic migrations and autogenerate, ERD constraints, and seed fixtures. It
requires PostgreSQL and a dedicated test database.

From `functional_codebase`, start PostgreSQL and install the development
requirements:

```powershell
docker compose up -d db
python -m pip install -r requirements-dev.txt
```

Create a dedicated database once. Replace `rbpdb` if `POSTGRES_USER` differs
from the project defaults:

```powershell
docker compose exec db sh -c 'createdb -U "$POSTGRES_USER" rbpdb_test'
```

Set `TEST_DATABASE_URL` to that database, using the PostgreSQL credentials and
host port from `.env` (URL-encode special characters in the password), then
run the suite:

```powershell
$env:TEST_DATABASE_URL = "postgresql+psycopg://rbpdb:rbpdb@localhost:5432/rbpdb_test"
python -m pytest
```

The test harness requires `_test` in the database name and rejects the
application database configured in `.env`. On each run it downgrades the
dedicated test database to Alembic `base` when necessary, then reapplies all
migrations. **This resets the schema and data in that test database.** Never
point `TEST_DATABASE_URL` at a development or production database.
