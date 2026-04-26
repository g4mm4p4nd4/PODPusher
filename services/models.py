from typing import Any, Dict, List, Optional
from enum import Enum
from datetime import datetime

from .common.time import utcnow

from sqlalchemy import Column, JSON
from sqlmodel import Field, SQLModel


class Trend(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    term: str = Field(index=True)
    category: str = Field(index=True)
    created_at: datetime = Field(default_factory=utcnow, index=True)


class TrendSignal(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    source: str = Field(index=True)
    keyword: str = Field(index=True)
    timestamp: datetime = Field(default_factory=utcnow, index=True)
    engagement_score: int = 0
    category: str = Field(default="other", index=True)


class Idea(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    trend_id: int
    description: str
    created_at: datetime = Field(default_factory=utcnow)


class Product(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    idea_id: int = Field(index=True)
    image_url: str
    sku: Optional[str] = Field(default=None, index=True)
    rating: Optional[int] = None
    tags: Optional[List[str]] = Field(default=None, sa_column=Column(JSON))
    flagged: Optional[bool] = Field(default=False)
    created_at: datetime = Field(default_factory=utcnow, index=True)


class Listing(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    product_id: int
    etsy_url: Optional[str] = None
    created_at: datetime = Field(default_factory=utcnow)


class ListingDraft(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    description: str
    tags: List[str] = Field(default_factory=list, sa_column=Column(JSON))
    language: str = "en"
    field_order: List[str] = Field(default_factory=list, sa_column=Column(JSON))
    updated_at: datetime = Field(default_factory=utcnow)


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    plan: str = "free"
    quota_used: int = 0
    quota_limit: Optional[int] = Field(default=None, nullable=True)
    last_reset: datetime = Field(default_factory=utcnow)
    auto_social: bool = True
    social_handles: Dict[str, str] = Field(default_factory=dict, sa_column=Column(JSON))
    email_notifications: bool = True
    push_notifications: bool = False
    preferred_language: str = "en"
    preferred_currency: str = "USD"
    timezone: str = "UTC"


class Notification(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(index=True)
    message: str
    type: str = "info"
    created_at: datetime = Field(default_factory=utcnow, index=True)
    read_status: bool = False


class ScheduledNotification(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int
    message: str
    type: str = "info"
    scheduled_for: datetime = Field(index=True)
    status: str = Field(default="pending")
    context: Dict[str, Any] | None = Field(default=None, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=utcnow)
    dispatched_at: datetime | None = Field(default=None, nullable=True)


class ExperimentType(str, Enum):
    IMAGE = "image"
    TITLE = "title"
    THUMBNAIL = "thumbnail"
    TAGS = "tags"
    DESCRIPTION = "description"
    PRICE = "price"


class ABTest(SQLModel, table=True):
    """Top level A/B test container."""

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    experiment_type: "ExperimentType"
    product_id: Optional[int] = Field(default=None, index=True)
    status: str = Field(default="running", index=True)
    winner_variant_id: Optional[int] = Field(default=None, nullable=True)
    start_time: datetime | None = None
    end_time: datetime | None = None
    created_at: datetime = Field(default_factory=utcnow)


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
    event_type: EventType = Field(index=True)
    path: str
    user_id: Optional[int] = Field(default=None, index=True)
    meta: Dict[str, Any] | None = Field(
        default=None, sa_column=Column("metadata", JSON)
    )
    created_at: datetime = Field(default_factory=utcnow, index=True)


class OAuthProvider(str, Enum):
    ETSY = "etsy"
    PRINTIFY = "printify"
    STRIPE = "stripe"


class OAuthState(SQLModel, table=True):
    state: str = Field(primary_key=True, max_length=255)
    user_id: int
    provider: OAuthProvider
    code_verifier: str | None = None
    redirect_uri: str
    created_at: datetime = Field(default_factory=utcnow)


class OAuthCredential(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int
    provider: OAuthProvider
    access_token: str
    refresh_token: Optional[str] = None
    expires_at: datetime | None = None
    scope: Optional[str] = None
    account_id: Optional[str] = None
    account_name: Optional[str] = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)


class UserSession(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int
    token_hash: str = Field(index=True, unique=True, max_length=128)
    expires_at: datetime
    created_at: datetime = Field(default_factory=utcnow)


class Store(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(index=True)
    name: str
    marketplace: str = Field(default="etsy", index=True)
    region: str = "US"
    currency: str = "USD"
    is_default: bool = True
    created_at: datetime = Field(default_factory=utcnow)


class BrandProfile(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(index=True)
    name: str = "PODPusher Default"
    tone: str = "Humorous, Positive"
    audience: str = "Adults, Parents"
    interests: List[str] = Field(default_factory=list, sa_column=Column(JSON))
    banned_topics: List[str] = Field(default_factory=list, sa_column=Column(JSON))
    preferred_products: List[str] = Field(default_factory=list, sa_column=Column(JSON))
    region: str = "US"
    language: str = "en"
    active: bool = True
    updated_at: datetime = Field(default_factory=utcnow, index=True)


class SavedNiche(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(index=True)
    niche: str = Field(index=True)
    score: int = 0
    context: Dict[str, Any] | None = Field(default=None, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=utcnow, index=True)


class SavedSearch(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(index=True)
    name: str
    query: str
    filters: Dict[str, Any] | None = Field(default=None, sa_column=Column(JSON))
    result_count: int = 0
    created_at: datetime = Field(default_factory=utcnow, index=True)


class WatchlistItem(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(index=True)
    item_type: str = Field(index=True)
    name: str = Field(index=True)
    context: Dict[str, Any] | None = Field(default=None, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=utcnow, index=True)


class SeasonalEvent(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: Optional[int] = Field(default=None, index=True)
    name: str = Field(index=True)
    event_date: datetime = Field(index=True)
    region: str = Field(default="US", index=True)
    language: str = "en"
    marketplace: str = "etsy"
    category: str = "all"
    priority: str = Field(default="medium", index=True)
    opportunity_score: int = 0
    keywords: List[Dict[str, Any]] = Field(default_factory=list, sa_column=Column(JSON))
    product_categories: List[Dict[str, Any]] = Field(
        default_factory=list, sa_column=Column(JSON)
    )
    saved: bool = False
    created_at: datetime = Field(default_factory=utcnow)


class ListingDraftRevision(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    draft_id: int = Field(index=True)
    title: str
    description: str
    tags: List[str] = Field(default_factory=list, sa_column=Column(JSON))
    metadata_json: Dict[str, Any] | None = Field(default=None, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=utcnow, index=True)


class ListingOptimization(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    draft_id: int = Field(index=True)
    score: int = 0
    seo_score: int = 0
    compliance_status: str = "unknown"
    checks: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    source: str = "local_estimator"
    is_estimated: bool = True
    confidence: float = 0.74
    updated_at: datetime = Field(default_factory=utcnow, index=True)


class ABExperimentEvent(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    test_id: int = Field(index=True)
    variant_id: Optional[int] = Field(default=None, index=True)
    event_type: str = Field(index=True)
    value: int = 1
    context: Dict[str, Any] | None = Field(default=None, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=utcnow, index=True)


class NotificationRule(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(index=True)
    name: str
    metric: str
    operator: str = "less_than"
    threshold: float = 0
    window: str = "1 day"
    channels: List[str] = Field(default_factory=list, sa_column=Column(JSON))
    active: bool = True
    created_at: datetime = Field(default_factory=utcnow, index=True)


class AutomationJob(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(index=True)
    name: str
    frequency: str
    next_run: datetime = Field(index=True)
    status: str = Field(default="on_track", index=True)
    category: str = "system"
    metadata_json: Dict[str, Any] | None = Field(default=None, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=utcnow)


class UsageLedger(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(index=True)
    resource_type: str = Field(index=True)
    quantity: int = 0
    source: str = "local"
    created_at: datetime = Field(default_factory=utcnow, index=True)


class TeamMember(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(index=True)
    email: str = Field(index=True)
    name: str
    role: str = "viewer"
    permissions: List[str] = Field(default_factory=list, sa_column=Column(JSON))
    status: str = "active"
    last_active_at: datetime = Field(default_factory=utcnow, index=True)
    created_at: datetime = Field(default_factory=utcnow)
