"""Billing service business logic."""

from __future__ import annotations

import os
from datetime import datetime
from typing import Optional

import stripe

from .plans import PlanTier, get_plan_limits, get_tier_from_stripe_product

# Initialize Stripe
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

# Stub mode for development without Stripe credentials
STUB_MODE = os.getenv("BILLING_STUB_MODE", "false").lower() == "true" or not stripe.api_key


class BillingError(Exception):
    """Billing-related error."""
    pass


async def get_or_create_customer(user_id: int, email: str) -> str:
    """Get or create a Stripe customer for a user.

    Returns the Stripe customer ID.
    """
    if STUB_MODE:
        return f"cus_stub_{user_id}"

    # In a real implementation, we would store the mapping in the database
    # For now, search by metadata
    try:
        customers = stripe.Customer.search(
            query=f"metadata['user_id']:'{user_id}'"
        )
        if customers.data:
            return customers.data[0].id

        # Create new customer
        customer = stripe.Customer.create(
            email=email,
            metadata={"user_id": str(user_id)},
        )
        return customer.id
    except stripe.error.StripeError as e:
        raise BillingError(f"Failed to get/create customer: {e}")


async def create_portal_session(customer_id: str, return_url: str) -> str:
    """Create a Stripe Customer Portal session.

    Returns the portal URL.
    """
    if STUB_MODE:
        return f"{return_url}?stub_portal=true"

    try:
        session = stripe.billing_portal.Session.create(
            customer=customer_id,
            return_url=return_url,
        )
        return session.url
    except stripe.error.StripeError as e:
        raise BillingError(f"Failed to create portal session: {e}")


async def get_subscription_for_customer(customer_id: str) -> Optional[dict]:
    """Get the active subscription for a customer."""
    if STUB_MODE:
        return {
            "id": "sub_stub",
            "status": "active",
            "current_period_end": int(datetime.now().timestamp()) + 86400 * 30,
            "plan_tier": PlanTier.STARTER.value,
        }

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
        plan_tier = get_tier_from_stripe_product(product_id) if product_id else PlanTier.FREE

        return {
            "id": sub.id,
            "status": sub.status,
            "current_period_end": sub.current_period_end,
            "plan_tier": plan_tier.value,
        }
    except stripe.error.StripeError as e:
        raise BillingError(f"Failed to get subscription: {e}")


async def get_user_plan_tier(user_id: int) -> PlanTier:
    """Get the plan tier for a user.

    In a full implementation, this would query the database for the cached
    subscription info rather than calling Stripe directly.
    """
    if STUB_MODE:
        return PlanTier.STARTER

    # This is a simplified version - in production, we would query our database
    # which is updated by webhooks
    try:
        # Search for customer by user_id metadata
        customers = stripe.Customer.search(
            query=f"metadata['user_id']:'{user_id}'"
        )
        if not customers.data:
            return PlanTier.FREE

        customer_id = customers.data[0].id
        subscription = await get_subscription_for_customer(customer_id)

        if subscription and subscription.get("status") == "active":
            return PlanTier(subscription["plan_tier"])

        return PlanTier.FREE
    except Exception:
        # Default to free tier on any error
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

    # Get user_id from customer metadata
    if STUB_MODE:
        user_id = 1
    else:
        try:
            customer = stripe.Customer.retrieve(customer_id)
            user_id = int(customer.metadata.get("user_id", 0))
        except stripe.error.StripeError as e:
            raise BillingError(f"Failed to retrieve customer: {e}")

    if not user_id:
        raise BillingError("No user_id found in customer metadata")

    return await update_user_quotas_from_subscription(user_id, subscription_id, product_id)


async def handle_subscription_updated(subscription: dict) -> dict:
    """Handle a subscription being updated (upgrade/downgrade)."""
    return await handle_subscription_created(subscription)


async def handle_subscription_deleted(subscription: dict) -> dict:
    """Handle a subscription being cancelled."""
    customer_id = subscription.get("customer")

    if STUB_MODE:
        user_id = 1
    else:
        try:
            customer = stripe.Customer.retrieve(customer_id)
            user_id = int(customer.metadata.get("user_id", 0))
        except stripe.error.StripeError as e:
            raise BillingError(f"Failed to retrieve customer: {e}")

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
