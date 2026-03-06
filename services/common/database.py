"""Database engine, session helper, and slow-query profiling.

Owner: Backend-Coder (per DEVELOPMENT_PLAN.md Task 2.3.2)
"""

import logging
import os
import tempfile
import time
import uuid
from contextlib import asynccontextmanager

from sqlalchemy import event
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

# Ensure SQLModel metadata includes all tables before init_db/create_all.
from .. import models  # noqa: F401

logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./test.db")

# Connection pool configuration (tuned for PostgreSQL; SQLite ignores pool_size)
_pool_kwargs = {}
if not DATABASE_URL.startswith("sqlite"):
    _pool_kwargs = {
        "pool_size": int(os.getenv("DB_POOL_SIZE", "10")),
        "max_overflow": int(os.getenv("DB_MAX_OVERFLOW", "20")),
        "pool_timeout": int(os.getenv("DB_POOL_TIMEOUT", "30")),
        "pool_recycle": int(os.getenv("DB_POOL_RECYCLE", "1800")),
        "pool_pre_ping": True,
    }

engine = create_async_engine(DATABASE_URL, echo=False, future=True, **_pool_kwargs)

# ---------------------------------------------------------------------------
# Slow-query profiling
# ---------------------------------------------------------------------------

SLOW_QUERY_THRESHOLD_MS = float(os.getenv("SLOW_QUERY_THRESHOLD_MS", "200"))


def _register_query_profiling(sync_engine) -> None:
    """Attach before/after cursor-execute listeners to log slow queries."""

    @event.listens_for(sync_engine, "before_cursor_execute")
    def _before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        conn.info.setdefault("query_start_time", []).append(time.perf_counter())

    @event.listens_for(sync_engine, "after_cursor_execute")
    def _after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        total_ms = (time.perf_counter() - conn.info["query_start_time"].pop()) * 1000
        if total_ms >= SLOW_QUERY_THRESHOLD_MS:
            logger.warning(
                "Slow query (%.1fms): %s | params=%s",
                total_ms,
                statement[:500],
                str(parameters)[:200] if parameters else "None",
            )


# Register profiling on the synchronous engine underlying the async engine
try:
    _register_query_profiling(engine.sync_engine)
except Exception:
    pass  # Silently skip if engine doesn't expose sync_engine yet


def _sqlite_file_path(url: str) -> str:
    return url.split("///", maxsplit=1)[-1]


def _sqlite_url(path: str) -> str:
    return f"sqlite+aiosqlite:///{path}"


async def init_db() -> None:
    global engine, DATABASE_URL
    if DATABASE_URL.startswith("sqlite"):
        db_path = _sqlite_file_path(DATABASE_URL)
        try:
            await engine.dispose()  # ensure no open connections block removal
        except Exception:
            pass

        if os.path.exists(db_path):
            try:
                os.remove(db_path)
            except PermissionError:
                # On Windows, a locked SQLite file can leave partial schema state behind.
                # Switch to a fresh temp file instead of reusing the stale database.
                temp_path = os.path.join(
                    tempfile.gettempdir(),
                    f"podpusher-{uuid.uuid4().hex}.db",
                )
                DATABASE_URL = _sqlite_url(temp_path)

        engine = create_async_engine(DATABASE_URL, echo=False, future=True)
        try:
            _register_query_profiling(engine.sync_engine)
        except Exception:
            pass

    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)
        await conn.run_sync(SQLModel.metadata.create_all)


@asynccontextmanager
async def get_session() -> AsyncSession:
    async with AsyncSession(engine, expire_on_commit=False) as session:
        yield session
