from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0004_add_user_preferences_columns"
down_revision = "0003_timescale_trend_aggregates"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("user") as batch_op:
        batch_op.add_column(
            sa.Column(
                "email_notifications",
                sa.Boolean(),
                nullable=False,
                server_default=sa.true(),
            )
        )
        batch_op.add_column(
            sa.Column(
                "push_notifications",
                sa.Boolean(),
                nullable=False,
                server_default=sa.false(),
            )
        )
        batch_op.add_column(
            sa.Column(
                "preferred_language",
                sa.String(),
                nullable=False,
                server_default="en",
            )
        )
        batch_op.add_column(
            sa.Column(
                "preferred_currency",
                sa.String(),
                nullable=False,
                server_default="USD",
            )
        )
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
        batch_op.drop_column("timezone")
        batch_op.drop_column("preferred_currency")
        batch_op.drop_column("preferred_language")
        batch_op.drop_column("push_notifications")
        batch_op.drop_column("email_notifications")
