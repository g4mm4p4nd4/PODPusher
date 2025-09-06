import json
import pytest
from httpx import AsyncClient, ASGITransport

from services.gateway.api import app as gateway_app
from services.common.database import init_db


@pytest.mark.asyncio
async def test_bulk_create_json_api():
    await init_db()
    transport = ASGITransport(app=gateway_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        data = [
            {
                "title": "Shirt",
                "description": "Desc",
                "price": 9.99,
                "category": "apparel",
                "variants": [{"sku": "s1", "price": 9.99}],
                "image_urls": ["http://example.com/img.png"],
            },
            {
                "title": "",
                "description": "Bad",
                "price": -1,
                "category": "apparel",
                "variants": [],
                "image_urls": [],
            },
        ]
        resp = await client.post("/api/bulk_create", json=data)
        assert resp.status_code == 200
        body = resp.json()
        assert len(body["created"]) == 1
        assert len(body["errors"]) == 1


@pytest.mark.asyncio
async def test_bulk_create_csv_api():
    await init_db()
    transport = ASGITransport(app=gateway_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        variants = json.dumps([{ "sku": "s1", "price": 9.99 }])
        images = json.dumps(["http://example.com/img.png"])
        import io, csv as csvmod
        out = io.StringIO()
        writer = csvmod.writer(out)
        writer.writerow(["title", "description", "price", "category", "variants", "image_urls"])
        writer.writerow(["Shirt", "Desc", 9.99, "apparel", variants, images])
        writer.writerow(["", "Bad", 9.99, "apparel", variants, images])
        csv_content = out.getvalue()
        files = {"file": ("products.csv", csv_content, "text/csv")}
        resp = await client.post("/api/bulk_create", files=files)
        assert resp.status_code == 200
        body = resp.json()
        assert len(body["created"]) == 1
        assert len(body["errors"]) == 1
