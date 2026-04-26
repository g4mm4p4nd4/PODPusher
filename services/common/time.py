from datetime import UTC, datetime


def utcnow() -> datetime:
    """Return a naive UTC datetime for existing database columns."""
    return datetime.now(UTC).replace(tzinfo=None)
