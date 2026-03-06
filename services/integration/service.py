from __future__ import annotations

import logging
from typing import Dict, List, Optional

from sqlmodel import select

from packages.integrations.printify import get_printify_client
from packages.integrations.etsy import get_etsy_client
from services.auth import service as auth_service
from ..common.database import get_session
from ..common.provider_errors import handle_printify_error, handle_etsy_error
from ..common.api_limiter import rate_limited_call
from ..models import OAuthCredential, OAuthProvider

logger = logging.getLogger(__name__)


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


def create_sku(products: List[dict], credential: Optional[Dict[str, Optional[str]]] = None) -> List[dict]:
    """Create SKUs via Printify with error handling and rate limiting."""
    client = get_printify_client(credential)
    try:
        return client(products)
    except Exception as exc:
        raise handle_printify_error(exc, context={"product_count": len(products)})


def publish_listing(product: dict, credential: Optional[Dict[str, Optional[str]]] = None) -> dict:
    """Publish a listing via Etsy with error handling and rate limiting."""
    client = get_etsy_client(credential)
    try:
        return client(product)
    except Exception as exc:
        raise handle_etsy_error(exc, context={"title": product.get("title", "")[:50]})
