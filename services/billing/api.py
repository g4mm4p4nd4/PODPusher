"""Billing service FastAPI endpoints."""

from __future__ import annotations

import logging
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException, Header, Request
from pydantic import BaseModel

from ..common.auth import require_user_id
from .plans import PlanTier, get_plan_limits
from .service import (
    BillingError,
    STUB_MODE,
    get_or_create_customer,
    create_portal_session,
    get_subscription_for_customer,
    get_user_plan_tier,
)
from .webhooks import verify_webhook_signature, process_webhook_event

logger = logging.getLogger(__name__)

app = FastAPI()


class SubscriptionResponse(BaseModel):
    """Response model for subscription status."""

    has_subscription: bool
    plan_tier: str
    subscription_id: Optional[str] = None
    status: Optional[str] = None
    current_period_end: Optional[int] = None
    limits: dict


class PortalResponse(BaseModel):
    """Response model for customer portal URL."""

    portal_url: str


class QuotaResponse(BaseModel):
    """Response model for user quotas."""

    plan_tier: str
    monthly_listings: int
    monthly_images: int
    monthly_ideas: int
    team_seats: int
    priority_support: bool


class WebhookResponse(BaseModel):
    """Response model for webhook processing."""

    status: str
    event_type: Optional[str] = None
    message: Optional[str] = None


@app.get("/subscription", response_model=SubscriptionResponse)
async def get_subscription(user_id: int = Depends(require_user_id)):
    """Get the current user's subscription status."""
    try:
        plan_tier = await get_user_plan_tier(user_id)
        limits = get_plan_limits(plan_tier)

        # Build response with limits
        response = SubscriptionResponse(
            has_subscription=plan_tier != PlanTier.FREE,
            plan_tier=plan_tier.value,
            limits={
                "monthly_listings": limits.monthly_listings,
                "monthly_images": limits.monthly_images,
                "monthly_ideas": limits.monthly_ideas,
                "team_seats": limits.team_seats,
                "priority_support": limits.priority_support,
            },
        )

        # If not on free tier, try to get subscription details
        if plan_tier != PlanTier.FREE and not STUB_MODE:
            # In a full implementation, we would look up cached subscription data
            pass

        return response

    except BillingError as e:
        logger.error(f"Failed to get subscription for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve subscription")


@app.get("/quota", response_model=QuotaResponse)
async def get_quota(user_id: int = Depends(require_user_id)):
    """Get the current user's quota limits based on their plan."""
    try:
        plan_tier = await get_user_plan_tier(user_id)
        limits = get_plan_limits(plan_tier)

        return QuotaResponse(
            plan_tier=plan_tier.value,
            monthly_listings=limits.monthly_listings,
            monthly_images=limits.monthly_images,
            monthly_ideas=limits.monthly_ideas,
            team_seats=limits.team_seats,
            priority_support=limits.priority_support,
        )

    except BillingError as e:
        logger.error(f"Failed to get quota for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve quota")


@app.post("/portal", response_model=PortalResponse)
async def create_customer_portal(
    return_url: str = "/settings",
    user_id: int = Depends(require_user_id),
):
    """Create a Stripe Customer Portal session for subscription management."""
    try:
        # Get user email from somewhere - placeholder for now
        # In a full implementation, we would look up the user's email
        user_email = f"user-{user_id}@example.com"

        customer_id = await get_or_create_customer(user_id, user_email)
        portal_url = await create_portal_session(customer_id, return_url)

        return PortalResponse(portal_url=portal_url)

    except BillingError as e:
        logger.error(f"Failed to create portal for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to create billing portal")


@app.post("/webhooks", response_model=WebhookResponse)
async def stripe_webhook(
    request: Request,
    stripe_signature: Optional[str] = Header(None, alias="Stripe-Signature"),
):
    """Handle Stripe webhook events.

    This endpoint receives webhook events from Stripe and processes them.
    It verifies the webhook signature to ensure authenticity.
    """
    try:
        payload = await request.body()

        # Verify signature (or parse directly in stub mode)
        try:
            event = verify_webhook_signature(
                payload,
                stripe_signature or "",
            )
        except ValueError as e:
            logger.warning(f"Webhook signature verification failed: {e}")
            raise HTTPException(status_code=400, detail="Invalid signature")

        # Process the event
        result = await process_webhook_event(event)

        return WebhookResponse(
            status=result.get("status", "processed"),
            event_type=result.get("event_type"),
            message=result.get("error"),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Unexpected error processing webhook: {e}")
        raise HTTPException(status_code=500, detail="Webhook processing failed")


@app.get("/plans")
async def list_plans():
    """List available subscription plans and their limits."""
    plans = []
    for tier in PlanTier:
        limits = get_plan_limits(tier)
        plans.append({
            "tier": tier.value,
            "name": tier.name.replace("_", " ").title(),
            "limits": {
                "monthly_listings": limits.monthly_listings,
                "monthly_images": limits.monthly_images,
                "monthly_ideas": limits.monthly_ideas,
                "team_seats": limits.team_seats,
                "priority_support": limits.priority_support,
            },
        })
    return {"plans": plans}
