from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0001_baseline"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "trend",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("term", sa.String(), nullable=False),
        sa.Column("category", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_table(
        "trendsignal",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("source", sa.String(), nullable=False),
        sa.Column("keyword", sa.String(), nullable=False),
        sa.Column("timestamp", sa.DateTime(), nullable=False),
        sa.Column("engagement_score", sa.Integer(), nullable=False),
        sa.Column("category", sa.String(), nullable=False),
    )
    op.create_table(
        "idea",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("trend_id", sa.Integer(), nullable=False),
        sa.Column("description", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_table(
        "product",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("idea_id", sa.Integer(), nullable=False),
        sa.Column("image_url", sa.String(), nullable=False),
        sa.Column("sku", sa.String(), nullable=True),
        sa.Column("rating", sa.Integer(), nullable=True),
        sa.Column("tags", sa.JSON(), nullable=True),
        sa.Column("flagged", sa.Boolean(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_table(
        "listing",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("etsy_url", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_table(
        "listingdraft",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=False),
        sa.Column("tags", sa.JSON(), nullable=False),
        sa.Column("language", sa.String(), nullable=False),
        sa.Column("field_order", sa.JSON(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_table(
        "user",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("plan", sa.String(), nullable=False),
        sa.Column("quota_used", sa.Integer(), nullable=False),
        sa.Column("quota_limit", sa.Integer(), nullable=True),
        sa.Column("last_reset", sa.DateTime(), nullable=False),
        sa.Column("auto_social", sa.Boolean(), nullable=False),
        sa.Column("social_handles", sa.JSON(), nullable=False),
    )
    op.create_table(
        "notification",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("message", sa.String(), nullable=False),
        sa.Column("type", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("read_status", sa.Boolean(), nullable=False),
    )
    op.create_table(
        "abtest",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("experiment_type", sa.String(), nullable=False),
        sa.Column("start_time", sa.DateTime(), nullable=True),
        sa.Column("end_time", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_table(
        "abvariant",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("test_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("weight", sa.Float(), nullable=False),
        sa.Column("impressions", sa.Integer(), nullable=False),
        sa.Column("clicks", sa.Integer(), nullable=False),
    )
    op.create_table(
        "analyticsevent",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("event_type", sa.String(), nullable=False),
        sa.Column("path", sa.String(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_table(
        "oauthstate",
        sa.Column("state", sa.String(length=255), primary_key=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("provider", sa.String(), nullable=False),
        sa.Column("code_verifier", sa.String(), nullable=True),
        sa.Column("redirect_uri", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_table(
        "oauthcredential",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("provider", sa.String(), nullable=False),
        sa.Column("access_token", sa.String(), nullable=False),
        sa.Column("refresh_token", sa.String(), nullable=True),
        sa.Column("expires_at", sa.DateTime(), nullable=True),
        sa.Column("scope", sa.String(), nullable=True),
        sa.Column("account_id", sa.String(), nullable=True),
        sa.Column("account_name", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_table(
        "usersession",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("token_hash", sa.String(length=128), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_usersession_token_hash", "usersession", ["token_hash"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_usersession_token_hash", table_name="usersession")
    op.drop_table("usersession")
    op.drop_table("oauthcredential")
    op.drop_table("oauthstate")
    op.drop_table("analyticsevent")
    op.drop_table("abvariant")
    op.drop_table("abtest")
    op.drop_table("notification")
    op.drop_table("user")
    op.drop_table("listingdraft")
    op.drop_table("listing")
    op.drop_table("product")
    op.drop_table("idea")
    op.drop_table("trendsignal")
    op.drop_table("trend")
