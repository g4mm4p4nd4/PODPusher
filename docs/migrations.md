# Database Migrations

PODPusher now uses Alembic to manage schema changes. The configuration files live
at the repository root (`alembic.ini`) and the `alembic/` directory.

## Setup

1. Install dependencies: `pip install -r requirements.txt` (includes Alembic).
2. Set `DATABASE_URL` to the target database. For local development SQLite is
   used by default (`sqlite+aiosqlite:///./test.db`).

## Commands

- `alembic upgrade head` ? apply all pending migrations.
- `alembic downgrade -1` ? roll back the last migration.
- `alembic revision --autogenerate -m "message"` ? create a new migration file.

When developing against the async SQLite or Postgres drivers, the Alembic env
converts URLs to their synchronous equivalents automatically, so no extra setup
is required.

## Baseline

Existing environments should be stamped to the baseline revision once to align
state without rewriting tables:

```bash
alembic stamp 0001_baseline
alembic upgrade head
```

After stamping, new deployments can continue using `alembic upgrade head` to
pick up the scheduled notifications schema (`0002_add_scheduled_notifications`).

## CI / Automation

The FastAPI services still support the existing `init_db()` helper for tests,
which recreates tables from SQLModel metadata. Production deployments should
run `alembic upgrade head` during release pipelines to ensure schema
consistency before workers start.
