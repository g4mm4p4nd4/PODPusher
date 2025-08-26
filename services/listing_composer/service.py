from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from ..models import ListingDraft
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
        return draft


async def get_draft(draft_id: int) -> Optional[ListingDraft]:
    async with get_session() as session:
        return await session.get(ListingDraft, draft_id)
