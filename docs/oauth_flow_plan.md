# OAuth UI & Flow Roadmap

This note sketches the work required to deliver production OAuth flows for Etsy, Printify, and Stripe.

## Frontend
- Build connect/disconnect widgets with provider status badges and token expiry messaging.
- Add callback handling page to capture `code`/`state` and surface errors to the user.
- Persist provider states in global store so generation flows can gate functionality.

## Backend
- Finalise refresh token rotation and background pruning in `services/auth/service.py`.
- Add webhook ingestion for Stripe account updates and plan changes.
- Harden rate limiting and error mapping for provider APIs.

## Testing
- Expand Playwright coverage to simulate happy/sad OAuth paths.
- Stub provider tokens in pytest fixtures for gateway `/generate` auth gating.

## Deployment
- Document environment variable expectations (client IDs, secrets, redirect URLs).
- Ensure Alembic migrations run prior to enabling OAuth to guarantee credential tables exist.

