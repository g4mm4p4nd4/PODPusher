from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0004_add_user_preferences_columns"
down_revision = "0003_timescale_trend_aggregates"
branch_labels = None
depends_on = None


def _has_table(name: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    return name in inspector.get_table_names()


def _existing_columns(table_name: str) -> set[str]:
    inspector = sa.inspect(op.get_bind())
    return {column["name"] for column in inspector.get_columns(table_name)}


def upgrade() -> None:
    if not _has_table("user"):
        return

    columns = _existing_columns("user")
    with op.batch_alter_table("user") as batch_op:
        if "email_notifications" not in columns:
            batch_op.add_column(sa.Column("email_notifications", sa.Boolean(), nullable=False, server_default=sa.true()))
        if "push_notifications" not in columns:
            batch_op.add_column(sa.Column("push_notifications", sa.Boolean(), nullable=False, server_default=sa.false()))
        if "preferred_language" not in columns:
            batch_op.add_column(sa.Column("preferred_language", sa.String(), nullable=False, server_default="en"))
        if "preferred_currency" not in columns:
            batch_op.add_column(sa.Column("preferred_currency", sa.String(), nullable=False, server_default="USD"))
        if "timezone" not in columns:
            batch_op.add_column(sa.Column("timezone", sa.String(), nullable=False, server_default="UTC"))


def downgrade() -> None:
    if not _has_table("user"):
        return

    columns = _existing_columns("user")
    with op.batch_alter_table("user") as batch_op:
        if "timezone" in columns:
            batch_op.drop_column("timezone")
        if "preferred_currency" in columns:
            batch_op.drop_column("preferred_currency")
        if "preferred_language" in columns:
            batch_op.drop_column("preferred_language")
        if "push_notifications" in columns:
            batch_op.drop_column("push_notifications")
        if "email_notifications" in columns:
            batch_op.drop_column("email_notifications")
