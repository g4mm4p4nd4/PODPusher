from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from ..common.observability import register_observability
from ..control_center.service import (
    compliance_payload,
    generate_listing_payload,
    score_listing_payload,
)
from .service import DraftPayload, get_draft, save_draft

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


@app.post("/generate")
async def generate(payload: ComposerGenerateRequest):
    return generate_listing_payload(payload.model_dump())


@app.post("/score")
async def score(payload: ComposerScoreRequest):
    return score_listing_payload(payload.model_dump())


@app.post("/compliance")
async def compliance(payload: ComposerComplianceRequest):
    return compliance_payload(payload.model_dump())
