import pytest
from fastapi import Depends, FastAPI
from httpx import ASGITransport, AsyncClient

from services.auth.service import create_session
from services.common.auth import optional_user_id, require_user_id
from services.common.database import init_db


app = FastAPI()


@app.get("/required")
async def required_route(user_id: int = Depends(require_user_id)):
    return {"user_id": user_id}


@app.get("/optional")
async def optional_route(user_id: int | None = Depends(optional_user_id)):
    return {"user_id": user_id}


@pytest.mark.asyncio
async def test_require_user_id_rejects_invalid_bearer_even_with_user_header():
    await init_db()
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get(
            "/required",
            headers={
                "Authorization": "Bearer invalid-token",
                "X-User-Id": "9",
            },
        )

    assert resp.status_code == 401
    assert resp.json()["detail"] == "Authentication required"


@pytest.mark.asyncio
async def test_require_user_id_accepts_x_user_id_without_bearer():
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/required", headers={"X-User-Id": "7"})

    assert resp.status_code == 200
    assert resp.json() == {"user_id": 7}


@pytest.mark.asyncio
async def test_require_user_id_accepts_valid_bearer():
    await init_db()
    token, _ = await create_session(33)
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/required", headers={"Authorization": f"Bearer {token}"})

    assert resp.status_code == 200
    assert resp.json() == {"user_id": 33}


@pytest.mark.asyncio
async def test_optional_user_id_does_not_fallback_on_invalid_bearer():
    await init_db()
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get(
            "/optional",
            headers={
                "Authorization": "Bearer invalid-token",
                "X-User-Id": "12",
            },
        )

    assert resp.status_code == 200
    assert resp.json() == {"user_id": None}


@pytest.mark.asyncio
async def test_optional_user_id_falls_back_to_header_without_authorization():
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/optional", headers={"X-User-Id": "12"})

    assert resp.status_code == 200
    assert resp.json() == {"user_id": 12}
