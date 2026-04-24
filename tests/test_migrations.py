import os
import sqlite3
from pathlib import Path

import pytest

try:
    from alembic import command
    from alembic.config import Config
except ImportError:  # pragma: no cover - Alembic not installed
    pytest.skip('Alembic not available', allow_module_level=True)

ROOT = Path(__file__).resolve().parents[1]
MIGRATION_DB = ROOT / 'alembic_validation.db'
EXPECTED_HEAD = "0006_wireframe_control_center"
EXPECTED_TABLES = {
    "abtest",
    "abvariant",
    "analyticsevent",
    "idea",
    "listing",
    "listingdraft",
    "notification",
    "oauthcredential",
    "oauthstate",
    "product",
    "schedulednotification",
    "trend",
    "trendsignal",
    "user",
    "usersession",
    "abexperimentevent",
    "automationjob",
    "brandprofile",
    "listingdraftrevision",
    "listingoptimization",
    "notificationrule",
    "savedniche",
    "savedsearch",
    "seasonalevent",
    "store",
    "teammember",
    "usageledger",
    "watchlistitem",
}
EXPECTED_INDEXES = {
    "analyticsevent": {
        "ix_analyticsevent_created_at",
        "ix_analyticsevent_event_type",
        "ix_analyticsevent_user_id",
    },
    "notification": {
        "ix_notification_created_at",
        "ix_notification_user_id",
    },
    "product": {
        "ix_product_created_at",
        "ix_product_idea_id",
        "ix_product_sku",
    },
    "schedulednotification": {"ix_schedulednotification_scheduled_for"},
    "trend": {
        "ix_trend_category",
        "ix_trend_created_at",
        "ix_trend_term",
    },
    "trendsignal": {
        "ix_trendsignal_category",
        "ix_trendsignal_keyword",
        "ix_trendsignal_source",
        "ix_trendsignal_timestamp",
    },
    "usersession": {"ix_usersession_token_hash"},
    "brandprofile": {"ix_brandprofile_user_id", "ix_brandprofile_updated_at"},
    "seasonalevent": {
        "ix_seasonalevent_event_date",
        "ix_seasonalevent_name",
        "ix_seasonalevent_priority",
        "ix_seasonalevent_region",
        "ix_seasonalevent_user_id",
    },
    "notificationrule": {
        "ix_notificationrule_user_id",
        "ix_notificationrule_created_at",
    },
    "automationjob": {
        "ix_automationjob_next_run",
        "ix_automationjob_status",
        "ix_automationjob_user_id",
    },
}


def _run_upgrade(db_url: str) -> None:
    config = Config(str(ROOT / 'alembic.ini'))
    previous = os.environ.get('DATABASE_URL')
    os.environ['DATABASE_URL'] = db_url
    try:
        command.upgrade(config, 'head')
    finally:
        if previous is None:
            os.environ.pop('DATABASE_URL', None)
        else:
            os.environ['DATABASE_URL'] = previous


def _drop_db(path: Path) -> None:
    if path.exists():
        path.unlink()


def test_alembic_upgrade_repeatability():
    db_url = f"sqlite:///{MIGRATION_DB.as_posix()}"
    _drop_db(MIGRATION_DB)
    try:
        for _ in range(3):
            _run_upgrade(db_url)
        conn = sqlite3.connect(MIGRATION_DB)
        try:
            cur = conn.cursor()
            cur.execute("SELECT version_num FROM alembic_version")
            versions = {row[0] for row in cur.fetchall()}
            assert versions == {EXPECTED_HEAD}

            cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = {row[0] for row in cur.fetchall()}
            assert EXPECTED_TABLES.issubset(tables)

            for table_name, expected_indexes in EXPECTED_INDEXES.items():
                cur.execute(f"PRAGMA index_list('{table_name}')")
                indexes = {row[1] for row in cur.fetchall()}
                assert expected_indexes.issubset(indexes), (
                    f"Missing indexes for {table_name}: "
                    f"{sorted(expected_indexes - indexes)}"
                )
        finally:
            conn.close()
    finally:
        _drop_db(MIGRATION_DB)
