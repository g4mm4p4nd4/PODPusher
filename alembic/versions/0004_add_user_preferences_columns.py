from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision = "0004_user_pref_columns"
down_revision = "0003_timescale_trend_aggregates"
branch_labels = None
depends_on = None


def _has_column(table_name: str, column_name: str) -> bool:
    bind = op.get_bind()
    inspector = inspect(bind)
    if not inspector.has_table(table_name):
        return False
    return any(column.get("name") == column_name for column in inspector.get_columns(table_name))


def upgrade() -> None:
    with op.batch_alter_table("user") as batch_op:
        if not _has_column("user", "email_notifications"):
            batch_op.add_column(
                sa.Column(
                    "email_notifications",
                    sa.Boolean(),
                    nullable=False,
                    server_default=sa.true(),
                )
            )
        if not _has_column("user", "push_notifications"):
            batch_op.add_column(
                sa.Column(
                    "push_notifications",
                    sa.Boolean(),
                    nullable=False,
                    server_default=sa.false(),
                )
            )
        if not _has_column("user", "preferred_language"):
            batch_op.add_column(
                sa.Column(
                    "preferred_language",
                    sa.String(),
                    nullable=False,
                    server_default="en",
                )
            )
        if not _has_column("user", "preferred_currency"):
            batch_op.add_column(
                sa.Column(
                    "preferred_currency",
                    sa.String(),
                    nullable=False,
                    server_default="USD",
                )
            )
        if not _has_column("user", "timezone"):
            batch_op.add_column(
                sa.Column(
                    "timezone",
                    sa.String(),
                    nullable=False,
                    server_default="UTC",
                )
            )


def downgrade() -> None:
    with op.batch_alter_table("user") as batch_op:
        if _has_column("user", "timezone"):
            batch_op.drop_column("timezone")
        if _has_column("user", "preferred_currency"):
            batch_op.drop_column("preferred_currency")
        if _has_column("user", "preferred_language"):
            batch_op.drop_column("preferred_language")
        if _has_column("user", "push_notifications"):
            batch_op.drop_column("push_notifications")
        if _has_column("user", "email_notifications"):
            batch_op.drop_column("email_notifications")
