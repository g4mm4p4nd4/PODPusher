from fastapi import FastAPI, HTTPException, Query, Response
from pydantic import BaseModel, Field

from ..common.observability import register_observability
from ..control_center.service import (
    compliance_payload,
    generate_listing_payload,
    score_listing_payload,
)
from .service import (
    DraftListResponse,
    DraftPayload,
    DraftRevisionPayload,
    PublishQueueListResponse,
    PublishQueueResponse,
    build_export_payload,
    draft_to_payload,
    export_payload_to_csv,
    get_draft,
    get_draft_history,
    list_drafts,
    list_publish_queue,
    queue_publish_job,
    save_draft,
)

app = FastAPI()
register_observability(app, service_name="listing_composer")


class ComposerGenerateRequest(BaseModel):
    niche: str = "Home Decor Wall Art"
    primary_keyword: str | None = None
    product_type: str = "Canvas Print"
    tone: str = "Warm & Inviting"
    target_audience: str = "Home Decor Enthusiasts"
    brand_rules: str | None = None


class ComposerScoreRequest(BaseModel):
    title: str
    description: str
    tags: list[str] = Field(default_factory=list)
    primary_keyword: str | None = None


class ComposerComplianceRequest(BaseModel):
    title: str
    description: str
    tags: list[str] = Field(default_factory=list)


@app.post("/drafts", response_model=DraftPayload)
async def create_draft(payload: DraftPayload):
    draft = await save_draft(payload)
    return await draft_to_payload(draft)


@app.get("/drafts", response_model=DraftListResponse)
async def read_drafts(
    search: str | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    sort_by: str = Query(default="updated_at", pattern="^(updated_at|title)$"),
    sort_order: str = Query(default="desc", pattern="^(asc|desc)$"),
):
    return await list_drafts(
        search=search,
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        sort_order=sort_order,
    )


@app.get("/drafts/{draft_id}", response_model=DraftPayload)
async def read_draft(draft_id: int):
    draft = await get_draft(draft_id)
    if not draft:
        raise HTTPException(status_code=404, detail="draft not found")
    return await draft_to_payload(draft)


@app.get("/drafts/{draft_id}/history", response_model=list[DraftRevisionPayload])
async def read_draft_history(draft_id: int):
    history = await get_draft_history(draft_id)
    if history is None:
        raise HTTPException(status_code=404, detail="draft not found")
    return history


@app.get("/publish-queue", response_model=PublishQueueListResponse)
async def read_publish_queue(
    status: str | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
):
    return await list_publish_queue(status=status, page=page, page_size=page_size)


@app.post("/drafts/{draft_id}/publish-queue", response_model=PublishQueueResponse)
async def publish_queue(draft_id: int):
    queued = await queue_publish_job(draft_id)
    if not queued:
        raise HTTPException(status_code=404, detail="draft not found")
    return queued


@app.get("/drafts/{draft_id}/export", response_model=None)
async def export_draft(
    draft_id: int,
    format: str = Query(default="json", pattern="^(json|csv)$"),
):
    payload = await build_export_payload(draft_id)
    if not payload:
        raise HTTPException(status_code=404, detail="draft not found")
    filename = f"listing-draft-{draft_id}.{format}"
    if format == "csv":
        return Response(
            content=export_payload_to_csv(payload),
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    return Response(
        content=payload.model_dump_json(),
        media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@app.post("/generate")
async def generate(payload: ComposerGenerateRequest):
    return generate_listing_payload(payload.model_dump())


@app.post("/score")
async def score(payload: ComposerScoreRequest):
    return score_listing_payload(payload.model_dump())


@app.post("/compliance")
async def compliance(payload: ComposerComplianceRequest):
    return compliance_payload(payload.model_dump())
