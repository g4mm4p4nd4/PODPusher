from __future__ import annotations

import os
from typing import Dict, List, Optional

import httpx
from sqlmodel import select

from packages.integrations import gemini
from packages.integrations.etsy import get_etsy_client
from packages.integrations.printify import (
    create_product as printify_create_product,
    get_printify_client,
)
from services.auth import service as auth_service
from ..common.database import get_session
from ..models import OAuthCredential, OAuthProvider


class IntegrationServiceError(Exception):
    """Base error for integration operations."""

    status_code = 500


class IntegrationCredentialError(IntegrationServiceError):
    status_code = 424


class IntegrationPayloadError(IntegrationServiceError):
    status_code = 422


class IntegrationUpstreamError(IntegrationServiceError):
    status_code = 502


async def load_oauth_credentials(
    user_id: Optional[int],
    provider: OAuthProvider,
) -> Optional[Dict[str, Optional[str]]]:
    if user_id is None:
        return None
    async with get_session() as session:
        result = await session.exec(
            select(OAuthCredential).where(
                (OAuthCredential.user_id == user_id)
                & (OAuthCredential.provider == provider)
            )
        )
        credential = result.first()
        if credential is None:
            return None
        credential = await auth_service.ensure_credential_fresh(session, credential)
        return {
            "access_token": credential.access_token,
            "refresh_token": credential.refresh_token,
            "expires_at": credential.expires_at.isoformat()
            if credential.expires_at
            else None,
            "account_id": credential.account_id,
            "account_name": credential.account_name,
        }


def _ensure_live_credential(
    provider: OAuthProvider,
    credential: Optional[Dict[str, Optional[str]]],
) -> Dict[str, Optional[str]]:
    if not credential:
        raise IntegrationCredentialError(
            f"OAuth credentials for {provider.value} are required"
        )
    if not credential.get("access_token"):
        raise IntegrationCredentialError(
            f"{provider.value} credential missing access token"
        )
    required_shop_env = "PRINTIFY_SHOP_ID" if provider == OAuthProvider.PRINTIFY else "ETSY_SHOP_ID"
    if not credential.get("account_id") and not os.getenv(required_shop_env):
        raise IntegrationCredentialError(
            f"{provider.value} credential missing account ID (or {required_shop_env})"
        )
    return credential


def create_sku(
    products: List[dict],
    credential: Optional[Dict[str, Optional[str]]] = None,
    require_live: bool = False,
) -> List[dict]:
    if require_live:
        credential = _ensure_live_credential(OAuthProvider.PRINTIFY, credential)
    client = get_printify_client(credential)
    try:
        created = client(products)
    except ValueError as exc:
        raise IntegrationPayloadError(str(exc)) from exc
    except RuntimeError as exc:
        raise IntegrationUpstreamError(str(exc)) from exc
    except httpx.HTTPError as exc:
        raise IntegrationUpstreamError("Printify request failed") from exc
    if require_live:
        for item in created:
            sku = str(item.get("sku", "")).strip()
            if not sku or sku.startswith("stub-sku-"):
                raise IntegrationCredentialError(
                    "Printify live credentials are not configured"
                )
    return created


def create_printify_product(
    idea_id: str,
    image_ids: List[str],
    blueprint_id: str,
    variants: List[str],
    credential: Optional[Dict[str, Optional[str]]] = None,
    require_live: bool = False,
) -> dict:
    if require_live:
        credential = _ensure_live_credential(OAuthProvider.PRINTIFY, credential)
    mockups = [gemini.generate_mockup(f"{blueprint_id} variant {variant}") for variant in variants]
    try:
        product = printify_create_product(
            idea_id,
            image_ids,
            blueprint_id,
            variants,
            mockups,
            credential=credential,
        )
    except ValueError as exc:
        raise IntegrationPayloadError(str(exc)) from exc
    except RuntimeError as exc:
        raise IntegrationUpstreamError(str(exc)) from exc
    except httpx.HTTPError as exc:
        raise IntegrationUpstreamError("Printify product request failed") from exc
    if require_live:
        product_id = str(product.get("product_id", "")).strip()
        if not product_id or product_id.startswith("stub-"):
            raise IntegrationCredentialError(
                "Printify live credentials are not configured"
            )
    return product


def publish_listing(
    product: dict,
    credential: Optional[Dict[str, Optional[str]]] = None,
    require_live: bool = False,
) -> dict:
    if require_live:
        credential = _ensure_live_credential(OAuthProvider.ETSY, credential)
        if not os.getenv("ETSY_CLIENT_ID"):
            raise IntegrationCredentialError("ETSY_CLIENT_ID is required for live listing")
    client = get_etsy_client(credential)
    try:
        listing = client(product)
    except ValueError as exc:
        raise IntegrationPayloadError(str(exc)) from exc
    except RuntimeError as exc:
        raise IntegrationUpstreamError(str(exc)) from exc
    except httpx.HTTPError as exc:
        raise IntegrationUpstreamError("Etsy request failed") from exc
    if require_live:
        listing_id = str(listing.get("listing_id", "")).strip()
        listing_url = str(listing.get("etsy_url") or listing.get("listing_url") or "").strip()
        if not listing_id or listing_id.startswith("stub"):
            raise IntegrationCredentialError("Etsy live credentials are not configured")
        if not listing_url or listing_url.startswith("https://etsy.example/"):
            raise IntegrationCredentialError("Etsy live credentials are not configured")
    return listing
