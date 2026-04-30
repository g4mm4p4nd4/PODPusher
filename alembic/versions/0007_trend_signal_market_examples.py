"""Add source-backed market examples to trend signals."""

from alembic import op
import sqlalchemy as sa


revision = "0007_trend_examples"
down_revision = "0006_wireframe_control_center"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("trendsignal") as batch_op:
        batch_op.add_column(sa.Column("metadata_json", sa.JSON(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("trendsignal") as batch_op:
        batch_op.drop_column("metadata_json")
