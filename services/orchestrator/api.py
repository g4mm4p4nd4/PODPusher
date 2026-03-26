from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, Field

from ..common.auth import require_user_id
from ..common.observability import register_observability
from .workers import (
    list_registered_schedules,
    publish_trend_signal,
    register_periodic_trend_signal,
    remove_periodic_trend_signal,
    start,
    stop,
)


@asynccontextmanager
async def _orchestrator_lifespan(_: FastAPI):
    await start()
    yield
    await stop()


app = FastAPI(lifespan=_orchestrator_lifespan)
register_observability(app, service_name="orchestrator")


class TrendEventRequest(BaseModel):
    trend: str = Field(min_length=1)
    source: str = "manual"


class TrendScheduleRequest(TrendEventRequest):
    interval_seconds: int = Field(default=3600, ge=60)


@app.post("/events/trend")
async def enqueue_trend_event(
    payload: TrendEventRequest,
    user_id: int = Depends(require_user_id),
):
    event = await publish_trend_signal(
        user_id=user_id,
        trend=payload.trend,
        source=payload.source,
    )
    return {"status": "accepted", "event": event}


@app.post("/schedules/trend")
async def create_trend_schedule(
    payload: TrendScheduleRequest,
    user_id: int = Depends(require_user_id),
):
    return register_periodic_trend_signal(
        user_id=user_id,
        trend=payload.trend,
        interval_seconds=payload.interval_seconds,
        source=payload.source,
    )


@app.get("/schedules")
async def list_schedules(
    user_id: int = Depends(require_user_id),
):
    return list_registered_schedules(user_id=user_id)


@app.delete("/schedules/{job_id}")
async def delete_schedule(
    job_id: str,
    user_id: int = Depends(require_user_id),
):
    removed = remove_periodic_trend_signal(job_id=job_id, user_id=user_id)
    if not removed:
        raise HTTPException(status_code=404, detail="Scheduled trend not found")
    return {"status": "deleted", "job_id": job_id}
