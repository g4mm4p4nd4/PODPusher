"""Stripe webhook handling."""

from __future__ import annotations

import os
import logging
from typing import Optional

import stripe

from .service import (
    handle_subscription_created,
    handle_subscription_updated,
    handle_subscription_deleted,
    handle_invoice_paid,
    handle_invoice_payment_failed,
    BillingError,
)

logger = logging.getLogger(__name__)

WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")
STUB_MODE = os.getenv("BILLING_STUB_MODE", "false").lower() == "true" or not WEBHOOK_SECRET


def verify_webhook_signature(payload: bytes, sig_header: str) -> dict:
    """Verify the Stripe webhook signature and return the event.

    Raises ValueError if signature verification fails.
    """
    if STUB_MODE:
        # In stub mode, parse the payload directly
        import json
        return json.loads(payload)

    if not WEBHOOK_SECRET:
        raise ValueError("Webhook secret not configured")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, WEBHOOK_SECRET
        )
        return event
    except stripe.error.SignatureVerificationError as e:
        logger.warning(f"Webhook signature verification failed: {e}")
        raise ValueError("Invalid signature")
    except ValueError as e:
        logger.warning(f"Invalid webhook payload: {e}")
        raise ValueError("Invalid payload")


async def process_webhook_event(event: dict) -> dict:
    """Process a Stripe webhook event.

    Returns the result of handling the event.
    """
    event_type = event.get("type", "")
    data_object = event.get("data", {}).get("object", {})

    logger.info(f"Processing webhook event: {event_type}")

    handlers = {
        "customer.subscription.created": handle_subscription_created,
        "customer.subscription.updated": handle_subscription_updated,
        "customer.subscription.deleted": handle_subscription_deleted,
        "invoice.paid": handle_invoice_paid,
        "invoice.payment_failed": handle_invoice_payment_failed,
    }

    handler = handlers.get(event_type)
    if not handler:
        logger.debug(f"No handler for event type: {event_type}")
        return {"status": "ignored", "event_type": event_type}

    try:
        result = await handler(data_object)
        logger.info(f"Successfully processed {event_type}: {result}")
        return {
            "status": "processed",
            "event_type": event_type,
            "result": result,
        }
    except BillingError as e:
        logger.error(f"Billing error processing {event_type}: {e}")
        return {
            "status": "error",
            "event_type": event_type,
            "error": str(e),
        }
    except Exception as e:
        logger.exception(f"Unexpected error processing {event_type}: {e}")
        return {
            "status": "error",
            "event_type": event_type,
            "error": "Internal error",
        }


# Event types we handle
HANDLED_EVENTS = [
    "customer.subscription.created",
    "customer.subscription.updated",
    "customer.subscription.deleted",
    "invoice.paid",
    "invoice.payment_failed",
]
