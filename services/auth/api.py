from __future__ import annotations

import os
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import Depends, FastAPI, HTTPException, Request, status
from pydantic import BaseModel, HttpUrl

from ..common.auth import require_user_id
from ..common.observability import register_observability
from .service import (
    PROVIDERS,
    create_authorization_url,
    create_session,
    exchange_code,
    list_credentials,
    prune_expired_oauth_records,
    revoke_session,
    start_cleanup_scheduler,
    stop_cleanup_scheduler,
    delete_oauth_credential,
)

@asynccontextmanager
async def _auth_lifespan(_: FastAPI):
    start_cleanup_scheduler()
    await prune_expired_oauth_records()
    try:
        yield
    finally:
        stop_cleanup_scheduler()

app = FastAPI(lifespan=_auth_lifespan)
register_observability(app, service_name="auth")

SESSION_SECRET = os.getenv("POD_SESSION_SECRET")

class SessionRequest(BaseModel):
    user_id: int
    ttl_hours: Optional[int] = 24
    secret: Optional[str] = None

class SessionResponse(BaseModel):
    token: str
    expires_at: datetime

class SessionRevokeRequest(BaseModel):
    token: str

class AuthorizeRequest(BaseModel):
    redirect_uri: HttpUrl
    scope: Optional[List[str]] = None

class AuthorizeResponse(BaseModel):
    authorization_url: HttpUrl

class CallbackRequest(BaseModel):
    code: str
    state: str
    redirect_uri: Optional[HttpUrl] = None

class CallbackResponse(BaseModel):
    provider: str
    expires_at: Optional[datetime] = None
    scope: Optional[str] = None
    account_id: Optional[str] = None
    account_name: Optional[str] = None

class CredentialSummary(BaseModel):
    provider: str
    expires_at: Optional[datetime] = None
    scope: Optional[str] = None
    account_id: Optional[str] = None
    account_name: Optional[str] = None

@app.post("/session", response_model=SessionResponse)
async def create_session_endpoint(payload: SessionRequest) -> SessionResponse:
    if SESSION_SECRET and payload.secret != SESSION_SECRET:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Invalid session secret")
    ttl = payload.ttl_hours or 24
    token, expires_at = await create_session(payload.user_id, ttl)
    return SessionResponse(token=token, expires_at=expires_at)

@app.post("/session/revoke")
async def revoke_session_endpoint(payload: SessionRevokeRequest) -> dict[str, str]:
    await revoke_session(payload.token)
    return {"status": "ok"}

@app.get("/providers")
async def list_providers() -> List[dict[str, object]]:
    items: List[dict[str, object]] = []
    for config in PROVIDERS.values():
        items.append(
            {
                "provider": config.name.value,
                "auth_url": config.auth_url,
                "token_url": config.token_url,
                "scope": config.scope,
                "use_pkce": config.use_pkce,
            }
        )
    return items

@app.post("/{provider}/authorize", response_model=AuthorizeResponse)
async def authorize_provider(
    provider: str,
    payload: AuthorizeRequest,
    user_id: int = Depends(require_user_id),
) -> AuthorizeResponse:
    url = await create_authorization_url(
        user_id=user_id,
        provider=provider,
        redirect_uri=str(payload.redirect_uri),
        scope=payload.scope,
    )
    return AuthorizeResponse(authorization_url=url)

@app.post("/{provider}/callback", response_model=CallbackResponse)
async def authorize_callback(
    provider: str,
    payload: CallbackRequest,
    user_id: int = Depends(require_user_id),
) -> CallbackResponse:
    data = await exchange_code(
        user_id=user_id,
        provider=provider,
        code=payload.code,
        state=payload.state,
        redirect_uri=str(payload.redirect_uri) if payload.redirect_uri else None,
    )
    expires_at = (
        datetime.fromisoformat(data["expires_at"]) if data.get("expires_at") else None
    )
    return CallbackResponse(
        provider=data.get("provider", provider),
        expires_at=expires_at,
        scope=data.get("scope"),
        account_id=data.get("account_id"),
        account_name=data.get("account_name"),
    )

@app.delete("/credentials/{provider}")
async def delete_credential(provider: str, user_id: int = Depends(require_user_id)) -> dict[str, str]:
    await delete_oauth_credential(user_id, provider)
    return {"status": "ok"}

@app.get("/credentials", response_model=List[CredentialSummary])
async def get_credentials(user_id: int = Depends(require_user_id)) -> List[CredentialSummary]:
    items = await list_credentials(user_id)
    summaries: List[CredentialSummary] = []
    for item in items:
        expires_at = (
            datetime.fromisoformat(item["expires_at"]) if item.get("expires_at") else None
        )
        summaries.append(
            CredentialSummary(
                provider=item.get("provider"),
                expires_at=expires_at,
                scope=item.get("scope"),
                account_id=item.get("account_id"),
                account_name=item.get("account_name"),
            )
        )
    return summaries
