from typing import Optional
from sqlmodel import SQLModel, Field
from datetime import datetime


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
    rating: Optional[int] = Field(default=None, ge=1, le=5)
    tags: Optional[str] = None
    flagged: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Listing(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    product_id: int
    etsy_url: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
