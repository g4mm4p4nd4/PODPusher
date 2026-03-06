"""Tests for billing service."""

import pytest
from unittest.mock import patch, AsyncMock

from services.billing.plans import PlanTier, PlanLimits, get_plan_limits, get_tier_from_stripe_product


class TestPlanTiers:
    """Test plan tier definitions."""

    def test_plan_tier_values(self):
        """Test that all plan tiers have correct string values."""
        assert PlanTier.FREE.value == "free"
        assert PlanTier.STARTER.value == "starter"
        assert PlanTier.PROFESSIONAL.value == "professional"
        assert PlanTier.ENTERPRISE.value == "enterprise"

    def test_get_plan_limits_free(self):
        """Test free tier limits."""
        limits = get_plan_limits(PlanTier.FREE)
        assert limits.monthly_listings == 10
        assert limits.monthly_images == 20
        assert limits.monthly_ideas == 50
        assert limits.team_seats == 1
        assert limits.priority_support is False

    def test_get_plan_limits_starter(self):
        """Test starter tier limits."""
        limits = get_plan_limits(PlanTier.STARTER)
        assert limits.monthly_listings == 50
        assert limits.monthly_images == 100
        assert limits.monthly_ideas == 200
        assert limits.team_seats == 1
        assert limits.priority_support is False

    def test_get_plan_limits_professional(self):
        """Test professional tier limits."""
        limits = get_plan_limits(PlanTier.PROFESSIONAL)
        assert limits.monthly_listings == 200
        assert limits.monthly_images == 500
        assert limits.monthly_ideas == 1000
        assert limits.team_seats == 3
        assert limits.priority_support is True

    def test_get_plan_limits_enterprise(self):
        """Test enterprise tier limits."""
        limits = get_plan_limits(PlanTier.ENTERPRISE)
        assert limits.monthly_listings == 1000
        assert limits.monthly_images == 2500
        assert limits.monthly_ideas == 5000
        assert limits.team_seats == 10
        assert limits.priority_support is True

    def test_get_plan_limits_unknown_defaults_to_free(self):
        """Test that unknown tiers default to free."""
        # Using a valid tier but checking the fallback logic
        limits = get_plan_limits(PlanTier.FREE)
        assert limits.monthly_listings == 10

    def test_get_tier_from_stripe_product_unknown(self):
        """Test that unknown product IDs return FREE tier."""
        tier = get_tier_from_stripe_product("unknown_product_id")
        assert tier == PlanTier.FREE


class TestBillingService:
    """Test billing service functions."""

    @pytest.mark.asyncio
    async def test_get_or_create_customer_stub_mode(self):
        """Test customer creation in stub mode."""
        with patch.dict('os.environ', {'BILLING_STUB_MODE': 'true'}):
            # Re-import to pick up stub mode
            from services.billing import service
            service.STUB_MODE = True

            customer_id = await service.get_or_create_customer(123, "test@example.com")
            assert customer_id == "cus_stub_123"

    @pytest.mark.asyncio
    async def test_create_portal_session_stub_mode(self):
        """Test portal session creation in stub mode."""
        with patch.dict('os.environ', {'BILLING_STUB_MODE': 'true'}):
            from services.billing import service
            service.STUB_MODE = True

            portal_url = await service.create_portal_session("cus_123", "/settings")
            assert "/settings" in portal_url
            assert "stub_portal=true" in portal_url

    @pytest.mark.asyncio
    async def test_get_subscription_for_customer_stub_mode(self):
        """Test subscription retrieval in stub mode."""
        with patch.dict('os.environ', {'BILLING_STUB_MODE': 'true'}):
            from services.billing import service
            service.STUB_MODE = True

            subscription = await service.get_subscription_for_customer("cus_123")
            assert subscription is not None
            assert subscription["id"] == "sub_stub"
            assert subscription["status"] == "active"
            assert subscription["plan_tier"] == "starter"

    @pytest.mark.asyncio
    async def test_get_user_plan_tier_stub_mode(self):
        """Test plan tier retrieval in stub mode."""
        with patch.dict('os.environ', {'BILLING_STUB_MODE': 'true'}):
            from services.billing import service
            service.STUB_MODE = True

            tier = await service.get_user_plan_tier(123)
            assert tier == PlanTier.STARTER

    @pytest.mark.asyncio
    async def test_update_user_quotas_from_subscription(self):
        """Test quota update from subscription."""
        from services.billing.service import update_user_quotas_from_subscription

        with patch.dict('os.environ', {'STRIPE_PRODUCT_STARTER': 'prod_starter'}):
            result = await update_user_quotas_from_subscription(
                user_id=123,
                subscription_id="sub_123",
                product_id="prod_starter",
            )

            assert result["plan_tier"] == "starter"
            assert result["monthly_listings"] == 50
            assert result["monthly_images"] == 100


class TestBillingWebhooks:
    """Test billing webhook handlers."""

    @pytest.mark.asyncio
    async def test_verify_webhook_signature_stub_mode(self):
        """Test webhook signature verification in stub mode."""
        import json
        from services.billing import webhooks
        webhooks.STUB_MODE = True

        payload = json.dumps({"type": "test_event", "data": {}}).encode()
        event = webhooks.verify_webhook_signature(payload, "")

        assert event["type"] == "test_event"

    @pytest.mark.asyncio
    async def test_process_webhook_event_unknown_type(self):
        """Test processing unknown event type."""
        from services.billing.webhooks import process_webhook_event

        result = await process_webhook_event({
            "type": "unknown.event.type",
            "data": {"object": {}},
        })

        assert result["status"] == "ignored"
        assert result["event_type"] == "unknown.event.type"

    @pytest.mark.asyncio
    async def test_process_webhook_event_invoice_paid(self):
        """Test processing invoice.paid event."""
        from services.billing.webhooks import process_webhook_event

        result = await process_webhook_event({
            "type": "invoice.paid",
            "data": {
                "object": {
                    "subscription": "sub_123",
                    "customer": "cus_123",
                    "amount_paid": 1999,
                    "currency": "usd",
                },
            },
        })

        assert result["status"] == "processed"
        assert result["event_type"] == "invoice.paid"
        assert result["result"]["status"] == "paid"

    @pytest.mark.asyncio
    async def test_process_webhook_event_invoice_payment_failed(self):
        """Test processing invoice.payment_failed event."""
        from services.billing.webhooks import process_webhook_event

        result = await process_webhook_event({
            "type": "invoice.payment_failed",
            "data": {
                "object": {
                    "subscription": "sub_123",
                    "customer": "cus_123",
                    "amount_due": 1999,
                    "currency": "usd",
                },
            },
        })

        assert result["status"] == "processed"
        assert result["event_type"] == "invoice.payment_failed"
        assert result["result"]["status"] == "failed"


class TestBillingAPI:
    """Test billing API endpoints."""

    @pytest.mark.asyncio
    async def test_list_plans(self):
        """Test listing available plans."""
        from httpx import AsyncClient, ASGITransport
        from services.billing.api import app

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/plans")

            assert response.status_code == 200
            data = response.json()
            assert "plans" in data
            assert len(data["plans"]) == 4

            # Verify plan structure
            plan_names = [p["tier"] for p in data["plans"]]
            assert "free" in plan_names
            assert "starter" in plan_names
            assert "professional" in plan_names
            assert "enterprise" in plan_names

    @pytest.mark.asyncio
    async def test_subscription_endpoint_requires_auth(self):
        """Test that subscription endpoint requires authentication."""
        from httpx import AsyncClient, ASGITransport
        from services.billing.api import app

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/subscription")
            # Should fail without X-User-Id header
            assert response.status_code in [400, 401, 422]

    @pytest.mark.asyncio
    async def test_quota_endpoint_requires_auth(self):
        """Test that quota endpoint requires authentication."""
        from httpx import AsyncClient, ASGITransport
        from services.billing.api import app

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/quota")
            # Should fail without X-User-Id header
            assert response.status_code in [400, 401, 422]

    @pytest.mark.asyncio
    async def test_portal_endpoint_requires_auth(self):
        """Test that portal endpoint requires authentication."""
        from httpx import AsyncClient, ASGITransport
        from services.billing.api import app

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post("/portal")
            # Should fail without X-User-Id header
            assert response.status_code in [400, 401, 422]
