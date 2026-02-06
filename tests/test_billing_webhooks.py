"""Tests for billing webhook handlers."""

import json
import pytest
from unittest.mock import patch, MagicMock

from services.billing.webhooks import (
    verify_webhook_signature,
    process_webhook_event,
    HANDLED_EVENTS,
)
from services.billing.service import BillingError


class TestWebhookSignatureVerification:
    """Test Stripe webhook signature verification."""

    def test_stub_mode_parses_payload_directly(self):
        """Test that stub mode parses payload without signature verification."""
        from services.billing import webhooks
        webhooks.STUB_MODE = True

        payload = json.dumps({
            "type": "customer.subscription.created",
            "data": {"object": {"id": "sub_123"}},
        }).encode()

        event = verify_webhook_signature(payload, "")
        assert event["type"] == "customer.subscription.created"

    def test_invalid_json_raises_error(self):
        """Test that invalid JSON raises an error."""
        from services.billing import webhooks
        webhooks.STUB_MODE = True

        with pytest.raises(json.JSONDecodeError):
            verify_webhook_signature(b"invalid json", "")


class TestWebhookEventProcessing:
    """Test webhook event processing."""

    @pytest.mark.asyncio
    async def test_subscription_created_event(self):
        """Test processing subscription.created event."""
        from services.billing import service
        service.STUB_MODE = True

        event = {
            "type": "customer.subscription.created",
            "data": {
                "object": {
                    "id": "sub_123",
                    "customer": "cus_123",
                    "items": {
                        "data": [{
                            "price": {"product": "prod_starter"},
                        }],
                    },
                },
            },
        }

        result = await process_webhook_event(event)
        assert result["status"] == "processed"
        assert result["event_type"] == "customer.subscription.created"

    @pytest.mark.asyncio
    async def test_subscription_updated_event(self):
        """Test processing subscription.updated event."""
        from services.billing import service
        service.STUB_MODE = True

        event = {
            "type": "customer.subscription.updated",
            "data": {
                "object": {
                    "id": "sub_123",
                    "customer": "cus_123",
                    "items": {
                        "data": [{
                            "price": {"product": "prod_professional"},
                        }],
                    },
                },
            },
        }

        result = await process_webhook_event(event)
        assert result["status"] == "processed"
        assert result["event_type"] == "customer.subscription.updated"

    @pytest.mark.asyncio
    async def test_subscription_deleted_event(self):
        """Test processing subscription.deleted event."""
        from services.billing import service
        service.STUB_MODE = True

        event = {
            "type": "customer.subscription.deleted",
            "data": {
                "object": {
                    "id": "sub_123",
                    "customer": "cus_123",
                },
            },
        }

        result = await process_webhook_event(event)
        assert result["status"] == "processed"
        assert result["event_type"] == "customer.subscription.deleted"
        # Should downgrade to free tier
        assert result["result"]["plan_tier"] == "free"

    @pytest.mark.asyncio
    async def test_invoice_paid_event(self):
        """Test processing invoice.paid event."""
        event = {
            "type": "invoice.paid",
            "data": {
                "object": {
                    "subscription": "sub_123",
                    "customer": "cus_123",
                    "amount_paid": 2999,
                    "currency": "usd",
                },
            },
        }

        result = await process_webhook_event(event)
        assert result["status"] == "processed"
        assert result["result"]["status"] == "paid"
        assert result["result"]["amount_paid"] == 2999

    @pytest.mark.asyncio
    async def test_invoice_payment_failed_event(self):
        """Test processing invoice.payment_failed event."""
        event = {
            "type": "invoice.payment_failed",
            "data": {
                "object": {
                    "subscription": "sub_123",
                    "customer": "cus_123",
                    "amount_due": 2999,
                    "currency": "usd",
                    "next_payment_attempt": 1234567890,
                },
            },
        }

        result = await process_webhook_event(event)
        assert result["status"] == "processed"
        assert result["result"]["status"] == "failed"
        assert result["result"]["amount_due"] == 2999
        assert result["result"]["next_payment_attempt"] == 1234567890

    @pytest.mark.asyncio
    async def test_unhandled_event_type(self):
        """Test that unhandled event types are ignored."""
        event = {
            "type": "charge.succeeded",
            "data": {"object": {}},
        }

        result = await process_webhook_event(event)
        assert result["status"] == "ignored"
        assert result["event_type"] == "charge.succeeded"

    @pytest.mark.asyncio
    async def test_malformed_event_data(self):
        """Test handling of events with missing data."""
        event = {
            "type": "customer.subscription.created",
            "data": {
                "object": {
                    # Missing required fields
                },
            },
        }

        result = await process_webhook_event(event)
        # Should return error status for missing data
        assert result["status"] == "error"


class TestHandledEvents:
    """Test the list of handled event types."""

    def test_handled_events_list(self):
        """Test that all expected events are in the handled list."""
        expected_events = [
            "customer.subscription.created",
            "customer.subscription.updated",
            "customer.subscription.deleted",
            "invoice.paid",
            "invoice.payment_failed",
        ]

        for event in expected_events:
            assert event in HANDLED_EVENTS, f"{event} should be in HANDLED_EVENTS"

    def test_handled_events_count(self):
        """Test that we handle the expected number of events."""
        assert len(HANDLED_EVENTS) == 5
