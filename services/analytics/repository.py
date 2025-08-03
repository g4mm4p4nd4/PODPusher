from sqlmodel import select
from sqlalchemy.sql import func
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from ..models import AnalyticsEvent, Metric


async def create_event(session: AsyncSession, event: AnalyticsEvent) -> AnalyticsEvent:
    session.add(event)
    await session.commit()
    await session.refresh(event)
    return event


def _event_query(event_type: str | None = None):
    stmt = select(AnalyticsEvent)
    if event_type:
        stmt = stmt.where(AnalyticsEvent.event_type == event_type)
    return stmt


async def fetch_events(session: AsyncSession, event_type: str | None = None) -> list[AnalyticsEvent]:
    result = await session.exec(_event_query(event_type))
    return result.all()


async def aggregate_events(session: AsyncSession, event_type: str | None = None):
    stmt = select(AnalyticsEvent.path, func.count(AnalyticsEvent.id).label("count"))
    if event_type:
        stmt = stmt.where(AnalyticsEvent.event_type == event_type)
    stmt = stmt.group_by(AnalyticsEvent.path)
    result = await session.exec(stmt)
    return result.all()


async def create_metric(session: AsyncSession, metric: Metric) -> Metric:
    session.add(metric)
    await session.commit()
    await session.refresh(metric)
    return metric


async def fetch_metrics(session: AsyncSession) -> list[Metric]:
    result = await session.exec(select(Metric))
    return result.all()
