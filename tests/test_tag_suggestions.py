import pytest
from services.ideation.service import suggest_tags
from services.common.database import init_db


@pytest.mark.asyncio
async def test_tag_suggestions_rank_by_history():
    await init_db()
    tags = await suggest_tags('cat t-shirt', '')
    assert tags[0] == 'cat'
    assert 't-shirt' in tags
