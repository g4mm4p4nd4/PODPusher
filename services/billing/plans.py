"""Subscription plan definitions."""

from enum import Enum
from typing import NamedTuple


class PlanTier(str, Enum):
    """Available subscription tiers."""
    FREE = "free"
    STARTER = "starter"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"


class PlanLimits(NamedTuple):
    """Resource limits for a plan tier."""
    monthly_listings: int
    monthly_images: int
    monthly_ideas: int
    team_seats: int
    priority_support: bool


# Plan configurations matching Stripe product IDs
PLAN_CONFIGS: dict[PlanTier, PlanLimits] = {
    PlanTier.FREE: PlanLimits(
        monthly_listings=10,
        monthly_images=20,
        monthly_ideas=50,
        team_seats=1,
        priority_support=False,
    ),
    PlanTier.STARTER: PlanLimits(
        monthly_listings=50,
        monthly_images=100,
        monthly_ideas=200,
        team_seats=1,
        priority_support=False,
    ),
    PlanTier.PROFESSIONAL: PlanLimits(
        monthly_listings=200,
        monthly_images=500,
        monthly_ideas=1000,
        team_seats=3,
        priority_support=True,
    ),
    PlanTier.ENTERPRISE: PlanLimits(
        monthly_listings=1000,
        monthly_images=2500,
        monthly_ideas=5000,
        team_seats=10,
        priority_support=True,
    ),
}


def get_plan_limits(tier: PlanTier) -> PlanLimits:
    """Get resource limits for a plan tier."""
    return PLAN_CONFIGS.get(tier, PLAN_CONFIGS[PlanTier.FREE])


def get_tier_from_stripe_product(product_id: str) -> PlanTier:
    """Map a Stripe product ID to a plan tier.

    In production, these would be configured via environment variables.
    """
    import os

    mappings = {
        os.getenv("STRIPE_PRODUCT_STARTER", "prod_starter"): PlanTier.STARTER,
        os.getenv("STRIPE_PRODUCT_PROFESSIONAL", "prod_professional"): PlanTier.PROFESSIONAL,
        os.getenv("STRIPE_PRODUCT_ENTERPRISE", "prod_enterprise"): PlanTier.ENTERPRISE,
    }

    return mappings.get(product_id, PlanTier.FREE)
