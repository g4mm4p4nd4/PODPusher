import pytest
from services.common.database import init_db
from services.listing_composer.service import DraftPayload, save_draft, get_draft


@pytest.mark.asyncio
async def test_save_and_get_draft():
    await init_db()
    payload = DraftPayload(
        title='t',
        description='d',
        tags=['a'],
        language='en',
        field_order=['title', 'description', 'tags'],
    )
    draft = await save_draft(payload)
    fetched = await get_draft(draft.id)
    assert fetched is not None
    assert fetched.title == 't'
