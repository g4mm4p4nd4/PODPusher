from datetime import datetime
from typing import Any

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from sqlmodel import select

from ..common.auth import optional_user_id
from ..common.database import get_session
from ..common.observability import register_observability
from ..control_center.service import get_settings_dashboard
from ..models import BrandProfile, TeamMember, UsageLedger, User

app = FastAPI()
register_observability(app, service_name="settings")


class LocalizationUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    default_language: str = "en"
    marketplace_regions: list[str] = Field(default_factory=lambda: ["US"])
    currency: str = "USD"
    date_format: str = "MMM DD, YYYY"
    localized_niche_targeting: bool = True
    primary_targeting_region: str = "US"
    timezone: str = "UTC"


class BrandProfilePayload(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = "New Brand Profile"
    tone: str = "Humorous, Positive"
    audience: str = "Adults, Parents"
    interests: list[str] = Field(default_factory=list)
    banned_topics: list[str] = Field(default_factory=list)
    preferred_products: list[str] = Field(default_factory=list)
    region: str = "US"
    language: str = "en"
    active: bool = False


class TeamInvitePayload(BaseModel):
    model_config = ConfigDict(extra="forbid")
    email: str
    name: str | None = None
    role: str = "viewer"
    permissions: list[str] = Field(default_factory=list)


class TeamRolePayload(BaseModel):
    model_config = ConfigDict(extra="forbid")
    role: str
    permissions: list[str] | None = None
    status: str | None = None


class IntegrationConfigurePayload(BaseModel):
    model_config = ConfigDict(extra="forbid")
    action: str = "configure"
    metadata: dict[str, Any] | None = None


def _user_id(value: int | None) -> int:
    return value or 1


def _provenance(source: str, estimated: bool = False) -> dict[str, Any]:
    return {
        "source": source,
        "is_estimated": estimated,
        "updated_at": datetime.utcnow().isoformat(),
        "confidence": 0.9 if not estimated else 0.72,
    }


def _profile_to_dict(profile: BrandProfile) -> dict[str, Any]:
    return {
        "id": profile.id,
        "name": profile.name,
        "tone": profile.tone,
        "audience": profile.audience,
        "interests": profile.interests,
        "banned_topics": profile.banned_topics,
        "preferred_products": profile.preferred_products,
        "region": profile.region,
        "language": profile.language,
        "active": profile.active,
        "updated_at": profile.updated_at.isoformat(),
        "provenance": _provenance("brandprofile_table"),
    }


@app.get("/dashboard")
async def dashboard(user_id: int | None = Depends(optional_user_id)):
    return await get_settings_dashboard(user_id)


@app.patch("/localization")
async def update_localization(
    payload: LocalizationUpdate,
    user_id: int | None = Depends(optional_user_id),
):
    resolved_user_id = _user_id(user_id)
    async with get_session() as session:
        user = await session.get(User, resolved_user_id)
        if not user:
            user = User(id=resolved_user_id)
        user.preferred_language = payload.default_language
        user.preferred_currency = payload.currency
        user.timezone = payload.timezone
        session.add(user)

        profile = (
            await session.exec(
                select(BrandProfile)
                .where(BrandProfile.user_id == resolved_user_id)
                .where(BrandProfile.active == True)  # noqa: E712
                .order_by(BrandProfile.updated_at.desc())
            )
        ).first()
        if not profile:
            profile = BrandProfile(user_id=resolved_user_id, active=True)
        profile.language = payload.default_language
        profile.region = payload.primary_targeting_region
        profile.updated_at = datetime.utcnow()
        session.add(profile)
        await session.commit()
        await session.refresh(user)
        await session.refresh(profile)

    return {
        "saved": True,
        "localization": {
            "default_language": user.preferred_language,
            "marketplace_regions": payload.marketplace_regions,
            "currency": user.preferred_currency,
            "date_format": payload.date_format,
            "localized_niche_targeting": payload.localized_niche_targeting,
            "primary_targeting_region": profile.region,
            "timezone": user.timezone,
        },
        "demo_state": {
            "date_format_storage": "stored in response only until a dedicated settings table is added",
        },
        "provenance": _provenance("user_and_brandprofile_tables"),
    }


@app.post("/brand-profiles")
async def create_brand_profile(
    payload: BrandProfilePayload,
    user_id: int | None = Depends(optional_user_id),
):
    resolved_user_id = _user_id(user_id)
    async with get_session() as session:
        if payload.active:
            existing = (
                await session.exec(
                    select(BrandProfile).where(
                        BrandProfile.user_id == resolved_user_id
                    )
                )
            ).all()
            for profile in existing:
                profile.active = False
                session.add(profile)
        record = BrandProfile(user_id=resolved_user_id, **payload.model_dump())
        record.updated_at = datetime.utcnow()
        session.add(record)
        await session.commit()
        await session.refresh(record)
    return {"saved": True, "profile": _profile_to_dict(record)}


@app.patch("/brand-profiles/{profile_id}")
async def update_brand_profile(
    profile_id: int,
    payload: BrandProfilePayload,
    user_id: int | None = Depends(optional_user_id),
):
    resolved_user_id = _user_id(user_id)
    async with get_session() as session:
        record = await session.get(BrandProfile, profile_id)
        if not record or record.user_id != resolved_user_id:
            raise HTTPException(status_code=404, detail="Brand profile not found")
        for field, value in payload.model_dump().items():
            setattr(record, field, value)
        record.updated_at = datetime.utcnow()
        session.add(record)
        await session.commit()
        await session.refresh(record)
    return {"saved": True, "profile": _profile_to_dict(record)}


@app.put("/brand-profiles/{profile_id}/default")
async def set_default_brand_profile(
    profile_id: int,
    user_id: int | None = Depends(optional_user_id),
):
    resolved_user_id = _user_id(user_id)
    async with get_session() as session:
        profiles = (
            await session.exec(
                select(BrandProfile).where(BrandProfile.user_id == resolved_user_id)
            )
        ).all()
        target = next((item for item in profiles if item.id == profile_id), None)
        if not target:
            raise HTTPException(status_code=404, detail="Brand profile not found")
        for profile in profiles:
            profile.active = profile.id == profile_id
            profile.updated_at = datetime.utcnow()
            session.add(profile)
        await session.commit()
        await session.refresh(target)
    return {"saved": True, "profile": _profile_to_dict(target)}


@app.post("/users/invite")
async def invite_user(
    payload: TeamInvitePayload,
    user_id: int | None = Depends(optional_user_id),
):
    resolved_user_id = _user_id(user_id)
    name = payload.name or payload.email.split("@")[0].replace(".", " ").title()
    permissions = payload.permissions or ["Listings", "Analytics"]
    async with get_session() as session:
        existing = (
            await session.exec(
                select(TeamMember)
                .where(TeamMember.user_id == resolved_user_id)
                .where(TeamMember.email == payload.email)
            )
        ).first()
        record = existing or TeamMember(user_id=resolved_user_id, email=payload.email)
        record.name = name
        record.role = payload.role
        record.permissions = permissions
        record.status = "invited"
        record.last_active_at = datetime.utcnow()
        session.add(record)
        await session.commit()
        await session.refresh(record)
    return {
        "sent": True,
        "member": {
            "id": record.id,
            "name": record.name,
            "email": record.email,
            "role": record.role,
            "permissions": record.permissions,
            "status": record.status,
            "last_active_at": record.last_active_at.isoformat(),
        },
        "provenance": _provenance("teammember_table"),
    }


@app.patch("/users/{member_id}/role")
async def update_user_role(
    member_id: int,
    payload: TeamRolePayload,
    user_id: int | None = Depends(optional_user_id),
):
    resolved_user_id = _user_id(user_id)
    async with get_session() as session:
        record = await session.get(TeamMember, member_id)
        if not record or record.user_id != resolved_user_id:
            raise HTTPException(status_code=404, detail="Team member not found")
        record.role = payload.role
        if payload.permissions is not None:
            record.permissions = payload.permissions
        if payload.status is not None:
            record.status = payload.status
        record.last_active_at = datetime.utcnow()
        session.add(record)
        await session.commit()
        await session.refresh(record)
    return {
        "saved": True,
        "member": {
            "id": record.id,
            "name": record.name,
            "email": record.email,
            "role": record.role,
            "permissions": record.permissions,
            "status": record.status,
            "last_active_at": record.last_active_at.isoformat(),
        },
        "provenance": _provenance("teammember_table"),
    }


@app.get("/usage-ledger")
async def usage_ledger(user_id: int | None = Depends(optional_user_id)):
    resolved_user_id = _user_id(user_id)
    async with get_session() as session:
        rows = (
            await session.exec(
                select(UsageLedger)
                .where(UsageLedger.user_id == resolved_user_id)
                .order_by(UsageLedger.created_at.desc())
                .limit(50)
            )
        ).all()
    if not rows:
        return {
            "items": [
                {
                    "resource_type": "image_generation",
                    "quantity": 17500,
                    "source": "demo_usage_estimate",
                    "created_at": datetime.utcnow().isoformat(),
                    "provenance": _provenance("demo_usage_estimate", estimated=True),
                }
            ],
            "demo_state": True,
            "provenance": _provenance("usageledger_table", estimated=True),
        }
    return {
        "items": [
            {
                "id": item.id,
                "resource_type": item.resource_type,
                "quantity": item.quantity,
                "source": item.source,
                "created_at": item.created_at.isoformat(),
                "provenance": _provenance(item.source),
            }
            for item in rows
        ],
        "demo_state": False,
        "provenance": _provenance("usageledger_table"),
    }


@app.post("/integrations/{provider}/configure")
async def configure_integration(
    provider: str,
    payload: IntegrationConfigurePayload,
    user_id: int | None = Depends(optional_user_id),
):
    return {
        "provider": provider,
        "status": "credentials_missing",
        "action": payload.action,
        "configured": False,
        "is_demo": True,
        "message": f"{provider.title()} credentials are not configured in local mode; dashboard data remains available with fallback status.",
        "user_id": _user_id(user_id),
        "provenance": _provenance("integration_placeholder", estimated=True),
    }
