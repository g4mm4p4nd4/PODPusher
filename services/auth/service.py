from __future__ import annotations

import base64
import hashlib
import logging
import os
import secrets
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import httpx
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlmodel import delete, select
from sqlmodel.ext.asyncio.session import AsyncSession

from ..common.database import get_session
from ..common.quotas import ensure_quota_state
from ..models import (
    OAuthCredential,
    OAuthProvider,
    OAuthState,
    User,
    UserSession,
)


@dataclass(slots=True)
class OAuthProviderConfig:
    name: OAuthProvider
    auth_url: str
    token_url: str
    scope: List[str]
    client_id_env: str
    client_secret_env: Optional[str] = None
    use_pkce: bool = False
    extra_auth_params: Dict[str, str] = field(default_factory=dict)
    token_headers: Dict[str, str] = field(default_factory=dict)


PROVIDERS: Dict[OAuthProvider, OAuthProviderConfig] = {
    OAuthProvider.ETSY: OAuthProviderConfig(
        name=OAuthProvider.ETSY,
        auth_url="https://www.etsy.com/oauth/connect",
        token_url="https://api.etsy.com/v3/public/oauth/token",
        scope=[
            "profile_r",
            "profile_w",
            "shops_r",
            "shops_w",
            "listings_r",
            "listings_w",
            "transactions_r",
            "transactions_w",
        ],
        client_id_env="ETSY_CLIENT_ID",
        client_secret_env="ETSY_CLIENT_SECRET",
        use_pkce=True,
        extra_auth_params={"response_type": "code", "code_challenge_method": "S256"},
    ),
    OAuthProvider.PRINTIFY: OAuthProviderConfig(
        name=OAuthProvider.PRINTIFY,
        auth_url="https://auth.printify.com/v1/oauth/authorize",
        token_url="https://auth.printify.com/v1/oauth/token",
        scope=["shop.read", "shop.write", "catalog.read"],
        client_id_env="PRINTIFY_CLIENT_ID",
        client_secret_env="PRINTIFY_CLIENT_SECRET",
        extra_auth_params={"response_type": "code"},
    ),
    OAuthProvider.STRIPE: OAuthProviderConfig(
        name=OAuthProvider.STRIPE,
        auth_url="https://connect.stripe.com/oauth/authorize",
        token_url="https://connect.stripe.com/oauth/token",
        scope=["read_write"],
        client_id_env="STRIPE_CLIENT_ID",
        client_secret_env="STRIPE_CLIENT_SECRET",
        extra_auth_params={"response_type": "code"},
    ),
}


logger = logging.getLogger(__name__)

REFRESH_LEEWAY_SECONDS = int(os.getenv("OAUTH_REFRESH_LEEWAY_SECONDS", "300"))
STATE_TTL_MINUTES = int(os.getenv("OAUTH_STATE_TTL_MINUTES", "15"))
CREDENTIAL_RETENTION_DAYS = int(os.getenv("OAUTH_CREDENTIAL_RETENTION_DAYS", "30"))
CLEANUP_INTERVAL_MINUTES = int(os.getenv("OAUTH_CLEANUP_INTERVAL_MINUTES", "60"))

_cleanup_scheduler = AsyncIOScheduler()


def _require_env(var: str) -> str:
    value = os.getenv(var)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {var}")
    return value


def _hash_sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


async def create_session(user_id: int, ttl_hours: int = 24) -> tuple[str, datetime]:
    token = secrets.token_urlsafe(32)
    token_hash = _hash_sha256(token)
    expires_at = datetime.utcnow() + timedelta(hours=ttl_hours)

    async with get_session() as session:
        user = await session.get(User, user_id)
        now = datetime.utcnow()
        if not user:
            user = User(id=user_id, last_reset=now)
            ensure_quota_state(user, now)
            session.add(user)
        session.add(
            UserSession(
                user_id=user_id,
                token_hash=token_hash,
                expires_at=expires_at,
            )
        )
        await session.commit()

    return token, expires_at


async def resolve_session_token(token: str) -> Optional[int]:
    token_hash = _hash_sha256(token)
    async with get_session() as session:
        result = await session.exec(
            select(UserSession).where(UserSession.token_hash == token_hash)
        )
        record = result.first()
        if not record:
            return None
        if record.expires_at < datetime.utcnow():
            await session.delete(record)
            await session.commit()
            return None
        return record.user_id


async def revoke_session(token: str) -> None:
    token_hash = _hash_sha256(token)
    async with get_session() as session:
        result = await session.exec(
            select(UserSession).where(UserSession.token_hash == token_hash)
        )
        record = result.first()
        if record:
            await session.delete(record)
            await session.commit()


def _generate_code_verifier() -> str:
    return base64.urlsafe_b64encode(os.urandom(40)).decode("utf-8").rstrip("=")


def _build_code_challenge(code_verifier: str) -> str:
    digest = hashlib.sha256(code_verifier.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(digest).decode("utf-8").rstrip("=")


def get_provider_config(provider: str) -> OAuthProviderConfig:
    try:
        provider_enum = OAuthProvider(provider)
    except ValueError as exc:
        raise ValueError(f"Unsupported OAuth provider: {provider}") from exc
    return PROVIDERS[provider_enum]


async def create_authorization_url(
    user_id: int,
    provider: str,
    redirect_uri: str,
    scope: Optional[List[str]] = None,
) -> str:
    config = get_provider_config(provider)
    client_id = _require_env(config.client_id_env)
    requested_scope = scope or config.scope

    state = secrets.token_urlsafe(24)
    code_verifier = _generate_code_verifier() if config.use_pkce else None
    params: Dict[str, str] = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "scope": " ".join(requested_scope),
        "state": state,
    }
    params.update(config.extra_auth_params)

    if config.use_pkce and code_verifier:
        params["code_challenge"] = _build_code_challenge(code_verifier)

    async with get_session() as session:
        state_record = OAuthState(
            state=state,
            user_id=user_id,
            provider=config.name,
            code_verifier=code_verifier,
            redirect_uri=redirect_uri,
        )
        session.add(state_record)
        await session.commit()

    from urllib.parse import urlencode

    return f"{config.auth_url}?{urlencode(params)}"


async def exchange_code(
    user_id: int,
    provider: str,
    code: str,
    state: str,
    redirect_uri: Optional[str] = None,
) -> Dict[str, Optional[str]]:
    config = get_provider_config(provider)
    client_id = _require_env(config.client_id_env)
    client_secret = (
        _require_env(config.client_secret_env)
        if config.client_secret_env
        else None
    )

    async with get_session() as session:
        state_record = await session.get(OAuthState, state)
        if not state_record or state_record.provider != config.name:
            raise ValueError("OAuth state mismatch or expired")
        if state_record.user_id != user_id:
            raise ValueError("OAuth state does not belong to the requesting user")

        redirect_target = redirect_uri or state_record.redirect_uri

        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_target,
            "client_id": client_id,
        }
        if client_secret:
            data["client_secret"] = client_secret
        if config.use_pkce and state_record.code_verifier:
            data["code_verifier"] = state_record.code_verifier

        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(
                config.token_url,
                data=data,
                headers={"Content-Type": "application/x-www-form-urlencoded", **config.token_headers},
            )
        response.raise_for_status()
        payload = response.json()

        expires_in = payload.get("expires_in")
        expires_at = (
            datetime.utcnow() + timedelta(seconds=int(expires_in))
            if expires_in
            else None
        )
        refresh_token = payload.get("refresh_token")
        scope = payload.get("scope")
        account_id = (
            payload.get("account_id")
            or payload.get("user_id")
            or payload.get("merchant_id")
            or payload.get("shop_id")
            or payload.get("store_id")
        )
        account_name = (
            payload.get("account_name")
            or payload.get("shop_name")
            or payload.get("store_name")
        )

        result = await session.exec(
            select(OAuthCredential).where(
                (OAuthCredential.user_id == user_id)
                & (OAuthCredential.provider == config.name)
            )
        )
        credential = result.first()
        if credential is None:
            credential = OAuthCredential(
                user_id=user_id,
                provider=config.name,
                access_token=payload["access_token"],
                refresh_token=refresh_token,
                expires_at=expires_at,
                scope=scope,
                account_id=account_id,
                account_name=account_name,
            )
            session.add(credential)
        else:
            credential.access_token = payload["access_token"]
            credential.refresh_token = refresh_token
            credential.expires_at = expires_at
            credential.scope = scope
            credential.account_id = account_id
            credential.account_name = account_name
            credential.updated_at = datetime.utcnow()
            session.add(credential)

        await session.delete(state_record)
        await session.commit()
        await session.refresh(credential)

    return {
        "provider": credential.provider.value,
        "expires_at": credential.expires_at.isoformat() if credential.expires_at else None,
        "scope": credential.scope,
        "account_id": credential.account_id,
        "account_name": credential.account_name,
    }


async def list_credentials(user_id: int) -> List[Dict[str, Optional[str]]]:
    async with get_session() as session:
        result = await session.exec(
            select(OAuthCredential).where(OAuthCredential.user_id == user_id)
        )
        credentials = result.all()
    summaries: List[Dict[str, Optional[str]]] = []
    for cred in credentials:
        summaries.append(
            {
                "provider": cred.provider.value,
                "expires_at": cred.expires_at.isoformat() if cred.expires_at else None,
                "scope": cred.scope,
                "account_id": cred.account_id,
                "account_name": cred.account_name,
            }
        )
    return summaries


async def delete_oauth_credential(user_id: int, provider: str) -> None:
    config = get_provider_config(provider)
    async with get_session() as session:
        result = await session.exec(
            select(OAuthCredential).where(
                (OAuthCredential.user_id == user_id)
                & (OAuthCredential.provider == config.name)
            )
        )
        credential = result.first()
        if credential:
            await session.delete(credential)
            await session.commit()


def _credential_requires_refresh(credential: OAuthCredential) -> bool:
    if not credential.refresh_token or credential.expires_at is None:
        return False
    window = credential.expires_at - timedelta(seconds=REFRESH_LEEWAY_SECONDS)
    return window <= datetime.utcnow()


async def _refresh_access_token(
    session: AsyncSession,
    credential: OAuthCredential,
    config: OAuthProviderConfig,
) -> OAuthCredential:
    client_id = _require_env(config.client_id_env)
    client_secret = (
        _require_env(config.client_secret_env)
        if config.client_secret_env
        else None
    )
    data = {
        "grant_type": "refresh_token",
        "refresh_token": credential.refresh_token,
        "client_id": client_id,
    }
    if client_secret:
        data["client_secret"] = client_secret
    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.post(
            config.token_url,
            data=data,
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                **config.token_headers,
            },
        )
    response.raise_for_status()
    payload = response.json()
    credential.access_token = payload.get("access_token", credential.access_token)
    new_refresh = payload.get("refresh_token")
    if new_refresh:
        credential.refresh_token = new_refresh
    expires_in = payload.get("expires_in")
    credential.expires_at = (
        datetime.utcnow() + timedelta(seconds=int(expires_in))
        if expires_in
        else None
    )
    scope = payload.get("scope")
    if scope:
        credential.scope = scope
    credential.updated_at = datetime.utcnow()
    session.add(credential)
    await session.commit()
    await session.refresh(credential)
    logger.debug("Refreshed %s credential for user %s", credential.provider, credential.user_id)
    return credential


async def ensure_credential_fresh(
    session: AsyncSession,
    credential: OAuthCredential,
) -> OAuthCredential:
    config = PROVIDERS.get(credential.provider)
    if not config:
        return credential
    if not _credential_requires_refresh(credential):
        return credential
    try:
        return await _refresh_access_token(session, credential, config)
    except Exception as exc:  # pragma: no cover - network failures bubble up
        logger.warning(
            "Failed to refresh %s credential for user %s: %s",
            credential.provider,
            credential.user_id,
            exc,
        )
        raise


async def prune_expired_oauth_records() -> None:
    now = datetime.utcnow()
    async with get_session() as session:
        if STATE_TTL_MINUTES > 0:
            state_cutoff = now - timedelta(minutes=STATE_TTL_MINUTES)
            await session.exec(
                delete(OAuthState).where(OAuthState.created_at < state_cutoff)
            )
        if CREDENTIAL_RETENTION_DAYS > 0:
            credential_cutoff = now - timedelta(days=CREDENTIAL_RETENTION_DAYS)
            await session.exec(
                delete(OAuthCredential).where(
                    (OAuthCredential.refresh_token.is_(None))
                    & (OAuthCredential.expires_at.is_not(None))
                    & (OAuthCredential.expires_at < credential_cutoff)
                )
            )
        await session.commit()


def start_cleanup_scheduler() -> None:
    if CLEANUP_INTERVAL_MINUTES <= 0:
        logger.debug("OAuth cleanup scheduler disabled via configuration")
        return
    if _cleanup_scheduler.running:
        return
    _cleanup_scheduler.add_job(
        prune_expired_oauth_records,
        "interval",
        minutes=CLEANUP_INTERVAL_MINUTES,
    )
    _cleanup_scheduler.start()


def stop_cleanup_scheduler() -> None:
    if _cleanup_scheduler.running:
        _cleanup_scheduler.shutdown(wait=False)
