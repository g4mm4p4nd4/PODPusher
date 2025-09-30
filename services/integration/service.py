from __future__ import annotations

from typing import Dict, List, Optional

from sqlmodel import select

from packages.integrations.printify import get_printify_client
from packages.integrations.etsy import get_etsy_client
from services.auth import service as auth_service
from ..common.database import get_session
from ..models import OAuthCredential, OAuthProvider


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
    client = get_printify_client(credential)
    return client(products)


def publish_listing(product: dict, credential: Optional[Dict[str, Optional[str]]] = None) -> dict:
    client = get_etsy_client(credential)
    return client(product)
