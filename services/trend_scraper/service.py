from typing import List
from pytrends.request import TrendReq
from ..models import Trend
from ..common.database import get_session


async def fetch_trends() -> List[dict]:
    try:
        pytrends = TrendReq()
        result = pytrends.trending_searches(pn="united_states").head(10)
        terms = result[0].tolist()
    except Exception:
        terms = ["stub trend"]

    trends = []
    async with get_session() as session:
        for term in terms:
            trend = Trend(term=term, category="general")
            session.add(trend)
            await session.commit()
            await session.refresh(trend)
            trends.append({"term": trend.term, "category": trend.category})
    return trends
