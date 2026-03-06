"""Alembic migration: Convert TrendSignal to TimescaleDB hypertable with continuous aggregates.

This migration requires PostgreSQL + TimescaleDB extension. It:
1. Converts the trendsignal table to a hypertable partitioned by timestamp
2. Creates continuous aggregates for hourly and daily trend rollups
3. Adds a refresh policy for automatic aggregate maintenance

When running on SQLite (development), only the index additions are applied.

Owner: Data-Seeder (per DEVELOPMENT_PLAN.md Technical Debt TD-01)
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0003_timescale_trend_aggregates"
down_revision = "0002_add_scheduled_notifications"
branch_labels = None
depends_on = None


def _is_postgresql() -> bool:
    """Check if we are running against PostgreSQL."""
    return op.get_bind().dialect.name == "postgresql"


def upgrade() -> None:
    # Add indexes that work on all backends
    with op.batch_alter_table("trendsignal") as batch_op:
        batch_op.create_index(
            "ix_trendsignal_source_keyword",
            ["source", "keyword"],
        )
        batch_op.create_index(
            "ix_trendsignal_category_timestamp",
            ["category", "timestamp"],
        )

    with op.batch_alter_table("trend") as batch_op:
        batch_op.create_index(
            "ix_trend_category_created",
            ["category", "created_at"],
        )

    # TimescaleDB-specific operations (PostgreSQL only)
    if not _is_postgresql():
        return

    # Enable TimescaleDB extension
    op.execute("CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE")

    # Convert trendsignal to a hypertable partitioned by timestamp.
    # The migrate_data option preserves existing rows.
    op.execute(
        "SELECT create_hypertable('trendsignal', 'timestamp', "
        "migrate_data => true, if_not_exists => true)"
    )

    # Hourly trend aggregates: count signals, avg engagement, top keywords per source
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

    # Daily trend aggregates: rolled up from the hourly view
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

    # Automatic refresh policies: refresh hourly view every 30 minutes,
    # daily view every 6 hours.  start_offset / end_offset define the
    # time window to recompute.
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

    # Retention policy: drop raw data older than 90 days (aggregates kept)
    op.execute("""
        SELECT add_retention_policy('trendsignal',
            INTERVAL '90 days',
            if_not_exists => true
        )
    """)


def downgrade() -> None:
    if _is_postgresql():
        op.execute("SELECT remove_retention_policy('trendsignal', if_exists => true)")
        op.execute("SELECT remove_continuous_aggregate_policy('trend_daily', if_not_exists => true)")
        op.execute("SELECT remove_continuous_aggregate_policy('trend_hourly', if_not_exists => true)")
        op.execute("DROP MATERIALIZED VIEW IF EXISTS trend_daily CASCADE")
        op.execute("DROP MATERIALIZED VIEW IF EXISTS trend_hourly CASCADE")

    with op.batch_alter_table("trend") as batch_op:
        batch_op.drop_index("ix_trend_category_created")

    with op.batch_alter_table("trendsignal") as batch_op:
        batch_op.drop_index("ix_trendsignal_category_timestamp")
        batch_op.drop_index("ix_trendsignal_source_keyword")
