from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0003_add_trend_signal_indexes"
down_revision = "0002_add_scheduled_notifications"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index("ix_trendsignal_source", "trendsignal", ["source"])
    op.create_index("ix_trendsignal_keyword", "trendsignal", ["keyword"])


def downgrade() -> None:
    op.drop_index("ix_trendsignal_keyword", table_name="trendsignal")
    op.drop_index("ix_trendsignal_source", table_name="trendsignal")
