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
- Document OAuth runtime credentials:
  - Etsy: `ETSY_CLIENT_ID`, `ETSY_CLIENT_SECRET`.
  - Printify: `PRINTIFY_CLIENT_ID`, `PRINTIFY_CLIENT_SECRET`.
  - Stripe Connect: `STRIPE_CLIENT_ID`, `STRIPE_CLIENT_SECRET`.
  - Optional listing fallback values: `ETSY_ACCESS_TOKEN`, `ETSY_SHOP_ID`, `PRINTIFY_API_KEY`.
- Ensure Alembic migrations run prior to enabling OAuth to guarantee credential tables exist.
