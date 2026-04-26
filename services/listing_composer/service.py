import csv
import io
from datetime import datetime, timedelta
from typing import Any, Optional
from pydantic import BaseModel, Field
from sqlmodel import select

from ..common.time import utcnow
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
    niche: str | None = None
    primary_keyword: str | None = None
    product_type: str | None = None
    target_audience: str | None = None
    materials: str | None = None
    occasion: str | None = None
    holiday: str | None = None
    recipient: str | None = None
    style: str | None = None
    updated_at: datetime | None = None
    revision_count: int = 0
    provenance: dict[str, Any] | None = None


class DraftRevisionPayload(BaseModel):
    id: int
    draft_id: int
    title: str
    description: str
    tags: list[str]
    metadata: dict[str, Any]
    created_at: datetime
    provenance: dict[str, Any]


class DraftListResponse(BaseModel):
    items: list[DraftPayload]
    total: int
    page: int
    page_size: int
    sort_by: str
    sort_order: str
    provenance: dict[str, Any]


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


class PublishQueueListResponse(BaseModel):
    items: list[PublishQueueResponse]
    total: int
    page: int
    page_size: int
    provenance: dict[str, Any]


def _provenance(
    source: str,
    *,
    estimated: bool = False,
    confidence: float = 0.9,
    updated_at: datetime | None = None,
) -> dict[str, Any]:
    return {
        "source": source,
        "is_estimated": estimated,
        "updated_at": (updated_at or utcnow()).isoformat(),
        "confidence": confidence,
    }


def _context_metadata(data: DraftPayload) -> dict[str, Any]:
    return {
        "language": data.language,
        "field_order": data.field_order,
        "niche": data.niche,
        "primary_keyword": data.primary_keyword,
        "product_type": data.product_type,
        "target_audience": data.target_audience,
        "materials": data.materials,
        "occasion": data.occasion,
        "holiday": data.holiday,
        "recipient": data.recipient,
        "style": data.style,
    }


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
    metadata = _context_metadata(data)
    async with get_session() as session:
        if data.id:
            existing = await session.get(ListingDraft, data.id)
            if existing:
                existing.title = data.title
                existing.description = data.description
                existing.tags = data.tags
                existing.language = data.language
                existing.field_order = data.field_order
                existing.updated_at = utcnow()
                await session.commit()
                await session.refresh(existing)
                session.add(
                    ListingDraftRevision(
                        draft_id=existing.id,
                        title=existing.title,
                        description=existing.description,
                        tags=existing.tags,
                        metadata_json=metadata,
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
                    **metadata,
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


async def draft_to_payload(draft: ListingDraft) -> DraftPayload:
    async with get_session() as session:
        revisions = (
            await session.exec(
                select(ListingDraftRevision)
                .where(ListingDraftRevision.draft_id == draft.id)
                .order_by(ListingDraftRevision.created_at.desc())
            )
        ).all()
    metadata = revisions[0].metadata_json if revisions else {}
    return DraftPayload(
        id=draft.id,
        title=draft.title,
        description=draft.description,
        tags=draft.tags,
        language=draft.language,
        field_order=draft.field_order,
        niche=(metadata or {}).get("niche"),
        primary_keyword=(metadata or {}).get("primary_keyword"),
        product_type=(metadata or {}).get("product_type"),
        target_audience=(metadata or {}).get("target_audience"),
        materials=(metadata or {}).get("materials"),
        occasion=(metadata or {}).get("occasion"),
        holiday=(metadata or {}).get("holiday"),
        recipient=(metadata or {}).get("recipient"),
        style=(metadata or {}).get("style"),
        updated_at=draft.updated_at,
        revision_count=len(revisions),
        provenance=_provenance(
            "listingdraft_table",
            estimated=False,
            confidence=0.96,
            updated_at=draft.updated_at,
        ),
    )


async def list_drafts(
    *,
    search: str | None = None,
    page: int = 1,
    page_size: int = 20,
    sort_by: str = "updated_at",
    sort_order: str = "desc",
) -> DraftListResponse:
    page = max(1, page)
    page_size = min(max(1, page_size), 100)
    async with get_session() as session:
        rows = (
            await session.exec(select(ListingDraft).order_by(ListingDraft.updated_at.desc()))
        ).all()
    query = (search or "").strip().lower()
    if query:
        rows = [
            draft
            for draft in rows
            if query in draft.title.lower()
            or query in draft.description.lower()
            or any(query in tag.lower() for tag in draft.tags)
        ]
    reverse = sort_order.lower() != "asc"
    if sort_by == "title":
        rows = sorted(rows, key=lambda draft: draft.title.lower(), reverse=reverse)
    else:
        rows = sorted(rows, key=lambda draft: draft.updated_at, reverse=reverse)
    total = len(rows)
    start = (page - 1) * page_size
    payloads = [await draft_to_payload(draft) for draft in rows[start:start + page_size]]
    return DraftListResponse(
        items=payloads,
        total=total,
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        sort_order="desc" if reverse else "asc",
        provenance=_provenance("listingdraft_table", estimated=False, confidence=0.96),
    )


async def get_draft_history(draft_id: int) -> list[DraftRevisionPayload] | None:
    async with get_session() as session:
        draft = await session.get(ListingDraft, draft_id)
        if not draft:
            return None
        revisions = (
            await session.exec(
                select(ListingDraftRevision)
                .where(ListingDraftRevision.draft_id == draft_id)
                .order_by(ListingDraftRevision.created_at.desc())
            )
        ).all()
    return [
        DraftRevisionPayload(
            id=revision.id,
            draft_id=revision.draft_id,
            title=revision.title,
            description=revision.description,
            tags=revision.tags,
            metadata=revision.metadata_json or {},
            created_at=revision.created_at,
            provenance=_provenance(
                "listingdraftrevision_table",
                estimated=False,
                confidence=0.96,
                updated_at=revision.created_at,
            ),
        )
        for revision in revisions
    ]


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
                "blocking": False,
                "credential_required_for_live_publish": True,
                "message": "Etsy credentials are not required for local queueing.",
            },
            "printify": {
                "status": "demo",
                "blocking": False,
                "credential_required_for_live_publish": True,
                "message": "Printify credentials are not required for local queueing.",
            },
            "openai": {
                "status": "not_required",
                "blocking": False,
                "credential_required_for_live_publish": False,
                "message": "Draft content is already generated or manually edited.",
            },
        }
        job = AutomationJob(
            user_id=user_id,
            name=f"Composer Publish Queue Draft {draft.id}",
            frequency="once",
            next_run=utcnow() + timedelta(minutes=5),
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


async def list_publish_queue(
    *,
    page: int = 1,
    page_size: int = 20,
    status: str | None = None,
) -> PublishQueueListResponse:
    page = max(1, page)
    page_size = min(max(1, page_size), 100)
    async with get_session() as session:
        rows = (
            await session.exec(
                select(AutomationJob)
                .where(AutomationJob.category == "listing_publish")
                .order_by(AutomationJob.created_at.desc())
            )
        ).all()
    if status and status != "all":
        rows = [job for job in rows if job.status == status]
    total = len(rows)
    start = (page - 1) * page_size
    items = []
    for job in rows[start:start + page_size]:
        metadata = job.metadata_json or {}
        integration_status = metadata.get("integration_status") or {}
        items.append(
            PublishQueueResponse(
                queue_item_id=job.id,
                draft_id=int(metadata.get("draft_id") or 0),
                status=job.status,
                mode=str(metadata.get("mode") or "demo"),
                message=(
                    "Draft is queued locally. Etsy and Printify remain credential-gated."
                ),
                integration_status=integration_status,
                created_at=job.created_at,
            )
        )
    return PublishQueueListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        provenance=_provenance("automationjob_table", estimated=False, confidence=0.94),
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
        revisions = (
            await session.exec(
                select(ListingDraftRevision)
                .where(ListingDraftRevision.draft_id == draft_id)
                .order_by(ListingDraftRevision.created_at.desc())
            )
        ).all()
        queued_jobs = (
            await session.exec(
                select(AutomationJob)
                .where(AutomationJob.category == "listing_publish")
                .order_by(AutomationJob.created_at.desc())
            )
        ).all()
        draft_jobs = [
            job
            for job in queued_jobs
            if int((job.metadata_json or {}).get("draft_id") or 0) == draft_id
        ]
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
                optimization.updated_at if optimization else utcnow()
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
                "revision_count": len(revisions),
                "latest_revision_id": revisions[0].id if revisions else None,
                "latest_revision_metadata": (
                    revisions[0].metadata_json if revisions else {}
                ),
                "publish_queue": [
                    {
                        "queue_item_id": job.id,
                        "status": job.status,
                        "mode": (job.metadata_json or {}).get("mode") or "demo",
                        "created_at": job.created_at.isoformat(),
                    }
                    for job in draft_jobs[:5]
                ],
                "integration_contract": {
                    "etsy": "credential_gated_non_blocking",
                    "printify": "credential_gated_non_blocking",
                    "openai": "not_required_for_manual_export",
                },
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
