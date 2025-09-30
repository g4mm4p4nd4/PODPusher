import sqlite3
from pathlib import Path

import pytest

try:
    from alembic import command
    from alembic.config import Config
except ImportError:  # pragma: no cover - Alembic not installed
    pytest.skip('Alembic not available', allow_module_level=True)

MIGRATION_DB = Path('alembic_validation.db')


def _run_upgrade(db_url: str) -> None:
    config = Config('alembic.ini')
    config.set_main_option(
        'sqlalchemy.url', db_url.replace('sqlite+aiosqlite://', 'sqlite:///')
    )
    command.upgrade(config, 'head')


def _drop_db(path: Path) -> None:
    if path.exists():
        path.unlink()


async def test_alembic_upgrade_repeatability():
    db_url = 'sqlite+aiosqlite:///./alembic_validation.db'
    _drop_db(MIGRATION_DB)
    try:
        for _ in range(3):
            _run_upgrade(db_url)
        conn = sqlite3.connect(MIGRATION_DB)
        try:
            cur = conn.cursor()
            cur.execute(
                'SELECT name FROM sqlite_master WHERE type=\'table\' AND name=\'schedulednotification\''
            )
            row = cur.fetchone()
            assert row and row[0] == 'schedulednotification'
            cur.execute('PRAGMA index_list(\'schedulednotification\')')
            indexes = [name for _, name, *_ in cur.fetchall()]
            assert 'ix_schedulednotification_scheduled_for' in indexes
        finally:
            conn.close()
    finally:
        _drop_db(MIGRATION_DB)

