import pytest
from services.common.database import init_db, get_session
from services.models import Trend, Idea, Product
from services.search.service import search_products


@pytest.mark.asyncio
async def test_search_pagination():
    await init_db()
    async with get_session() as session:
        t = Trend(term='term', category='cat')
        session.add(t)
        await session.commit()
        await session.refresh(t)
        for i in range(2):
            idea = Idea(trend_id=t.id, description=f'desc {i}')
            session.add(idea)
            await session.commit()
            await session.refresh(idea)
            prod = Product(idea_id=idea.id, image_url=f'{i}.png', rating=5)
            session.add(prod)
            await session.commit()
    res = await search_products(page=2, page_size=1)
    assert res['page'] == 2
    assert res['items'][0]['image_url'] == '1.png'
