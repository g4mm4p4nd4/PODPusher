from typing import Optional, List
from sqlmodel import SQLModel, Field
from sqlalchemy import Column, JSON
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
    rating: Optional[int] = None
    tags: Optional[List[str]] = Field(default=None, sa_column=Column(JSON))
    flagged: Optional[bool] = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Listing(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    product_id: int
    etsy_url: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    plan: str = "free"
    images_used: int = 0
    last_reset: datetime = Field(default_factory=datetime.utcnow)


class Notification(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int
    message: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    read: bool = False
