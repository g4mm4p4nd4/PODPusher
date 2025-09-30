import pytest
from datetime import datetime, timedelta
from httpx import ASGITransport, AsyncClient
from sqlmodel import select

from services.auth.api import app as auth_app
from services.auth import service as auth_service
from services.auth.service import create_authorization_url, exchange_code
from services.integration import service as integration_service
from services.common.database import get_session, init_db
from services.models import OAuthCredential, OAuthProvider, OAuthState


class DummyResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self):
        return self._payload


class DummyClient:
    def __init__(self, *args, **kwargs):
        self.last_request = None

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def post(self, url, data=None, headers=None):
        self.last_request = {"url": url, "data": data, "headers": headers}
        return DummyResponse(
            {
                "access_token": "token-123",
                "refresh_token": "refresh-456",
                "expires_in": 3600,
                "scope": "listings_r",
                "account_id": "shop_99",
                "account_name": "My Shop",
            }
        )


@pytest.mark.asyncio
async def test_create_authorization_url_persists_state(monkeypatch):
    await init_db()
    monkeypatch.setenv("ETSY_CLIENT_ID", "cid")
    monkeypatch.setenv("ETSY_CLIENT_SECRET", "secret")
    url = await create_authorization_url(10, "etsy", "https://example.com/callback")
    assert "state=" in url
    async with get_session() as session:
        result = await session.exec(select(OAuthState))
        state = result.first()
        assert state is not None
        assert state.user_id == 10


@pytest.mark.asyncio
async def test_exchange_code_stores_credentials(monkeypatch):
    await init_db()
    monkeypatch.setenv("ETSY_CLIENT_ID", "cid")
    monkeypatch.setenv("ETSY_CLIENT_SECRET", "secret")

    await create_authorization_url(11, "etsy", "https://example.com/return")
    async with get_session() as session:
        result = await session.exec(select(OAuthState))
        state_record = result.first()
        state_value = state_record.state

    monkeypatch.setattr(auth_service, "httpx", type("MockHttpx", (), {"AsyncClient": DummyClient}))
    data = await exchange_code(11, "etsy", code="abc", state=state_value)
    assert data["provider"] == "etsy"

    async with get_session() as session:
        result = await session.exec(select(OAuthCredential))
        credential = result.first()
        assert credential is not None
        assert credential.user_id == 11
        assert credential.access_token == "token-123"


@pytest.mark.asyncio
async def test_session_roundtrip():
    await init_db()
    token, _ = await auth_service.create_session(77)
    assert token
    resolved = await auth_service.resolve_session_token(token)
    assert resolved == 77
    await auth_service.revoke_session(token)
    assert await auth_service.resolve_session_token(token) is None


@pytest.mark.asyncio
async def test_auth_api_authorize_flow(monkeypatch):
    await init_db()
    monkeypatch.setenv("PRINTIFY_CLIENT_ID", "pid")
    monkeypatch.setenv("PRINTIFY_CLIENT_SECRET", "psecret")

    transport = ASGITransport(app=auth_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/session",
            json={"user_id": 21},
        )
        assert resp.status_code == 200
        token = resp.json()["token"]

        resp = await client.post(
            "/printify/authorize",
            json={"redirect_uri": "https://example.com/oauth"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        assert "authorization_url" in resp.json()


class RefreshClient:
    def __init__(self, *args, **kwargs):
        self.last_request = None

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def post(self, url, data=None, headers=None):
        self.last_request = {"url": url, "data": data, "headers": headers}
        return DummyResponse(
            {
                "access_token": "token-refreshed",
                "refresh_token": "refresh-updated",
                "expires_in": 7200,
                "scope": "shop.read",
            }
        )


@pytest.mark.asyncio
async def test_refresh_token_rotation(monkeypatch):
    await init_db()
    monkeypatch.setenv("PRINTIFY_CLIENT_ID", "pid")
    monkeypatch.setenv("PRINTIFY_CLIENT_SECRET", "secret")

    async with get_session() as session:
        credential = OAuthCredential(
            user_id=33,
            provider=OAuthProvider.PRINTIFY,
            access_token="old-token",
            refresh_token="stale-refresh",
            expires_at=datetime.utcnow() - timedelta(minutes=10),
        )
        session.add(credential)
        await session.commit()
        await session.refresh(credential)
        stored_id = credential.id

    monkeypatch.setattr(auth_service, "httpx", type("MockHttpx", (), {"AsyncClient": RefreshClient}))

    creds = await integration_service.load_oauth_credentials(33, OAuthProvider.PRINTIFY)
    assert creds is not None
    assert creds["access_token"] == "token-refreshed"
    assert creds["refresh_token"] == "refresh-updated"

    async with get_session() as session:
        saved = await session.get(OAuthCredential, stored_id)
        assert saved is not None
        assert saved.access_token == "token-refreshed"
        assert saved.refresh_token == "refresh-updated"
        assert saved.expires_at and saved.expires_at > datetime.utcnow()


@pytest.mark.asyncio
async def test_prune_expired_oauth_records(monkeypatch):
    await init_db()
    monkeypatch.setattr(auth_service, "STATE_TTL_MINUTES", 1)
    monkeypatch.setattr(auth_service, "CREDENTIAL_RETENTION_DAYS", 1)

    stale_state_value = "stale-state"
    async with get_session() as session:
        session.add(
            OAuthState(
                state=stale_state_value,
                user_id=50,
                provider=OAuthProvider.ETSY,
                code_verifier=None,
                redirect_uri="https://example.com/return",
                created_at=datetime.utcnow() - timedelta(minutes=10),
            )
        )
        session.add(
            OAuthState(
                state="fresh",
                user_id=50,
                provider=OAuthProvider.ETSY,
                code_verifier=None,
                redirect_uri="https://example.com/return",
            )
        )
        expired_credential = OAuthCredential(
            user_id=50,
            provider=OAuthProvider.PRINTIFY,
            access_token="expired",
            refresh_token=None,
            expires_at=datetime.utcnow() - timedelta(days=10),
        )
        session.add(expired_credential)
        session.add(
            OAuthCredential(
                user_id=50,
                provider=OAuthProvider.ETSY,
                access_token="active",
                refresh_token="keep",
                expires_at=datetime.utcnow() + timedelta(days=10),
            )
        )
        await session.commit()

    await auth_service.prune_expired_oauth_records()

    async with get_session() as session:
        state = await session.get(OAuthState, stale_state_value)
        assert state is None
        result = await session.exec(select(OAuthCredential))
        remaining = result.all()
        assert any(cred.access_token == "active" for cred in remaining)
        assert all(cred.access_token != "expired" for cred in remaining)


@pytest.mark.asyncio
async def test_delete_oauth_credential_endpoint():
    await init_db()
    token, _ = await auth_service.create_session(77)
    async with get_session() as session:
        session.add(
            OAuthCredential(
                user_id=77,
                provider=OAuthProvider.PRINTIFY,
                access_token="token",
            )
        )
        await session.commit()

    transport = ASGITransport(app=auth_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.delete(
            "/credentials/printify",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200

    async with get_session() as session:
        result = await session.exec(
            select(OAuthCredential).where(OAuthCredential.user_id == 77)
        )
        assert result.first() is None
