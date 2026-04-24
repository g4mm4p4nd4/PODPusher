from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from ..control_center.service import compliance_payload, score_listing_payload
from ..models import ListingDraft, ListingDraftRevision, ListingOptimization
from ..common.database import get_session


class DraftPayload(BaseModel):
    id: Optional[int] = None
    title: str
    description: str
    tags: list[str] = Field(default_factory=list)
    language: str = "en"
    field_order: list[str] = Field(default_factory=list)


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
                score = score_listing_payload(
                    {
                        "title": existing.title,
                        "description": existing.description,
                        "tags": existing.tags,
                        "primary_keyword": existing.tags[0] if existing.tags else "",
                    }
                )
                compliance = compliance_payload(
                    {
                        "title": existing.title,
                        "description": existing.description,
                        "tags": existing.tags,
                    }
                )
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
