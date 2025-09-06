from fastapi.testclient import TestClient
from services.gateway.api import app

client = TestClient(app)


def sample_products():
    return [
        {
            "title": "Test",
            "description": "Desc",
            "price": 9.99,
            "category": "shirts",
            "variants": [],
            "image_urls": ["http://example.com/img.png"],
        }
    ]


def test_bulk_create_json():
    resp = client.post("/api/bulk_create", json={"products": sample_products()})
    assert resp.status_code == 200
    data = resp.json()
    assert data["created"] == 1
    assert data["errors"] == []


def test_bulk_create_csv():
    csv_content = "title,description,price,category,image_urls\nA,B,10,cat,http://example.com/img.png"
    files = {"file": ("products.csv", csv_content, "text/csv")}
    resp = client.post("/api/bulk_create", files=files)
    assert resp.status_code == 200
    data = resp.json()
    assert data["created"] == 1


def test_bulk_create_invalid():
    bad = [{"title": "", "description": "", "price": -1, "category": ""}]
    resp = client.post("/api/bulk_create", json={"products": bad})
    assert resp.status_code == 200
    data = resp.json()
    assert data["created"] == 0
    assert data["errors"]
