import asyncio
import base64
from fastapi.testclient import TestClient

from services.social_generator.api import app
from services.social_generator.service import generate_post


def test_generate_caption_english_tshirt():
    data = {
        "title": "Cool Tee",
        "description": "Soft and comfy",
        "tags": ["cool"],
        "product_type": "tshirt",
        "language": "en",
    }
    result = asyncio.run(generate_post(data))
    assert "Cool Tee" in result["caption"]
    assert result["image"] is not None
    base64.b64decode(result["image"])  # should not raise


def test_generate_caption_spanish_mug():
    data = {
        "title": "Taza",
        "description": "Bonita",
        "tags": ["cafe"],
        "product_type": "mug",
        "language": "es",
    }
    result = asyncio.run(generate_post(data))
    assert "Taza" in result["caption"]


def test_generate_endpoint():
    client = TestClient(app)
    resp = client.post(
        "/generate",
        json={"title": "Test", "description": "Desc", "product_type": "tshirt"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "caption" in body and "image" in body
