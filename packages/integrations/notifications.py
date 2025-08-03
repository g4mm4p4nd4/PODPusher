"""Notification delivery stubs.

These helpers provide email and push notification functions. If the
``NOTIFY_USE_STUB`` environment variable is truthy (default) or the
required API keys are missing, the helpers merely print the payload
instead of performing any network calls. This keeps tests fast and
avoids external dependencies while allowing real integrations later.
"""
from __future__ import annotations

import os


USE_STUB = os.getenv("NOTIFY_USE_STUB", "1").lower() in {"1", "true", "yes"}


def send_email(user_id: int, message: str, notif_type: str) -> None:
    """Send an email notification or print a stub."""
    if USE_STUB or not os.getenv("EMAIL_API_KEY"):
        print(f"[stub email] user={user_id} type={notif_type} msg={message}")
        return
    raise NotImplementedError("Real email integration not configured")


def send_push(user_id: int, message: str, notif_type: str) -> None:
    """Send a push notification or print a stub."""
    if USE_STUB or not os.getenv("PUSH_API_KEY"):
        print(f"[stub push] user={user_id} type={notif_type} msg={message}")
        return
    raise NotImplementedError("Real push integration not configured")
