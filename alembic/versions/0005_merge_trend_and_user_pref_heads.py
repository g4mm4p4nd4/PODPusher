"""Merge Alembic heads after origin reconciliation."""

from __future__ import annotations


revision = "0005_merge_trend_user"
down_revision = ("0003_add_trend_signal_indexes", "0004_user_pref_columns")
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
