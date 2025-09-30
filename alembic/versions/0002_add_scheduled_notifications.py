from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0002_add_scheduled_notifications"
down_revision = "0001_baseline"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "schedulednotification",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("message", sa.String(), nullable=False),
        sa.Column("type", sa.String(), nullable=False),
        sa.Column("scheduled_for", sa.DateTime(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("context", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("dispatched_at", sa.DateTime(), nullable=True),
    )
    op.create_index(
        "ix_schedulednotification_scheduled_for",
        "schedulednotification",
        ["scheduled_for"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_schedulednotification_scheduled_for",
        table_name="schedulednotification",
    )
    op.drop_table("schedulednotification")
