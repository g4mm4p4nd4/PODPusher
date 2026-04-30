"""Billing service business logic."""

from __future__ import annotations

import os
import logging
from datetime import datetime
from typing import Optional
import re

try:
    import stripe
except ModuleNotFoundError:  # pragma: no cover - exercised in minimal local envs

    class _StripeFallbackError(Exception):
        pass

    class _StripeFallbackInvalidRequestError(_StripeFallbackError):
        pass

    class _StripeFallbackCustomer:
        @staticmethod
        def search(*_args, **_kwargs):
            raise _StripeFallbackError("Stripe SDK is not installed")

        @staticmethod
        def list(*_args, **_kwargs):
            raise _StripeFallbackError("Stripe SDK is not installed")

        @staticmethod
        def create(*_args, **_kwargs):
            raise _StripeFallbackError("Stripe SDK is not installed")

        @staticmethod
        def retrieve(*_args, **_kwargs):
            raise _StripeFallbackError("Stripe SDK is not installed")

    class _StripeFallbackSubscription:
        @staticmethod
        def list(*_args, **_kwargs):
            raise _StripeFallbackError("Stripe SDK is not installed")

    class _StripeFallbackPortal:
        class Session:
            @staticmethod
            def create(*_args, **_kwargs):
                raise _StripeFallbackError("Stripe SDK is not installed")

    class _StripeFallback:
        api_key = None
        Customer = _StripeFallbackCustomer
        Subscription = _StripeFallbackSubscription
        billing_portal = _StripeFallbackPortal

        class error:
            StripeError = _StripeFallbackError
            InvalidRequestError = _StripeFallbackInvalidRequestError

    stripe = _StripeFallback()

from .plans import PlanTier, get_plan_limits, get_tier_from_stripe_product

logger = logging.getLogger(__name__)

# Initialize Stripe when the optional SDK is available.
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

# Stub mode for development without Stripe credentials
STUB_MODE = (
    os.getenv("BILLING_STUB_MODE", "false").lower() == "true" or not stripe.api_key
)


class BillingError(Exception):
    """Billing-related error."""

    pass


def _format_stripe_error(prefix: str, exc: Exception) -> str:
    detail = getattr(exc, "user_message", None) or str(exc) or exc.__class__.__name__
    return f"{prefix}: {exc.__class__.__name__}: {detail}"


def _coerce_user_id(raw_user_id: object) -> int:
    try:
        user_id = int(raw_user_id)
    except (TypeError, ValueError):
        return 0
    return user_id if user_id > 0 else 0


def _user_id_from_metadata(payload: dict | None) -> int:
    if not isinstance(payload, dict):
        return 0
    metadata = payload.get("metadata")
    if not isinstance(metadata, dict):
        return 0
    return _coerce_user_id(metadata.get("user_id"))


def _user_id_from_stub_customer(customer_id: str | None) -> int:
    if not customer_id:
        return 0
    match = re.fullmatch(r"cus_stub_(\d+)", str(customer_id))
    if not match:
        return 0
    return _coerce_user_id(match.group(1))


def _resolve_user_id_for_subscription_event(
    payload: dict, customer_id: str | None
) -> int:
    user_id = _user_id_from_metadata(payload)
    if user_id:
        return user_id

    if STUB_MODE:
        return _user_id_from_stub_customer(customer_id)

    try:
        customer = stripe.Customer.retrieve(customer_id)
    except stripe.error.StripeError as exc:
        raise BillingError(
            _format_stripe_error("Failed to retrieve customer", exc)
        ) from exc

    return _user_id_from_metadata({"metadata": getattr(customer, "metadata", {})})


async def get_or_create_customer(user_id: int, email: str) -> str:
    """Get or create a Stripe customer for a user.

    Returns the Stripe customer ID.
    """
    if STUB_MODE:
        raise BillingError(
            "Stripe billing is not configured; set STRIPE_SECRET_KEY and complete billing integration before creating customers"
        )

    try:
        # Preferred path: metadata search by internal user ID.
        customers = stripe.Customer.search(query=f"metadata['user_id']:'{user_id}'")
        if customers.data:
            return customers.data[0].id
    except stripe.error.InvalidRequestError as e:
        # Fallback for Stripe accounts where search is not enabled.
        logger.warning(
            "Stripe customer search unavailable; falling back to list: %s", e
        )
        try:
            listed_customers = stripe.Customer.list(email=email, limit=10)
        except stripe.error.StripeError as list_exc:
            raise BillingError(
                _format_stripe_error("Failed to lookup customer", list_exc)
            ) from list_exc

        for customer in listed_customers.data:
            metadata = getattr(customer, "metadata", {}) or {}
            if str(metadata.get("user_id", "")) == str(user_id):
                return customer.id

        if len(listed_customers.data) == 1:
            return listed_customers.data[0].id
    except stripe.error.StripeError as e:
        raise BillingError(_format_stripe_error("Failed to lookup customer", e)) from e

    try:
        # Create new customer
        customer = stripe.Customer.create(
            email=email,
            metadata={"user_id": str(user_id)},
        )
        return customer.id
    except stripe.error.StripeError as e:
        raise BillingError(_format_stripe_error("Failed to create customer", e)) from e


async def create_portal_session(customer_id: str, return_url: str) -> str:
    """Create a Stripe Customer Portal session.

    Returns the portal URL.
    """
    if STUB_MODE:
        raise BillingError(
            "Stripe billing portal is not configured; set STRIPE_SECRET_KEY and complete billing integration before opening the portal"
        )

    try:
        session = stripe.billing_portal.Session.create(
            customer=customer_id,
            return_url=return_url,
        )
        return session.url
    except stripe.error.StripeError as e:
        raise BillingError(
            _format_stripe_error("Failed to create portal session", e)
        ) from e


async def get_subscription_for_customer(customer_id: str) -> Optional[dict]:
    """Get the active subscription for a customer."""
    if STUB_MODE:
        return None

    try:
        subscriptions = stripe.Subscription.list(
            customer=customer_id,
            status="active",
            limit=1,
        )
        if not subscriptions.data:
            return None

        sub = subscriptions.data[0]
        product_id = sub.items.data[0].price.product if sub.items.data else None
        plan_tier = (
            get_tier_from_stripe_product(product_id) if product_id else PlanTier.FREE
        )

        return {
            "id": sub.id,
            "status": sub.status,
            "current_period_end": sub.current_period_end,
            "plan_tier": plan_tier.value,
        }
    except stripe.error.StripeError as e:
        raise BillingError(_format_stripe_error("Failed to get subscription", e)) from e


async def get_user_plan_tier(user_id: int) -> PlanTier:
    """Get the plan tier for a user.

    In a full implementation, this would query the database for the cached
    subscription info rather than calling Stripe directly.
    """
    if STUB_MODE:
        return PlanTier.FREE

    # This is a simplified version - in production, we would query our database
    # which is updated by webhooks
    try:
        # Search for customer by user_id metadata
        customers = stripe.Customer.search(query=f"metadata['user_id']:'{user_id}'")
        if not customers.data:
            return PlanTier.FREE

        customer_id = customers.data[0].id
        subscription = await get_subscription_for_customer(customer_id)

        if subscription and subscription.get("status") == "active":
            return PlanTier(subscription["plan_tier"])

        return PlanTier.FREE
    except stripe.error.StripeError as exc:
        logger.warning(
            "Falling back to free tier for user %s due to Stripe error: %s",
            user_id,
            exc,
        )
        return PlanTier.FREE
    except Exception:
        # Default to free tier on any unexpected error.
        return PlanTier.FREE


async def update_user_quotas_from_subscription(
    user_id: int,
    subscription_id: str,
    product_id: str,
) -> dict:
    """Update user quotas based on their subscription.

    This is called by webhook handlers when subscription changes.
    Returns the updated quota limits.
    """
    plan_tier = get_tier_from_stripe_product(product_id)
    limits = get_plan_limits(plan_tier)

    # In a full implementation, this would update the database
    # For now, return the limits that should be applied
    return {
        "plan_tier": plan_tier.value,
        "monthly_listings": limits.monthly_listings,
        "monthly_images": limits.monthly_images,
        "monthly_ideas": limits.monthly_ideas,
        "team_seats": limits.team_seats,
        "priority_support": limits.priority_support,
    }


async def handle_subscription_created(subscription: dict) -> dict:
    """Handle a new subscription being created."""
    customer_id = subscription.get("customer")
    subscription_id = subscription.get("id")
    items = subscription.get("items", {}).get("data", [])
    product_id = items[0].get("price", {}).get("product") if items else None

    if not customer_id or not product_id:
        raise BillingError("Missing customer or product in subscription")

    user_id = _resolve_user_id_for_subscription_event(subscription, customer_id)

    if not user_id:
        raise BillingError("No user_id found in customer metadata")

    return await update_user_quotas_from_subscription(
        user_id, subscription_id, product_id
    )


async def handle_subscription_updated(subscription: dict) -> dict:
    """Handle a subscription being updated (upgrade/downgrade)."""
    return await handle_subscription_created(subscription)


async def handle_subscription_deleted(subscription: dict) -> dict:
    """Handle a subscription being cancelled."""
    customer_id = subscription.get("customer")
    if not customer_id:
        raise BillingError("Missing customer in subscription")

    user_id = _resolve_user_id_for_subscription_event(subscription, customer_id)

    if not user_id:
        raise BillingError("No user_id found in customer metadata")

    # Downgrade to free tier
    limits = get_plan_limits(PlanTier.FREE)
    return {
        "plan_tier": PlanTier.FREE.value,
        "monthly_listings": limits.monthly_listings,
        "monthly_images": limits.monthly_images,
        "monthly_ideas": limits.monthly_ideas,
        "team_seats": limits.team_seats,
        "priority_support": limits.priority_support,
    }


async def handle_invoice_paid(invoice: dict) -> dict:
    """Handle a successful invoice payment."""
    subscription_id = invoice.get("subscription")
    customer_id = invoice.get("customer")

    return {
        "status": "paid",
        "subscription_id": subscription_id,
        "customer_id": customer_id,
        "amount_paid": invoice.get("amount_paid", 0),
        "currency": invoice.get("currency", "usd"),
    }


async def handle_invoice_payment_failed(invoice: dict) -> dict:
    """Handle a failed invoice payment."""
    subscription_id = invoice.get("subscription")
    customer_id = invoice.get("customer")

    # In a full implementation, we would:
    # 1. Send notification to user
    # 2. Maybe downgrade access after grace period
    # 3. Log the failure

    return {
        "status": "failed",
        "subscription_id": subscription_id,
        "customer_id": customer_id,
        "amount_due": invoice.get("amount_due", 0),
        "currency": invoice.get("currency", "usd"),
        "next_payment_attempt": invoice.get("next_payment_attempt"),
    }
