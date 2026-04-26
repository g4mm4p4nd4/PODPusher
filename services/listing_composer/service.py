import csv
import io
from datetime import datetime, timedelta
from typing import Any, Optional
from pydantic import BaseModel, Field
from sqlmodel import select
from ..control_center.service import compliance_payload, score_listing_payload
from ..models import (
    AutomationJob,
    ListingDraft,
    ListingDraftRevision,
    ListingOptimization,
)
from ..common.database import get_session


class DraftPayload(BaseModel):
    id: Optional[int] = None
    title: str
    description: str
    tags: list[str] = Field(default_factory=list)
    language: str = "en"
    field_order: list[str] = Field(default_factory=list)


class PublishQueueResponse(BaseModel):
    queue_item_id: int
    draft_id: int
    status: str
    mode: str
    message: str
    integration_status: dict[str, Any]
    created_at: datetime


class ExportPayload(BaseModel):
    draft_id: int
    title: str
    description: str
    tags: list[str]
    metadata: dict[str, Any]
    score: dict[str, Any]
    compliance: dict[str, Any]
    provenance: dict[str, Any]


def _score_and_compliance(draft: ListingDraft) -> tuple[dict[str, Any], dict[str, Any]]:
    score = score_listing_payload(
        {
            "title": draft.title,
            "description": draft.description,
            "tags": draft.tags,
            "primary_keyword": draft.tags[0] if draft.tags else "",
        }
    )
    compliance = compliance_payload(
        {"title": draft.title, "description": draft.description, "tags": draft.tags}
    )
    return score, compliance


async def save_draft(data: DraftPayload) -> ListingDraft:
    async with get_session() as session:
        if data.id:
            existing = await session.get(ListingDraft, data.id)
            if existing:
                existing.title = data.title
                existing.description = data.description
                existing.tags = data.tags
                existing.language = data.language
                existing.field_order = data.field_order
                existing.updated_at = datetime.utcnow()
                await session.commit()
                await session.refresh(existing)
                session.add(
                    ListingDraftRevision(
                        draft_id=existing.id,
                        title=existing.title,
                        description=existing.description,
                        tags=existing.tags,
                        metadata_json={
                            "language": existing.language,
                            "field_order": existing.field_order,
                        },
                    )
                )
                score, compliance = _score_and_compliance(existing)
                session.add(
                    ListingOptimization(
                        draft_id=existing.id,
                        score=score["optimization_score"],
                        seo_score=score["seo_score"],
                        compliance_status=compliance["status"],
                        checks={
                            "seo": score["checks"],
                            "compliance": compliance["checks"],
                        },
                    )
                )
                await session.commit()
                return existing
        draft = ListingDraft(
            title=data.title,
            description=data.description,
            tags=data.tags,
            language=data.language,
            field_order=data.field_order,
        )
        session.add(draft)
        await session.commit()
        await session.refresh(draft)
        session.add(
            ListingDraftRevision(
                draft_id=draft.id,
                title=draft.title,
                description=draft.description,
                tags=draft.tags,
                metadata_json={
                    "language": draft.language,
                    "field_order": draft.field_order,
                },
            )
        )
        score, compliance = _score_and_compliance(draft)
        session.add(
            ListingOptimization(
                draft_id=draft.id,
                score=score["optimization_score"],
                seo_score=score["seo_score"],
                compliance_status=compliance["status"],
                checks={"seo": score["checks"], "compliance": compliance["checks"]},
            )
        )
        await session.commit()
        return draft


async def get_draft(draft_id: int) -> Optional[ListingDraft]:
    async with get_session() as session:
        return await session.get(ListingDraft, draft_id)


async def queue_publish_job(
    draft_id: int, user_id: int = 1
) -> PublishQueueResponse | None:
    async with get_session() as session:
        draft = await session.get(ListingDraft, draft_id)
        if not draft:
            return None

        integration_status = {
            "etsy": {
                "status": "demo",
                "message": "Etsy credentials are not required for local queueing.",
            },
            "printify": {
                "status": "demo",
                "message": "Printify credentials are not required for local queueing.",
            },
            "openai": {
                "status": "not_required",
                "message": "Draft content is already generated or manually edited.",
            },
        }
        job = AutomationJob(
            user_id=user_id,
            name=f"Composer Publish Queue Draft {draft.id}",
            frequency="once",
            next_run=datetime.utcnow() + timedelta(minutes=5),
            status="pending",
            category="listing_publish",
            metadata_json={
                "draft_id": draft.id,
                "mode": "demo",
                "source": "listing_composer",
                "integration_status": integration_status,
            },
        )
        session.add(job)
        await session.commit()
        await session.refresh(job)
        return PublishQueueResponse(
            queue_item_id=job.id,
            draft_id=draft.id,
            status=job.status,
            mode="demo",
            message="Draft queued for demo publish. Connect Etsy and Printify to publish live.",
            integration_status=integration_status,
            created_at=job.created_at,
        )


async def build_export_payload(draft_id: int) -> ExportPayload | None:
    async with get_session() as session:
        draft = await session.get(ListingDraft, draft_id)
        if not draft:
            return None

        result = await session.exec(
            select(ListingOptimization)
            .where(ListingOptimization.draft_id == draft_id)
            .order_by(ListingOptimization.updated_at.desc())
            .limit(1)
        )
        optimization = result.first()
        live_score, live_compliance = _score_and_compliance(draft)

        score = {
            "optimization_score": (
                optimization.score if optimization else live_score["optimization_score"]
            ),
            "seo_score": (
                optimization.seo_score if optimization else live_score["seo_score"]
            ),
            "checks": (
                (optimization.checks or {}).get("seo", live_score["checks"])
                if optimization
                else live_score["checks"]
            ),
        }
        compliance = {
            "status": (
                optimization.compliance_status
                if optimization
                else live_compliance["status"]
            ),
            "checks": (
                (optimization.checks or {}).get("compliance", live_compliance["checks"])
                if optimization
                else live_compliance["checks"]
            ),
        }
        provenance = {
            "source": optimization.source if optimization else "local_estimator",
            "is_estimated": optimization.is_estimated if optimization else True,
            "confidence": optimization.confidence if optimization else 0.74,
            "updated_at": (
                optimization.updated_at if optimization else datetime.utcnow()
            ).isoformat(),
            "export_status": "ready",
            "mode": "download",
        }
        return ExportPayload(
            draft_id=draft.id,
            title=draft.title,
            description=draft.description,
            tags=draft.tags,
            metadata={
                "language": draft.language,
                "field_order": draft.field_order,
                "draft_updated_at": draft.updated_at.isoformat(),
            },
            score=score,
            compliance=compliance,
            provenance=provenance,
        )


def export_payload_to_csv(payload: ExportPayload) -> str:
    output = io.StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=[
            "draft_id",
            "title",
            "description",
            "tags",
            "metadata",
            "score",
            "compliance",
            "provenance",
        ],
    )
    writer.writeheader()
    writer.writerow(
        {
            "draft_id": payload.draft_id,
            "title": payload.title,
            "description": payload.description,
            "tags": ";".join(payload.tags),
            "metadata": payload.metadata,
            "score": payload.score,
            "compliance": payload.compliance,
            "provenance": payload.provenance,
        }
    )
    return output.getvalue()
