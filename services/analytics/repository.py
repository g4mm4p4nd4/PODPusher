from sqlmodel import select
from sqlalchemy.sql import func, case
from sqlmodel.ext.asyncio.session import AsyncSession
from ..models import AnalyticsEvent


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


async def fetch_events(
    session: AsyncSession, event_type: str | None = None
) -> list[AnalyticsEvent]:
    result = await session.exec(_event_query(event_type))
    return result.all()


async def aggregate_metrics(session: AsyncSession):
    stmt = select(
        AnalyticsEvent.path,
        func.sum(
            case((AnalyticsEvent.event_type == "page_view", 1), else_=0)
        ).label("views"),
        func.sum(
            case((AnalyticsEvent.event_type == "click", 1), else_=0)
        ).label("clicks"),
        func.sum(
            case((AnalyticsEvent.event_type == "conversion", 1), else_=0)
        ).label("conversions"),
    ).group_by(AnalyticsEvent.path)
    result = await session.exec(stmt)
    return result.all()
