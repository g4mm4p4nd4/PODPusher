from typing import Any, Dict, List, Optional
from enum import Enum
from datetime import datetime

from sqlalchemy import Column, JSON
from sqlmodel import Field, SQLModel


class Trend(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    term: str
    category: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Idea(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    trend_id: int
    description: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Product(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    idea_id: int
    image_url: str
    sku: Optional[str] = None
    rating: Optional[int] = None
    tags: Optional[List[str]] = Field(default=None, sa_column=Column(JSON))
    flagged: Optional[bool] = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Image(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    idea_id: int
    provider: str
    url: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Listing(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    product_id: int
    etsy_url: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ListingDraft(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    description: str
    tags: List[str] = Field(default_factory=list, sa_column=Column(JSON))
    language: str = "en"
    field_order: List[str] = Field(default_factory=list, sa_column=Column(JSON))
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    plan: str = "free"
    quota_used: int = 0
    last_reset: datetime = Field(default_factory=datetime.utcnow)
    auto_social: bool = True
    social_handles: Dict[str, str] = Field(default_factory=dict, sa_column=Column(JSON))


class Notification(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int
    message: str
    type: str = "info"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    read_status: bool = False


class ExperimentType(str, Enum):
    IMAGE = "image"
    DESCRIPTION = "description"
    PRICE = "price"


class ABTest(SQLModel, table=True):
    """Top level A/B test container."""

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    experiment_type: "ExperimentType"
    start_time: datetime | None = None
    end_time: datetime | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ABVariant(SQLModel, table=True):
    """Variant belonging to an A/B test."""

    id: Optional[int] = Field(default=None, primary_key=True)
    test_id: int
    name: str
    weight: float = 1.0
    impressions: int = 0
    clicks: int = 0


class EventType(str, Enum):
    page_view = "page_view"
    click = "click"
    conversion = "conversion"


class AnalyticsEvent(SQLModel, table=True):
    """Stored analytics event for dashboards."""

    id: Optional[int] = Field(default=None, primary_key=True)
    event_type: EventType
    path: str
    user_id: Optional[int] = None
    meta: Dict[str, Any] | None = Field(
        default=None, sa_column=Column("metadata", JSON)
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)
