# PODPusher Development Plan

> **Created:** January 2026
> **Branch:** `claude/podpusher-dev-plan-Othn7`
> **Status:** Active Development

---

## Executive Summary

PODPusher is approximately **75-80% complete** for MVP launch. The core product pipeline (trends → ideas → images → products → listings) is functional, all 17 backend services are implemented, and the frontend dashboard has all major pages. This plan outlines the remaining work to reach production readiness.

**Estimated Timeline:** 6-8 weeks to MVP launch

---

## Current State Assessment

### Completed Features (Ready for Production)

| Component | Status | Notes |
|-----------|--------|-------|
| Trend Scraper | ✅ Complete | Fallback data + API endpoints |
| Ideation Service | ✅ Complete | GPT-4o integration with retry logic |
| Image Generation | ✅ Complete | gpt-image-1 wrapper + stub mode |
| Printify Integration | ✅ Complete | SKU creation, real API calls |
| Etsy Integration | ✅ Complete | Listing publisher, OAuth backend |
| Listing Composer | ✅ Complete | Drag-drop, drafts, validation |
| A/B Testing | ✅ Complete | Engine, variants, metrics |
| Analytics | ✅ Complete | Event tracking, dashboards |
| Notifications | ✅ Complete | Instant + scheduled, APScheduler |
| Social Generator | ✅ Complete | Captions, templates, 13 languages |
| Bulk Creation | ✅ Complete | CSV/JSON upload + validation |
| Search | ✅ Complete | Filtering, pagination |
| Auth Backend | ✅ Complete | OAuth PKCE, session management |
| Database | ✅ Complete | 15 models, Alembic migrations |
| CI/CD | ✅ Complete | GitHub Actions, full test suite |
| Observability | ✅ Complete | Prometheus, health checks, logging |

### Incomplete Features (Requires Work)

| Component | Completion | Blocking MVP? | Priority |
|-----------|------------|---------------|----------|
| OAuth UI (Frontend) | 20% | Yes | P0 |
| Stripe Billing | 10% | Yes | P0 |
| i18n Coverage | 40% | No | P1 |
| Live Trend Scrapers | 20% | No | P1 |
| Settings Page Polish | 50% | No | P2 |
| Advanced Search Ranking | 0% | No | P3 |

---

## Development Phases

### Phase 0: Critical MVP Blockers (Weeks 1-2)

These items **must** be completed before any beta launch.

#### Task 0.1: OAuth UI Integration
**Priority:** P0 | **Effort:** 5 days | **Owner:** Frontend-Coder

The backend OAuth endpoints are complete, but users cannot connect providers from the dashboard.

**Deliverables:**
1. `client/components/OAuthConnect.tsx` - Connect/disconnect widget
   - Provider status badges (connected/disconnected/expired)
   - Token expiry warning messages
   - One-click connect buttons with provider logos

2. `client/pages/settings.tsx` - Update to include OAuth widgets
   - Connected accounts section
   - Per-provider connection status
   - Disconnect confirmation modal

3. `client/services/oauth.ts` - Extend with:
   - `getProviderStatus()` - Check connection state
   - `disconnectProvider()` - Revoke access
   - `refreshConnection()` - Manual token refresh

4. Provider state in React context for gating generation flows

**Acceptance Criteria:**
- [ ] Users can connect Etsy, Printify, Stripe from Settings page
- [ ] Connection status visible with clear indicators
- [ ] Expired tokens show warning with refresh option
- [ ] Disconnect flow works with confirmation
- [ ] e2e tests cover happy/sad OAuth paths

**Files to Modify:**
- `client/pages/settings.tsx`
- `client/components/` (new: `OAuthConnect.tsx`, `ProviderBadge.tsx`)
- `client/services/oauth.ts`
- `client/contexts/` (new: `ProviderContext.tsx`)
- `tests/e2e/oauth.spec.ts` (new)

---

#### Task 0.2: Stripe Billing Integration
**Priority:** P0 | **Effort:** 5 days | **Owner:** Integrations-Engineer

Stripe is partially implemented (OAuth, conversion tracking) but payment processing is missing.

**Deliverables:**
1. `services/billing/` - New billing service
   ```
   services/billing/
   ├── __init__.py
   ├── api.py          # FastAPI endpoints
   ├── service.py      # Billing logic
   ├── webhooks.py     # Stripe webhook handlers
   └── plans.py        # Plan definitions
   ```

2. Webhook endpoints:
   - `POST /api/billing/webhooks` - Stripe webhook ingestion
   - Handle: `invoice.paid`, `invoice.payment_failed`, `customer.subscription.*`

3. Customer portal integration:
   - `GET /api/billing/portal` - Generate Stripe portal URL
   - Redirect users to manage subscriptions

4. Quota enforcement updates:
   - Link plan tier to user quotas
   - Automatic quota adjustment on plan change

**Acceptance Criteria:**
- [ ] Stripe webhooks processed and stored
- [ ] Users can access Stripe customer portal
- [ ] Plan upgrades/downgrades update quotas
- [ ] 402 returned when quota exceeded
- [ ] Unit tests for webhook handlers

**Files to Create:**
- `services/billing/` directory
- `tests/test_billing.py`
- `tests/test_billing_webhooks.py`

**Files to Modify:**
- `services/gateway/api.py` (mount billing service)
- `services/common/quotas.py` (link to billing)

---

### Phase 1: Core Experience Polish (Weeks 3-4)

#### Task 1.1: Internationalization Expansion
**Priority:** P1 | **Effort:** 4 days | **Owner:** Frontend-Coder

Currently only 40% of UI strings are translated. Per `docs/i18n_plan.md`:

**Deliverables:**
1. Audit and extract all hard-coded strings:
   - `client/pages/analytics.tsx`
   - `client/pages/bulk-upload.tsx`
   - `client/pages/notifications.tsx`
   - `client/pages/search.tsx`
   - `client/pages/settings.tsx`
   - `client/pages/ab_tests.tsx`

2. Create `scripts/i18n_extract.ts` - Extract untranslated strings

3. Expand locale files:
   ```
   client/locales/en/common.json  - Add missing keys
   client/locales/es/common.json  - Add Spanish translations
   client/locales/fr/common.json  - Add French (new)
   client/locales/de/common.json  - Add German (new)
   ```

4. Implement ICU formatting for currencies:
   - Use `Intl.NumberFormat` for monetary values
   - Add locale metadata to API responses

5. Update Playwright tests for language switching coverage

**Acceptance Criteria:**
- [ ] Zero hard-coded user-facing strings in `client/pages/`
- [ ] 4 languages supported (EN, ES, FR, DE)
- [ ] Currency formatting respects user locale
- [ ] CI translation verification passes
- [ ] Language switching e2e test covers all major pages

**Files to Modify:**
- All files in `client/pages/`
- `client/locales/` (expand)
- `scripts/verify_translations.py` (update)
- `tests/e2e/localization.spec.ts` (expand)

---

#### Task 1.2: Live Trend Scrapers
**Priority:** P1 | **Effort:** 5 days | **Owner:** Data-Seeder

The trend ingestion infrastructure exists but actual scrapers need implementation.

**Deliverables:**
1. Complete Playwright scrapers in `services/trend_ingestion/sources.py`:
   ```python
   async def scrape_tiktok() -> list[RawSignal]
   async def scrape_instagram() -> list[RawSignal]
   async def scrape_twitter() -> list[RawSignal]
   async def scrape_pinterest() -> list[RawSignal]
   async def scrape_etsy_trending() -> list[RawSignal]
   ```

2. Rate limiting and retry logic per platform

3. Proxy rotation support for scraping resilience

4. Admin endpoint for manual re-scrape trigger:
   - `POST /api/trends/refresh` - Trigger immediate scrape

5. Monitoring and alerting for scrape failures

**Acceptance Criteria:**
- [ ] ≥50 unique keywords per scrape cycle
- [ ] ≤5% scrape failure rate
- [ ] Scrapers respect platform rate limits
- [ ] Failed scrapes trigger alerts
- [ ] Manual refresh works from admin UI

**Files to Modify:**
- `services/trend_ingestion/sources.py`
- `services/trend_ingestion/service.py`
- `services/trend_ingestion/api.py`
- `tests/test_trend_ingestion_scrapers.py` (new)

---

#### Task 1.3: Settings Page Completion
**Priority:** P1 | **Effort:** 2 days | **Owner:** Frontend-Coder

**Deliverables:**
1. Complete user preferences section:
   - Notification channel preferences (email/push toggles)
   - Default language selection
   - Currency preference
   - Timezone setting

2. Social handles configuration:
   - Instagram, TikTok, Twitter handles
   - Used by social generator service

3. Quota display with upgrade CTA:
   - Current usage vs limit
   - Visual progress bars
   - "Upgrade" button linking to Stripe portal

**Files to Modify:**
- `client/pages/settings.tsx`
- `client/components/UserQuota.tsx`
- `client/components/SocialSettings.tsx`

---

### Phase 2: Enhanced Reliability (Weeks 5-6)

#### Task 2.1: Error Handling Standardization
**Priority:** P1 | **Effort:** 3 days | **Owner:** Backend-Coder

**Deliverables:**
1. Standardized error response schema:
   ```python
   class APIError(BaseModel):
       code: str
       message: str
       details: dict | None
       request_id: str
   ```

2. Error mapping for external APIs:
   - Printify error codes → user-friendly messages
   - Etsy error codes → user-friendly messages
   - OpenAI content policy → clear feedback

3. Frontend error boundary with user-friendly messages

**Files to Create:**
- `services/common/errors.py`
- `client/components/ErrorBoundary.tsx`

**Files to Modify:**
- `services/integration/service.py`
- `services/ideation/service.py`
- `services/image_gen/service.py`

---

#### Task 2.2: Rate Limiting Implementation
**Priority:** P1 | **Effort:** 2 days | **Owner:** Backend-Coder

**Deliverables:**
1. Install and configure `fastapi-limiter`:
   - Per-user rate limits based on plan tier
   - Per-IP rate limits for unauthenticated endpoints

2. Rate limit headers in responses:
   - `X-RateLimit-Limit`
   - `X-RateLimit-Remaining`
   - `X-RateLimit-Reset`

3. Graceful handling when limits exceeded

**Files to Modify:**
- `services/gateway/api.py`
- `services/common/` (new: `rate_limit.py`)
- `requirements.txt`

---

#### Task 2.3: Performance Optimization
**Priority:** P2 | **Effort:** 3 days | **Owner:** Backend-Coder + Frontend-Coder

**Deliverables:**
1. Backend:
   - Add Redis caching for trend data (5-min TTL)
   - Optimize database queries with proper indexing
   - Add connection pooling configuration

2. Frontend:
   - Implement React.memo for expensive components
   - Add virtualization for long lists
   - Optimize bundle size with dynamic imports

3. Metrics:
   - Ensure P95 API latency < 300ms
   - Frontend CLS < 0.1

---

### Phase 3: Launch Preparation (Weeks 7-8)

#### Task 3.1: Security Audit
**Priority:** P0 | **Effort:** 2 days | **Owner:** Backend-Coder

**Deliverables:**
1. Input validation on all endpoints
2. SQL injection prevention verification
3. XSS protection in frontend
4. CSRF protection for state-changing operations
5. Secrets management audit
6. Dependency vulnerability scan (Snyk)

---

#### Task 3.2: Documentation Completion
**Priority:** P1 | **Effort:** 2 days | **Owner:** Docs-Writer

**Deliverables:**
1. User onboarding guide
2. API documentation (OpenAPI spec)
3. Provider connection guides (Etsy, Printify, Stripe)
4. Troubleshooting FAQ
5. Environment setup documentation

---

#### Task 3.3: Load Testing & Monitoring
**Priority:** P1 | **Effort:** 2 days | **Owner:** DevOps-Engineer

**Deliverables:**
1. Load test suite (k6 or Locust)
2. Target: 2000 concurrent users, 10000 daily image jobs
3. Grafana dashboards for production monitoring
4. Alert rules for SLO breaches

---

## Technical Debt to Address

Per `agents.md` Section 13:

| ID | Description | Priority | Phase |
|----|-------------|----------|-------|
| TD-01 | Replace in-memory scraper cache with Timescale continuous aggregates | High | Phase 2 |
| TD-02 | Comprehensive error handling for Printify API | Medium | Phase 2 |
| TD-03 | Reduce GPT hallucinations in descriptions | Medium | Phase 3 |
| TD-04 | Pagination for trend signals API | Low | Phase 3 |

---

## Post-MVP Roadmap

### Month 2-3: Stabilize & Enhance
- [ ] Bug backlog burndown
- [ ] A/B optimization for listings
- [ ] Scheduled product drops
- [ ] Enhanced social media posting

### Month 4-6: Scale & Collaborate
- [ ] Agency workspaces with team roles
- [ ] Community prompt pack marketplace
- [ ] Additional POD provider integrations
- [ ] Team analytics dashboard

### Month 7-12: Monetize & Expand
- [ ] Premium tier features
- [ ] Dynamic pricing advisor
- [ ] Shopify integration
- [ ] Amazon Merch integration

---

## Development Workflow

### Branch Strategy
```
main                    - Production releases
├── staging            - Pre-production testing
├── claude/*           - AI agent development branches
└── agent/<handle>/*   - Human developer branches
```

### PR Requirements
1. All CI checks pass (tests, lint, migrations)
2. Documentation updated
3. Changelog entry added
4. Code review approved

### Definition of Done
Per `agents.md` Section 17:
1. Story moved to Done in project board
2. All automated checks pass
3. Docs, tests, changelog updated
4. Staging deployment successful
5. Smoke tests pass

---

## Quick Start for Developers

### Prerequisites
- Python 3.11+
- Node.js 18+
- Docker & Docker Compose
- PostgreSQL 15+
- Redis 7+

### Setup
```bash
# Clone and install dependencies
git clone <repo>
cd PODPusher
pip install -r requirements.txt
cd client && npm install && cd ..

# Start infrastructure
docker-compose up -d postgres redis

# Run migrations
alembic upgrade head

# Start backend
uvicorn services.gateway.api:app --reload

# Start frontend (separate terminal)
cd client && npm run dev
```

### Running Tests
```bash
# Backend tests
pytest tests/

# Frontend tests
cd client && npm test

# E2E tests
cd client && npx playwright test
```

---

## Appendix: File Structure Overview

```
PODPusher/
├── services/                    # Backend microservices
│   ├── gateway/                # Main API gateway
│   ├── auth/                   # OAuth & sessions
│   ├── trend_scraper/          # Static trend data
│   ├── trend_ingestion/        # Live Playwright scrapers
│   ├── ideation/               # GPT idea generation
│   ├── image_gen/              # Image generation
│   ├── integration/            # Printify/Etsy clients
│   ├── listing_composer/       # Draft management
│   ├── ab_tests/               # A/B testing engine
│   ├── analytics/              # Event tracking
│   ├── notifications/          # Notification system
│   ├── search/                 # Product search
│   ├── social_generator/       # Social captions
│   ├── bulk_create/            # Bulk upload
│   ├── product/                # Product CRUD
│   ├── user/                   # User management
│   └── common/                 # Shared utilities
├── client/                     # Next.js frontend
│   ├── pages/                  # Route pages
│   ├── components/             # React components
│   ├── services/               # API clients
│   └── locales/                # i18n translations
├── tests/                      # Python tests
│   └── e2e/                    # Playwright specs
├── alembic/                    # Database migrations
├── docs/                       # Documentation
└── scripts/                    # Utility scripts
```

---

## Contact & Escalation

- **Project Manager Agent:** Coordinates all development
- **Architect:** Technical decisions and design reviews
- **Issues:** GitHub Issues for bug tracking
- **Docs:** See `docs/internal_docs.md` for detailed guides

---

*This plan aligns with the specifications in `agents.md` and supersedes previous planning documents.*
