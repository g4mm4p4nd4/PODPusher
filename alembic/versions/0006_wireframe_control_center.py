from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision = "0006_wireframe_control_center"
down_revision = "0005_merge_trend_and_user_pref_heads"
branch_labels = None
depends_on = None


def _has_table(table_name: str) -> bool:
    return inspect(op.get_bind()).has_table(table_name)


def _has_column(table_name: str, column_name: str) -> bool:
    inspector = inspect(op.get_bind())
    if not inspector.has_table(table_name):
        return False
    return any(
        column.get("name") == column_name
        for column in inspector.get_columns(table_name)
    )


def _has_index(table_name: str, index_name: str) -> bool:
    inspector = inspect(op.get_bind())
    if not inspector.has_table(table_name):
        return False
    return any(
        index.get("name") == index_name for index in inspector.get_indexes(table_name)
    )


def _create_index(
    table_name: str, index_name: str, columns: list[str], unique: bool = False
) -> None:
    if _has_table(table_name) and not _has_index(table_name, index_name):
        op.create_index(index_name, table_name, columns, unique=unique)


def _create_table_if_missing(table_name: str, *columns: sa.Column) -> None:
    if not _has_table(table_name):
        op.create_table(table_name, *columns)


def upgrade() -> None:
    with op.batch_alter_table("abtest") as batch_op:
        if not _has_column("abtest", "product_id"):
            batch_op.add_column(sa.Column("product_id", sa.Integer(), nullable=True))
        if not _has_column("abtest", "status"):
            batch_op.add_column(
                sa.Column(
                    "status", sa.String(), nullable=False, server_default="running"
                )
            )
        if not _has_column("abtest", "winner_variant_id"):
            batch_op.add_column(
                sa.Column("winner_variant_id", sa.Integer(), nullable=True)
            )

    _create_index("abtest", "ix_abtest_product_id", ["product_id"])
    _create_index("abtest", "ix_abtest_status", ["status"])

    _create_table_if_missing(
        "store",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("marketplace", sa.String(), nullable=False),
        sa.Column("region", sa.String(), nullable=False),
        sa.Column("currency", sa.String(), nullable=False),
        sa.Column("is_default", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    _create_index("store", "ix_store_user_id", ["user_id"])
    _create_index("store", "ix_store_marketplace", ["marketplace"])

    _create_table_if_missing(
        "brandprofile",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("tone", sa.String(), nullable=False),
        sa.Column("audience", sa.String(), nullable=False),
        sa.Column("interests", sa.JSON(), nullable=False),
        sa.Column("banned_topics", sa.JSON(), nullable=False),
        sa.Column("preferred_products", sa.JSON(), nullable=False),
        sa.Column("region", sa.String(), nullable=False),
        sa.Column("language", sa.String(), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    _create_index("brandprofile", "ix_brandprofile_user_id", ["user_id"])
    _create_index("brandprofile", "ix_brandprofile_updated_at", ["updated_at"])

    _create_table_if_missing(
        "savedniche",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("niche", sa.String(), nullable=False),
        sa.Column("score", sa.Integer(), nullable=False),
        sa.Column("context", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    _create_index("savedniche", "ix_savedniche_user_id", ["user_id"])
    _create_index("savedniche", "ix_savedniche_niche", ["niche"])
    _create_index("savedniche", "ix_savedniche_created_at", ["created_at"])

    _create_table_if_missing(
        "savedsearch",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("query", sa.String(), nullable=False),
        sa.Column("filters", sa.JSON(), nullable=True),
        sa.Column("result_count", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    _create_index("savedsearch", "ix_savedsearch_user_id", ["user_id"])
    _create_index("savedsearch", "ix_savedsearch_created_at", ["created_at"])

    _create_table_if_missing(
        "watchlistitem",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("item_type", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("context", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    _create_index("watchlistitem", "ix_watchlistitem_user_id", ["user_id"])
    _create_index("watchlistitem", "ix_watchlistitem_item_type", ["item_type"])
    _create_index("watchlistitem", "ix_watchlistitem_name", ["name"])
    _create_index("watchlistitem", "ix_watchlistitem_created_at", ["created_at"])

    _create_table_if_missing(
        "seasonalevent",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("event_date", sa.DateTime(), nullable=False),
        sa.Column("region", sa.String(), nullable=False),
        sa.Column("language", sa.String(), nullable=False),
        sa.Column("marketplace", sa.String(), nullable=False),
        sa.Column("category", sa.String(), nullable=False),
        sa.Column("priority", sa.String(), nullable=False),
        sa.Column("opportunity_score", sa.Integer(), nullable=False),
        sa.Column("keywords", sa.JSON(), nullable=False),
        sa.Column("product_categories", sa.JSON(), nullable=False),
        sa.Column("saved", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    _create_index("seasonalevent", "ix_seasonalevent_user_id", ["user_id"])
    _create_index("seasonalevent", "ix_seasonalevent_name", ["name"])
    _create_index("seasonalevent", "ix_seasonalevent_event_date", ["event_date"])
    _create_index("seasonalevent", "ix_seasonalevent_region", ["region"])
    _create_index("seasonalevent", "ix_seasonalevent_priority", ["priority"])

    _create_table_if_missing(
        "listingdraftrevision",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("draft_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=False),
        sa.Column("tags", sa.JSON(), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    _create_index(
        "listingdraftrevision", "ix_listingdraftrevision_draft_id", ["draft_id"]
    )
    _create_index(
        "listingdraftrevision", "ix_listingdraftrevision_created_at", ["created_at"]
    )

    _create_table_if_missing(
        "listingoptimization",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("draft_id", sa.Integer(), nullable=False),
        sa.Column("score", sa.Integer(), nullable=False),
        sa.Column("seo_score", sa.Integer(), nullable=False),
        sa.Column("compliance_status", sa.String(), nullable=False),
        sa.Column("checks", sa.JSON(), nullable=False),
        sa.Column("source", sa.String(), nullable=False),
        sa.Column("is_estimated", sa.Boolean(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    _create_index(
        "listingoptimization", "ix_listingoptimization_draft_id", ["draft_id"]
    )
    _create_index(
        "listingoptimization", "ix_listingoptimization_updated_at", ["updated_at"]
    )

    _create_table_if_missing(
        "abexperimentevent",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("test_id", sa.Integer(), nullable=False),
        sa.Column("variant_id", sa.Integer(), nullable=True),
        sa.Column("event_type", sa.String(), nullable=False),
        sa.Column("value", sa.Integer(), nullable=False),
        sa.Column("context", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    _create_index("abexperimentevent", "ix_abexperimentevent_test_id", ["test_id"])
    _create_index(
        "abexperimentevent", "ix_abexperimentevent_variant_id", ["variant_id"]
    )
    _create_index(
        "abexperimentevent", "ix_abexperimentevent_event_type", ["event_type"]
    )
    _create_index(
        "abexperimentevent", "ix_abexperimentevent_created_at", ["created_at"]
    )

    _create_table_if_missing(
        "notificationrule",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("metric", sa.String(), nullable=False),
        sa.Column("operator", sa.String(), nullable=False),
        sa.Column("threshold", sa.Float(), nullable=False),
        sa.Column("window", sa.String(), nullable=False),
        sa.Column("channels", sa.JSON(), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    _create_index("notificationrule", "ix_notificationrule_user_id", ["user_id"])
    _create_index("notificationrule", "ix_notificationrule_created_at", ["created_at"])

    _create_table_if_missing(
        "automationjob",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("frequency", sa.String(), nullable=False),
        sa.Column("next_run", sa.DateTime(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("category", sa.String(), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    _create_index("automationjob", "ix_automationjob_user_id", ["user_id"])
    _create_index("automationjob", "ix_automationjob_next_run", ["next_run"])
    _create_index("automationjob", "ix_automationjob_status", ["status"])

    _create_table_if_missing(
        "usageledger",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("resource_type", sa.String(), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("source", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    _create_index("usageledger", "ix_usageledger_user_id", ["user_id"])
    _create_index("usageledger", "ix_usageledger_resource_type", ["resource_type"])
    _create_index("usageledger", "ix_usageledger_created_at", ["created_at"])

    _create_table_if_missing(
        "teammember",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("role", sa.String(), nullable=False),
        sa.Column("permissions", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("last_active_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    _create_index("teammember", "ix_teammember_user_id", ["user_id"])
    _create_index("teammember", "ix_teammember_email", ["email"])
    _create_index("teammember", "ix_teammember_last_active_at", ["last_active_at"])


def downgrade() -> None:
    for table_name in [
        "teammember",
        "usageledger",
        "automationjob",
        "notificationrule",
        "abexperimentevent",
        "listingoptimization",
        "listingdraftrevision",
        "seasonalevent",
        "watchlistitem",
        "savedsearch",
        "savedniche",
        "brandprofile",
        "store",
    ]:
        if _has_table(table_name):
            op.drop_table(table_name)

    with op.batch_alter_table("abtest") as batch_op:
        if _has_column("abtest", "winner_variant_id"):
            batch_op.drop_column("winner_variant_id")
        if _has_column("abtest", "status"):
            batch_op.drop_column("status")
        if _has_column("abtest", "product_id"):
            batch_op.drop_column("product_id")
