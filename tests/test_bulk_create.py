import pytest
from fastapi.testclient import TestClient

from services.gateway.api import app
from services.listing_composer import bulk_service
from services.listing_composer.bulk_service import (
    ProductDefinition,
    parse_csv,
    create_listings,
)


def test_parse_csv():
    data = (
        "title,description,base_product_type,variants,tags\n"
        "T1,Desc,shirt,red;blue,funny;dog\n"
    ).encode()
    products = parse_csv(data)
    assert products[0].title == "T1"
    assert products[0].variants == ["red", "blue"]
    assert products[0].tags == ["funny", "dog"]


def test_parse_csv_missing_field():
    data = (
        "title,description,base_product_type,variants\n" ",Desc,shirt,red\n"
    ).encode()
    with pytest.raises(ValueError):
        parse_csv(data)


@pytest.mark.asyncio
async def test_create_listings(monkeypatch):
    calls: list[dict] = []

    def fake_publish(prod: dict):
        calls.append(prod)
        return {"id": len(calls)}

    monkeypatch.setattr(bulk_service, "publish_listing", fake_publish)
    products = [
        ProductDefinition(
            title="A",
            description="d",
            base_product_type="shirt",
            variants=["v1"],
        ),
        ProductDefinition(
            title="B",
            description="d",
            base_product_type="shirt",
            variants=["v2"],
        ),
    ]
    result = await create_listings(products)
    assert result.created == [1, 2]
    assert result.errors == []


def test_bulk_create_endpoint(monkeypatch):
    def fake_publish(prod: dict):
        return {"id": 99}

    monkeypatch.setattr(bulk_service, "publish_listing", fake_publish)
    client = TestClient(app)
    payload = [
        {
            "title": "T",
            "description": "D",
            "base_product_type": "shirt",
            "variants": ["v1"],
        }
    ]
    resp = client.post("/api/bulk_create", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["created"] == [99]
    assert data["errors"] == []
