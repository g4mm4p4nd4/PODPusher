from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0003_add_trend_signal_indexes"
down_revision = "0002_add_scheduled_notifications"
branch_labels = None
depends_on = None


def _has_table(name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return name in inspector.get_table_names()


def upgrade() -> None:
    if not _has_table("trendsignal"):
        return
    op.create_index("ix_trendsignal_source", "trendsignal", ["source"])
    op.create_index("ix_trendsignal_keyword", "trendsignal", ["keyword"])


def downgrade() -> None:
    if not _has_table("trendsignal"):
        return
    op.drop_index("ix_trendsignal_keyword", table_name="trendsignal")
    op.drop_index("ix_trendsignal_source", table_name="trendsignal")
