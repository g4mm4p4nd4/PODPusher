import pytest
from httpx import ASGITransport, AsyncClient

from services.common.database import get_session, init_db
from services.models import BrandProfile, TeamMember, User
from services.settings.api import app as settings_app


def _transport():
    return ASGITransport(app=settings_app)


@pytest.mark.asyncio
async def test_settings_localization_brand_user_and_integration_mutations():
    await init_db()
    transport = _transport()

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        localization_resp = await client.patch(
            "/localization",
            json={
                "default_language": "fr",
                "marketplace_regions": ["US", "FR"],
                "currency": "EUR",
                "date_format": "DD MMM YYYY",
                "localized_niche_targeting": True,
                "primary_targeting_region": "FR",
                "timezone": "Europe/Paris",
            },
            headers={"X-User-Id": "1"},
        )
        assert localization_resp.status_code == 200
        assert localization_resp.json()["saved"] is True
        assert localization_resp.json()["localization"]["currency"] == "EUR"
        assert localization_resp.json()["provenance"]["source"] == "user_and_brandprofile_tables"

        brand_resp = await client.post(
            "/brand-profiles",
            json={
                "name": "Paris Studio",
                "tone": "Warm",
                "audience": "Gift buyers",
                "interests": ["Home"],
                "banned_topics": ["Politics"],
                "preferred_products": ["Mugs"],
                "region": "FR",
                "language": "fr",
                "active": True,
            },
            headers={"X-User-Id": "1"},
        )
        assert brand_resp.status_code == 200
        profile_id = brand_resp.json()["profile"]["id"]

        default_resp = await client.put(
            f"/brand-profiles/{profile_id}/default",
            json={},
            headers={"X-User-Id": "1"},
        )
        assert default_resp.status_code == 200
        assert default_resp.json()["profile"]["active"] is True

        invite_resp = await client.post(
            "/users/invite",
            json={"email": "editor@podpusher.com", "role": "Editor"},
            headers={"X-User-Id": "1"},
        )
        assert invite_resp.status_code == 200
        member_id = invite_resp.json()["member"]["id"]

        role_resp = await client.patch(
            f"/users/{member_id}/role",
            json={"role": "Manager", "permissions": ["Listings"], "status": "active"},
            headers={"X-User-Id": "1"},
        )
        assert role_resp.status_code == 200
        assert role_resp.json()["member"]["role"] == "Manager"

        integration_resp = await client.post(
            "/integrations/slack/configure",
            json={"action": "configure"},
            headers={"X-User-Id": "1"},
        )
        assert integration_resp.status_code == 200
        assert integration_resp.json()["status"] == "credentials_missing"
        assert integration_resp.json()["is_demo"] is True

    async with get_session() as session:
        user = await session.get(User, 1)
        profile = await session.get(BrandProfile, profile_id)
        member = await session.get(TeamMember, member_id)
        assert user.preferred_currency == "EUR"
        assert profile.active is True
        assert member.role == "Manager"


@pytest.mark.asyncio
async def test_usage_ledger_returns_explicit_demo_state_when_empty():
    await init_db()
    transport = _transport()
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/usage-ledger", headers={"X-User-Id": "1"})
    assert resp.status_code == 200
    assert resp.json()["demo_state"] is True
    assert resp.json()["items"][0]["provenance"]["is_estimated"] is True
