# Seed data

The seed command creates a small, repeatable fixture set for API testing:

- The `student`, `faculty`, and `admin` roles.
- One user per role.
- One lab, two courses, and two projects, arranged Lab → Course → Project.
- Three tags associated with the lab, one course, and one project.
- Two posts (one discussion and one announcement) with three comments, including a reply.

Run from `functional_codebase` after configuring `.env`, starting PostgreSQL, and applying migrations:

```powershell
docker compose up -d db
alembic upgrade head
python -m app.seed
```

The command is idempotent. To remove and recreate only its fixtures:

```powershell
python -m app.seed --reset
```

To remove the fixtures without recreating them:

```powershell
python -m app.seed --clean
```

Roles are shared lookup data and are retained by cleanup. Cleanup deletes the seed thread hierarchy, its posts and comments, seed tags, and seed users by their reserved fixture names and emails. Any test-created records that reference a seed user outside the seed hierarchy can prevent that user's deletion; those records must be removed first. Do not use the reserved `rbpdb_seed_*` usernames, `rbpdb.seed.*@example.test` emails, `RBPDB Seed ...` thread and post titles, or `rbpdb-seed-*` tags for non-seed data.
