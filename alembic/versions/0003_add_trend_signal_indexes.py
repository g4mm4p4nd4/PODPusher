from __future__ import annotations

from alembic import op
from sqlalchemy import inspect


revision = "0003_add_trend_signal_indexes"
down_revision = "0002_add_scheduled_notifications"
branch_labels = None
depends_on = None


def _has_index(table_name: str, index_name: str) -> bool:
    bind = op.get_bind()
    inspector = inspect(bind)
    if not inspector.has_table(table_name):
        return False
    return any(index.get("name") == index_name for index in inspector.get_indexes(table_name))


def upgrade() -> None:
    if not _has_index("trendsignal", "ix_trendsignal_source"):
        op.create_index("ix_trendsignal_source", "trendsignal", ["source"])
    if not _has_index("trendsignal", "ix_trendsignal_keyword"):
        op.create_index("ix_trendsignal_keyword", "trendsignal", ["keyword"])


def downgrade() -> None:
    if _has_index("trendsignal", "ix_trendsignal_keyword"):
        op.drop_index("ix_trendsignal_keyword", table_name="trendsignal")
    if _has_index("trendsignal", "ix_trendsignal_source"):
        op.drop_index("ix_trendsignal_source", table_name="trendsignal")
