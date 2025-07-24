from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from contextlib import asynccontextmanager
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./test.db")
engine = create_async_engine(DATABASE_URL, echo=False, future=True)


async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)
        await conn.run_sync(SQLModel.metadata.create_all)


@asynccontextmanager
async def get_session() -> AsyncSession:
    async with AsyncSession(engine) as session:
        yield session
