from typing import List
from pytrends.request import TrendReq
from ..models import Trend
from ..common.database import get_session


FALLBACK_TRENDS = {
    "animals": [
        "cute dog designs",
        "funny cat quotes",
        "pet memorial gifts",
    ],
    "activism": [
        "human rights slogans",
        "mental health awareness",
        "climate change posters",
    ],
    "family": [
        "best dad ever",
        "family reunion shirts",
        "new mom gifts",
    ],
    "humor": [
        "meme t-shirts",
        "sarcastic quotes",
        "dad jokes",
    ],
    "jobs": [
        "nurse life",
        "teacher appreciation",
        "coding humor",
    ],
    "fitness": [
        "gym motivation",
        "yoga lifestyle",
        "running clubs",
    ],
    "sustainability": [
        "zero waste living",
        "reusable bags",
        "plant trees",
    ],
    "love": [
        "couples goals",
        "wedding season",
        "valentines gifts",
    ],
    "music": [
        "retro vinyl",
        "festival outfits",
        "guitar lovers",
    ],
    "food": [
        "coffee lovers",
        "baking trends",
        "taco Tuesday",
    ],
}

# Fallback product categories for 2025 based on market research
FALLBACK_CATEGORIES = {
    "apparel": [
        "unisex t-shirts",
        "oversized hoodies",
        "athleisure",
        "yoga pants",
        "leggings",
    ],
    "home_decor": [
        "coffee mugs",
        "canvases",
        "posters",
        "acrylic plaques",
        "metal prints",
        "wall decals",
        "doormats",
        "carpets",
        "pillows",
        "blankets",
        "candles",
        "coasters",
    ],
    "pet_items": [
        "harnesses",
        "leashes",
        "bandanas",
        "pet clothing",
        "beds",
        "bowls",
        "collars",
        "tags",
        "blankets",
    ],
    "jewelry": ["engraved bracelets", "engraved necklaces"],
    "accessories": [
        "tote bags",
        "stickers",
        "caps",
        "backpacks",
        "bandanas",
        "patches",
        "socks",
        "beanies",
        "bucket hats",
        "flip-flops",
        "belt bags",
    ],
    "tech_accessories": [
        "phone cases",
        "wireless chargers",
        "mousepads",
        "laptop sleeves",
        "popsocket grips",
        "bluetooth speakers",
        "water bottles",
    ],
    "athletic_accessories": [
        "yoga mats",
        "gym gear",
        "gloves",
        "backpacks",
        "duffle bags",
    ],
    "holiday_items": [
        "Valentine’s shirts",
        "Mother’s Day tote bags",
        "Father’s Day cards",
        "Halloween costumes",
        "Christmas ornaments",
        "New Year greeting cards",
        "back-to-school stationery",
    ],
}


async def fetch_trends(category: str | None = None) -> List[dict]:
    terms = []
    try:
        pytrends = TrendReq()
        if category:
            pytrends.build_payload([category], timeframe="now 7-d")
            data = pytrends.related_queries().get(category, {}).get("top")
            if data is not None:
                terms = data["query"].tolist()[:10]
        else:
            result = pytrends.trending_searches(pn="united_states").head(10)
            terms = result[0].tolist()
    except Exception:
        pass
    if not terms:
        if category:
            terms = FALLBACK_TRENDS.get(category.lower(), [])[:10]
        else:
            for vals in FALLBACK_TRENDS.values():
                terms.extend(vals)
            terms = terms[:10]

    cat = category.lower() if category else "general"
    trends = []
    async with get_session() as session:
        for term in terms:
            trend = Trend(term=term, category=cat)
            session.add(trend)
            await session.commit()
            await session.refresh(trend)
            trends.append({"term": trend.term, "category": trend.category})
    return trends


def get_trending_categories(category: str | None = None) -> List[dict]:
    """Return 2025 trending product categories and popular items."""

    if category:
        key = category.lower()
        items = FALLBACK_CATEGORIES.get(key)
        if items:
            return [{"name": key, "items": items}]
        return []
    return [
        {"name": name, "items": items} for name, items in FALLBACK_CATEGORIES.items()
    ]
