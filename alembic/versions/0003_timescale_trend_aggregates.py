"""Alembic migration: Convert TrendSignal to TimescaleDB hypertable with continuous aggregates.

This migration requires PostgreSQL + TimescaleDB extension. It:
1. Converts the trendsignal table to a hypertable partitioned by timestamp
2. Creates continuous aggregates for hourly and daily trend rollups
3. Adds a refresh policy for automatic aggregate maintenance

When running on SQLite (development), only index additions are attempted.
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0003_timescale_trend_aggregates"
down_revision = "0002_add_scheduled_notifications"
branch_labels = None
depends_on = None


def _is_postgresql() -> bool:
    return op.get_bind().dialect.name == "postgresql"


def _has_table(name: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    return name in inspector.get_table_names()


def _has_index(table_name: str, index_name: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    try:
        indexes = inspector.get_indexes(table_name)
    except Exception:
        return False
    return any(idx.get("name") == index_name for idx in indexes)


def upgrade() -> None:
    if _has_table("trendsignal"):
        with op.batch_alter_table("trendsignal") as batch_op:
            if not _has_index("trendsignal", "ix_trendsignal_source_keyword"):
                batch_op.create_index("ix_trendsignal_source_keyword", ["source", "keyword"])
            if not _has_index("trendsignal", "ix_trendsignal_category_timestamp"):
                batch_op.create_index("ix_trendsignal_category_timestamp", ["category", "timestamp"])

    if _has_table("trend"):
        with op.batch_alter_table("trend") as batch_op:
            if not _has_index("trend", "ix_trend_category_created"):
                batch_op.create_index("ix_trend_category_created", ["category", "created_at"])

    if not _is_postgresql() or not _has_table("trendsignal"):
        return

    op.execute("CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE")
    op.execute(
        "SELECT create_hypertable('trendsignal', 'timestamp', "
        "migrate_data => true, if_not_exists => true)"
    )

    op.execute("""
        CREATE MATERIALIZED VIEW IF NOT EXISTS trend_hourly
        WITH (timescaledb.continuous) AS
        SELECT
            time_bucket('1 hour', timestamp) AS bucket,
            source,
            category,
            keyword,
            COUNT(*)                         AS signal_count,
            AVG(engagement_score)            AS avg_engagement,
            MAX(engagement_score)            AS max_engagement
        FROM trendsignal
        GROUP BY bucket, source, category, keyword
        WITH NO DATA
    """)

    op.execute("""
        CREATE MATERIALIZED VIEW IF NOT EXISTS trend_daily
        WITH (timescaledb.continuous) AS
        SELECT
            time_bucket('1 day', timestamp) AS bucket,
            source,
            category,
            keyword,
            COUNT(*)                         AS signal_count,
            AVG(engagement_score)            AS avg_engagement,
            MAX(engagement_score)            AS max_engagement
        FROM trendsignal
        GROUP BY bucket, source, category, keyword
        WITH NO DATA
    """)

    op.execute("""
        SELECT add_continuous_aggregate_policy('trend_hourly',
            start_offset  => INTERVAL '3 hours',
            end_offset    => INTERVAL '1 hour',
            schedule_interval => INTERVAL '30 minutes',
            if_not_exists => true
        )
    """)

    op.execute("""
        SELECT add_continuous_aggregate_policy('trend_daily',
            start_offset  => INTERVAL '3 days',
            end_offset    => INTERVAL '1 day',
            schedule_interval => INTERVAL '6 hours',
            if_not_exists => true
        )
    """)

    op.execute("""
        SELECT add_retention_policy('trendsignal',
            INTERVAL '90 days',
            if_not_exists => true
        )
    """)


def downgrade() -> None:
    if _is_postgresql() and _has_table("trendsignal"):
        op.execute("SELECT remove_retention_policy('trendsignal', if_exists => true)")
        op.execute("SELECT remove_continuous_aggregate_policy('trend_daily', if_not_exists => true)")
        op.execute("SELECT remove_continuous_aggregate_policy('trend_hourly', if_not_exists => true)")
        op.execute("DROP MATERIALIZED VIEW IF EXISTS trend_daily CASCADE")
        op.execute("DROP MATERIALIZED VIEW IF EXISTS trend_hourly CASCADE")

    if _has_table("trend") and _has_index("trend", "ix_trend_category_created"):
        with op.batch_alter_table("trend") as batch_op:
            batch_op.drop_index("ix_trend_category_created")

    if _has_table("trendsignal"):
        with op.batch_alter_table("trendsignal") as batch_op:
            if _has_index("trendsignal", "ix_trendsignal_category_timestamp"):
                batch_op.drop_index("ix_trendsignal_category_timestamp")
            if _has_index("trendsignal", "ix_trendsignal_source_keyword"):
                batch_op.drop_index("ix_trendsignal_source_keyword")
