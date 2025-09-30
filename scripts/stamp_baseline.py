"""Utility to stamp the database with the Alembic baseline revision."""
from __future__ import annotations

import os

from alembic import command
from alembic.config import Config


DEFAULT_URL = 'sqlite+aiosqlite:///./test.db'


def main() -> None:
    db_url = os.getenv('DATABASE_URL', DEFAULT_URL)
    config = Config('alembic.ini')
    config.set_main_option('sqlalchemy.url', db_url.replace('sqlite+aiosqlite://', 'sqlite:///'))
    command.stamp(config, '0001_baseline')


if __name__ == '__main__':
    main()
