from fastapi import FastAPI, HTTPException, Query, Response
from pydantic import BaseModel, Field

from ..common.observability import register_observability
from ..control_center.service import (
    compliance_payload,
    generate_listing_payload,
    score_listing_payload,
)
from .service import (
    DraftPayload,
    PublishQueueResponse,
    build_export_payload,
    export_payload_to_csv,
    get_draft,
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
    return DraftPayload(**draft.model_dump())


@app.get("/drafts/{draft_id}", response_model=DraftPayload)
async def read_draft(draft_id: int):
    draft = await get_draft(draft_id)
    if not draft:
        raise HTTPException(status_code=404, detail="draft not found")
    return DraftPayload(**draft.model_dump())


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
