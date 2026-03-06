# PODPusher Development Plan

> **Created:** January 2026
> **Branch:** `claude/podpusher-dev-plan-Othn7`
> **Status:** Active Development
> **Authority:** This plan follows the multi-agent workflow defined in [`agents.md`](./agents.md)

---

## Agent Directory

This project uses a multi-agent development workflow. Each agent has specific responsibilities defined in their specification file:

| Agent | Specification | Primary Responsibilities |
|-------|--------------|-------------------------|
| **Project-Manager** | [`agents_project_manager.md`](./agents_project_manager.md) | Task decomposition, agent delegation, PR gatekeeping, KPI monitoring |
| **Spec-Writer** | [`agents_spec_writer.md`](./agents_spec_writer.md) | Feature specs (Gherkin), acceptance criteria, domain glossary |
| **Architect** | [`agents_architect.md`](./agents_architect.md) | System design, OpenAPI specs, database schemas, security |
| **Backend-Coder** | [`agents_backend_coder.md`](./agents_backend_coder.md) | FastAPI services, business logic, Celery tasks, repositories |
| **Frontend-Coder** | [`agents_frontend_coder.md`](./agents_frontend_coder.md) | Next.js pages, React components, state management, i18n |
| **Auth-Integrator** | [`agents_auth_integrator.md`](./agents_auth_integrator.md) | OAuth PKCE flows, token management, RBAC enforcement |
| **AI-Engineer** | [`agents_ai_engineer.md`](./agents_ai_engineer.md) | Prompt engineering, GPT/image generation, content safety |
| **Data-Seeder** | [`agents_data_seeder.md`](./agents_data_seeder.md) | Trend scraping, data ingestion, ETL pipelines, fallback data |
| **Integrations-Engineer** | [`agents_integrations_engineer.md`](./agents_integrations_engineer.md) | Printify/Etsy/Stripe clients, webhooks, rate limiting |
| **Unit-Tester** | [`agents_unit_tester.md`](./agents_unit_tester.md) | PyTest/Jest tests, coverage enforcement, regression prevention |
| **QA-Automator** | [`agents_qa_automator.md`](./agents_qa_automator.md) | Playwright e2e tests, performance testing, accessibility |
| **DevOps-Engineer** | [`agents_dev_ops_engineer.md`](./agents_dev_ops_engineer.md) | CI/CD, Docker, Kubernetes, monitoring, incident response |
| **Docs-Writer** | [`agents_docs_writer.md`](./agents_docs_writer.md) | User guides, API docs, changelog, marketing content |

### Agent Workflow

```
Project-Manager → Spec-Writer → Architect
                                    ↓
                    ┌───────────────┼───────────────┐
                    ↓               ↓               ↓
            Backend-Coder   Frontend-Coder   Auth-Integrator
                    ↓               ↓               ↓
                    └───────────────┼───────────────┘
                                    ↓
                    ┌───────────────┼───────────────┐
                    ↓               ↓               ↓
              AI-Engineer    Data-Seeder   Integrations-Engineer
                    ↓               ↓               ↓
                    └───────────────┼───────────────┘
                                    ↓
                              Unit-Tester
                                    ↓
                              QA-Automator
                                    ↓
                            DevOps-Engineer
                                    ↓
                              Docs-Writer
                                    ↓
                            Project-Manager (merge)
```

---

## Executive Summary

PODPusher is approximately **75-80% complete** for MVP launch. The core product pipeline (trends → ideas → images → products → listings) is functional, all 17 backend services are implemented, and the frontend dashboard has all major pages. This plan outlines the remaining work to reach production readiness.

**Estimated Timeline:** 6-8 weeks to MVP launch

---

## Current State Assessment

### Completed Features (Ready for Production)

| Component | Status | Owner Agent |
|-----------|--------|-------------|
| Trend Scraper | ✅ Complete | Data-Seeder |
| Ideation Service | ✅ Complete | AI-Engineer |
| Image Generation | ✅ Complete | AI-Engineer |
| Printify Integration | ✅ Complete | Integrations-Engineer |
| Etsy Integration | ✅ Complete | Integrations-Engineer |
| Listing Composer | ✅ Complete | Frontend-Coder |
| A/B Testing | ✅ Complete | Backend-Coder |
| Analytics | ✅ Complete | Backend-Coder |
| Notifications | ✅ Complete | Backend-Coder |
| Social Generator | ✅ Complete | AI-Engineer |
| Bulk Creation | ✅ Complete | Backend-Coder |
| Search | ✅ Complete | Backend-Coder |
| Auth Backend | ✅ Complete | Auth-Integrator |
| Database | ✅ Complete | Architect |
| CI/CD | ✅ Complete | DevOps-Engineer |
| Observability | ✅ Complete | DevOps-Engineer |

### Incomplete Features (Requires Work)

| Component | Completion | Priority | Owner Agent(s) |
|-----------|------------|----------|----------------|
| OAuth UI (Frontend) | 20% | P0 | Frontend-Coder, Auth-Integrator |
| Stripe Billing | 10% | P0 | Integrations-Engineer, Backend-Coder |
| i18n Coverage | 40% | P1 | Frontend-Coder, Docs-Writer |
| Live Trend Scrapers | 20% | P1 | Data-Seeder |
| Settings Page Polish | 50% | P2 | Frontend-Coder |
| Advanced Search Ranking | 0% | P3 | Backend-Coder, Architect |

---

## Development Phases

### Phase 0: Critical MVP Blockers (Weeks 1-2)

These items **must** be completed before any beta launch.

---

#### Task 0.1: OAuth UI Integration

| Attribute | Value |
|-----------|-------|
| **Priority** | P0 - Critical |
| **Effort** | 5 days |
| **Primary Agent** | Frontend-Coder |
| **Supporting Agents** | Auth-Integrator, Unit-Tester, QA-Automator |

**Reference Specs:**
- Frontend-Coder responsibilities: FC-05 (Authentication & Authorization)
- Auth-Integrator responsibilities: AU-06 (SSO & Account Linking)
- See [`docs/oauth_flow_plan.md`](./docs/oauth_flow_plan.md)

**Deliverables:**

1. **OAuthConnect Component** (`client/components/OAuthConnect.tsx`)
   - Provider status badges (connected/disconnected/expired)
   - Token expiry warning messages
   - One-click connect buttons with provider logos
   - *Owner:* Frontend-Coder

2. **Provider Context** (`client/contexts/ProviderContext.tsx`)
   - Track connected providers (Etsy, Printify, Stripe)
   - Expose `isConnected(provider)` helper
   - Auto-refresh status on mount
   - *Owner:* Frontend-Coder

3. **Settings Page Update** (`client/pages/settings.tsx`)
   - Connected accounts section
   - Per-provider connection status
   - Disconnect confirmation modal
   - *Owner:* Frontend-Coder

4. **OAuth Service Extension** (`client/services/oauth.ts`)
   - `getProviderStatus()` - Check connection state
   - `disconnectProvider()` - Revoke access
   - `refreshConnection()` - Manual token refresh
   - *Owner:* Frontend-Coder

5. **E2E Tests** (`tests/e2e/oauth_connect.spec.ts`)
   - Happy path: connect provider
   - Disconnect flow
   - Expired token warning
   - Generation flow gating
   - *Owner:* QA-Automator

**Acceptance Criteria (per agents.md §17):**
- [ ] Users can connect Etsy, Printify, Stripe from Settings page
- [ ] Connection status visible with clear indicators
- [ ] Expired tokens show warning with refresh option
- [ ] Disconnect flow works with confirmation
- [ ] E2E tests pass (≥98% pass rate per QA-01)
- [ ] Unit test coverage ≥90% (per UT-02)

---

#### Task 0.2: Stripe Billing Integration

| Attribute | Value |
|-----------|-------|
| **Priority** | P0 - Critical |
| **Effort** | 5 days |
| **Primary Agent** | Integrations-Engineer |
| **Supporting Agents** | Backend-Coder, Auth-Integrator, Unit-Tester |

**Reference Specs:**
- Integrations-Engineer responsibilities: IN-03 (Stripe Integration), IN-07 (Webhook Processing)
- Backend-Coder responsibilities: BC-03 (Authentication & Authorization)
- See [`agents.md`](./agents.md) §11 MVP Feature Matrix: Billing & Quotas

**Deliverables:**

1. **Billing Service** (`services/billing/`)
   ```
   services/billing/
   ├── __init__.py
   ├── api.py          # FastAPI endpoints
   ├── service.py      # Billing logic
   ├── webhooks.py     # Stripe webhook handlers
   └── plans.py        # Plan definitions
   ```
   - *Owner:* Integrations-Engineer

2. **Webhook Handlers** (`services/billing/webhooks.py`)
   - `invoice.paid` - Activate subscription
   - `invoice.payment_failed` - Notify user
   - `customer.subscription.created` - Set quotas
   - `customer.subscription.updated` - Update quotas
   - `customer.subscription.deleted` - Downgrade
   - Signature verification (per IN-07)
   - *Owner:* Integrations-Engineer

3. **Customer Portal** (`GET /api/billing/portal`)
   - Generate Stripe portal session URL
   - Return redirect URL to frontend
   - *Owner:* Integrations-Engineer

4. **Quota Enforcement** (`services/common/quotas.py`)
   - Query user's plan tier from billing
   - Apply tier-specific limits
   - Return 402 when exceeded (per AU-05)
   - *Owner:* Backend-Coder

5. **Tests**
   - `tests/test_billing.py` - Service logic
   - `tests/test_billing_webhooks.py` - Webhook handlers
   - *Owner:* Unit-Tester

**Acceptance Criteria:**
- [ ] Stripe webhooks processed and stored
- [ ] Users can access Stripe customer portal
- [ ] Plan upgrades/downgrades update quotas
- [ ] 402 returned when quota exceeded
- [ ] ≥98% API call success rate (per IN KPIs)
- [ ] Error mapping coverage 100% (per IN-05)

---

### Phase 1: Core Experience Polish (Weeks 3-4)

---

#### Task 1.1: Internationalization Expansion

| Attribute | Value |
|-----------|-------|
| **Priority** | P1 |
| **Effort** | 4 days |
| **Primary Agent** | Frontend-Coder |
| **Supporting Agents** | Docs-Writer, QA-Automator |

**Reference Specs:**
- Frontend-Coder standing assumptions §7: "Internationalisation is considered"
- See [`docs/i18n_plan.md`](./docs/i18n_plan.md)

**Deliverables:**

1. **String Extraction Audit** (per i18n_plan.md Action Item 1)
   - Audit `client/pages/analytics.tsx` - extract hard-coded strings
   - Audit `client/pages/bulk-upload.tsx`
   - Audit `client/pages/notifications.tsx`
   - Audit `client/pages/search.tsx`
   - Audit `client/pages/settings.tsx`
   - Audit `client/pages/ab_tests.tsx`
   - *Owner:* Frontend-Coder

2. **Extraction Script** (`scripts/i18n_extract.ts`)
   - Scan for untranslated strings
   - Output missing keys to JSON
   - *Owner:* Frontend-Coder

3. **Expanded Locale Files**
   - `client/locales/en/common.json` - Add missing keys
   - `client/locales/es/common.json` - Complete Spanish
   - `client/locales/fr/common.json` - Add French (new)
   - `client/locales/de/common.json` - Add German (new)
   - *Owner:* Frontend-Coder, Docs-Writer (for copy)

4. **ICU Currency Formatting** (per i18n_plan.md Action Item 3)
   - `Intl.NumberFormat` wrapper utility
   - Update price displays
   - Locale metadata in API responses
   - *Owner:* Frontend-Coder

5. **E2E Locale Tests** (per i18n_plan.md Action Item 4)
   - Update `tests/e2e/localization.spec.ts`
   - Test all pages with ES, FR, DE locales
   - Test currency formatting
   - *Owner:* QA-Automator

**Acceptance Criteria:**
- [ ] Zero hard-coded user-facing strings in `client/pages/`
- [ ] 4 languages supported (EN, ES, FR, DE)
- [ ] Currency formatting respects user locale
- [ ] CI translation verification passes
- [ ] Lighthouse accessibility ≥90 (per FC KPIs)

---

#### Task 1.2: Live Trend Scrapers

| Attribute | Value |
|-----------|-------|
| **Priority** | P1 |
| **Effort** | 5 days |
| **Primary Agent** | Data-Seeder |
| **Supporting Agents** | Backend-Coder, Unit-Tester, DevOps-Engineer |

**Reference Specs:**
- Data-Seeder responsibilities: DS-01 (Trend Scraping), DS-02 (Data Cleaning), DS-06 (Monitoring)
- Data-Seeder KPIs: ≥95% scrape success, ≥50 keywords per scan
- See [`agents.md`](./agents.md) §11 MVP: Trend Scraper

**Deliverables:**

1. **Platform Scrapers** (`services/trend_ingestion/sources.py`)
   ```python
   async def scrape_tiktok() -> list[RawSignal]
   async def scrape_instagram() -> list[RawSignal]
   async def scrape_twitter() -> list[RawSignal]
   async def scrape_pinterest() -> list[RawSignal]
   async def scrape_etsy_trending() -> list[RawSignal]
   ```
   - *Owner:* Data-Seeder

2. **Rate Limiting & Retry** (per DS-01, DS-06)
   - Respect platform rate limits
   - Exponential backoff with jitter
   - Circuit breaker pattern
   - *Owner:* Data-Seeder

3. **Proxy Rotation** (per DS standing assumptions §7)
   - Randomize user agents
   - Implement proxy pool
   - Handle bot detection gracefully
   - *Owner:* Data-Seeder

4. **Manual Refresh Endpoint** (`POST /api/trends/refresh`)
   - Trigger immediate scrape
   - Admin-only access
   - *Owner:* Backend-Coder

5. **Monitoring & Alerting** (per DS-06)
   - Scrape success/failure metrics
   - Alert on ≥5% failure rate
   - Fallback to curated data on outage
   - *Owner:* DevOps-Engineer

6. **Tests** (`tests/test_trend_scrapers.py`)
   - Mock Playwright responses
   - Test normalization
   - Test error handling
   - *Owner:* Unit-Tester

**Acceptance Criteria:**
- [ ] ≥50 unique keywords per scrape cycle (per DS KPIs)
- [ ] ≤5% scrape failure rate (per DS KPIs)
- [ ] Scrapers respect platform rate limits
- [ ] Failed scrapes trigger alerts
- [ ] 100% fallback availability (per DS KPIs)
- [ ] Manual refresh works from admin UI

---

#### Task 1.3: Settings Page Completion

| Attribute | Value |
|-----------|-------|
| **Priority** | P1 |
| **Effort** | 2 days |
| **Primary Agent** | Frontend-Coder |
| **Supporting Agents** | Backend-Coder |

**Deliverables:**

1. **User Preferences Section**
   - Notification channel toggles (email/push)
   - Default language selector
   - Currency preference dropdown
   - Timezone setting
   - *Owner:* Frontend-Coder

2. **Social Handles Configuration**
   - Instagram, TikTok, Twitter handle inputs
   - Handle format validation
   - Used by social generator service
   - *Owner:* Frontend-Coder

3. **Quota Display Enhancement** (`client/components/UserQuota.tsx`)
   - Visual progress bars
   - Usage breakdown by resource type
   - "Upgrade" CTA button linking to Stripe portal
   - *Owner:* Frontend-Coder

**Acceptance Criteria:**
- [ ] All preference changes persist
- [ ] Social handles validate format
- [ ] Quota display shows accurate usage
- [ ] Upgrade button opens Stripe portal

---

### Phase 2: Enhanced Reliability (Weeks 5-6)

---

#### Task 2.1: Error Handling Standardization

| Attribute | Value |
|-----------|-------|
| **Priority** | P1 |
| **Effort** | 3 days |
| **Primary Agent** | Backend-Coder |
| **Supporting Agents** | Frontend-Coder, Integrations-Engineer |

**Reference Specs:**
- Backend-Coder responsibilities: BC-04 (Input Validation & Error Handling)
- Integrations-Engineer responsibilities: IN-05 (Error Handling & Logging)
- Technical Debt: TD-02 (Printify error handling)

**Deliverables:**

1. **Standardized Error Schema** (`services/common/errors.py`)
   ```python
   class APIError(BaseModel):
       code: str
       message: str
       details: dict | None
       request_id: str
   ```
   - *Owner:* Backend-Coder

2. **Provider Error Mapping**
   - Printify error codes → user-friendly messages (TD-02)
   - Etsy error codes → user-friendly messages
   - OpenAI content policy → clear feedback
   - *Owner:* Integrations-Engineer

3. **Frontend Error Boundary** (`client/components/ErrorBoundary.tsx`)
   - Catch and display errors gracefully
   - "Try Again" action
   - Log errors to analytics
   - *Owner:* Frontend-Coder

**Acceptance Criteria:**
- [ ] All API errors return standardized format
- [ ] 100% error mapping coverage (per IN-05)
- [ ] <1% 5xx error rate (per BC KPIs)
- [ ] Frontend handles errors gracefully

---

#### Task 2.2: Rate Limiting Implementation

| Attribute | Value |
|-----------|-------|
| **Priority** | P1 |
| **Effort** | 2 days |
| **Primary Agent** | Backend-Coder |
| **Supporting Agents** | Auth-Integrator |

**Reference Specs:**
- Backend-Coder responsibilities: BC-08 (Performance & Scalability)
- Backend-Coder standing assumptions §7: "Rate-limit external API calls"

**Deliverables:**

1. **Backend Rate Limits** (`services/common/rate_limit.py`)
   - Install and configure `fastapi-limiter`
   - Per-user limits based on plan tier
   - Per-IP limits for unauthenticated endpoints
   - *Owner:* Backend-Coder

2. **Rate Limit Headers**
   - `X-RateLimit-Limit`
   - `X-RateLimit-Remaining`
   - `X-RateLimit-Reset`
   - *Owner:* Backend-Coder

3. **Frontend Handling**
   - Detect 429 responses
   - Show rate limit message to user
   - Display retry-after countdown
   - *Owner:* Frontend-Coder

**Acceptance Criteria:**
- [ ] Rate limits enforced by plan tier
- [ ] Headers present on all responses
- [ ] Frontend shows clear rate limit messaging

---

#### Task 2.3: Performance Optimization

| Attribute | Value |
|-----------|-------|
| **Priority** | P2 |
| **Effort** | 3 days |
| **Primary Agent** | Backend-Coder |
| **Supporting Agents** | Frontend-Coder, DevOps-Engineer |

**Reference Specs:**
- Backend-Coder KPIs: p95 latency <300ms
- Frontend-Coder KPIs: Lighthouse ≥90, FCP <2s
- Technical Debt: TD-01 (Timescale continuous aggregates)

**Deliverables:**

1. **Backend Optimization**
   - Redis caching for trends (5min TTL)
   - Database query indexing
   - Connection pooling configuration
   - Replace in-memory cache with Timescale (TD-01)
   - *Owner:* Backend-Coder

2. **Frontend Optimization**
   - React.memo for heavy components
   - List virtualization
   - Dynamic imports for code splitting
   - Image lazy loading
   - *Owner:* Frontend-Coder

3. **Performance Metrics**
   - Verify p95 API latency <300ms
   - Verify frontend CLS <0.1
   - Grafana dashboard for latency
   - *Owner:* DevOps-Engineer

**Acceptance Criteria:**
- [ ] P95 API latency <300ms (per agents.md §2)
- [ ] CLS <0.1 (per agents.md §2)
- [ ] Lighthouse performance ≥90 (per FC KPIs)

---

### Phase 3: Launch Preparation (Weeks 7-8)

---

#### Task 3.1: Security Audit

| Attribute | Value |
|-----------|-------|
| **Priority** | P0 |
| **Effort** | 2 days |
| **Primary Agent** | Architect |
| **Supporting Agents** | DevOps-Engineer, Backend-Coder |

**Reference Specs:**
- Architect responsibilities: AR-05 (Security & Compliance)
- DevOps-Engineer responsibilities: DO-06 (Security & Compliance)
- See [`agents.md`](./agents.md) §14 Compliance & Privacy

**Deliverables:**

1. **Security Review**
   - Input validation on all endpoints
   - SQL injection prevention verification
   - XSS protection in frontend
   - CSRF tokens for state-changing operations
   - *Owner:* Architect

2. **Secrets Audit**
   - Verify no secrets in code
   - Rotation schedule documented
   - Least-privilege access verified
   - *Owner:* DevOps-Engineer

3. **Vulnerability Scan**
   - Run Snyk/Trivy scans
   - Zero critical vulnerabilities
   - Generate SBOM
   - *Owner:* DevOps-Engineer

**Acceptance Criteria:**
- [ ] 0 critical vulnerabilities (per AR KPIs, DO KPIs)
- [ ] 100% secrets encrypted (per DO KPIs)
- [ ] OWASP Top 10 addressed
- [ ] Threat model documented (per AR-05)

---

#### Task 3.2: Documentation Completion

| Attribute | Value |
|-----------|-------|
| **Priority** | P1 |
| **Effort** | 2 days |
| **Primary Agent** | Docs-Writer |
| **Supporting Agents** | All agents |

**Reference Specs:**
- Docs-Writer responsibilities: DW-01 (User Documentation), DW-02 (Developer Documentation)
- Docs-Writer KPIs: 100% feature coverage

**Deliverables:**

1. **User Documentation** (`/docs/user/`)
   - Onboarding guide
   - Dashboard walkthrough
   - FAQ and troubleshooting
   - *Owner:* Docs-Writer

2. **Developer Documentation** (`/docs/api/`)
   - OpenAPI specification (maintained by Architect)
   - Integration guides
   - SDK examples
   - *Owner:* Docs-Writer

3. **Provider Guides**
   - Etsy connection guide
   - Printify connection guide
   - Stripe billing guide
   - *Owner:* Docs-Writer

4. **Changelog** (`/docs/changelog.md`)
   - Release notes
   - Breaking changes
   - Migration steps
   - *Owner:* Docs-Writer

**Acceptance Criteria:**
- [ ] 100% features documented (per DW KPIs)
- [ ] All guides tested with real user flows
- [ ] WCAG 2.1 AA compliance (per DW KPIs)

---

#### Task 3.3: Load Testing & Monitoring

| Attribute | Value |
|-----------|-------|
| **Priority** | P1 |
| **Effort** | 2 days |
| **Primary Agent** | DevOps-Engineer |
| **Supporting Agents** | QA-Automator, Backend-Coder |

**Reference Specs:**
- QA-Automator responsibilities: QA-02 (Performance Testing)
- DevOps-Engineer responsibilities: DO-05 (Monitoring & Alerting)
- Target: 2000 concurrent users, 10000 daily image jobs (agents.md §2)

**Deliverables:**

1. **Load Test Suite** (`/tests/perf/`)
   - k6 or Locust scripts
   - Test 2000 concurrent users
   - Test 10000 daily image generations
   - *Owner:* QA-Automator

2. **Grafana Dashboards** (`/infra/monitoring/`)
   - API latency (p50, p95, p99)
   - Error rates by service
   - Job queue depths
   - Database connections
   - *Owner:* DevOps-Engineer

3. **Alert Rules**
   - SLO breach alerts
   - Error budget burn
   - PagerDuty integration
   - *Owner:* DevOps-Engineer

**Acceptance Criteria:**
- [ ] Handle 2000 concurrent users (per agents.md §2)
- [ ] Handle 10000 daily image jobs (per agents.md §2)
- [ ] Dashboards show all key metrics
- [ ] Alerts trigger on SLO breach
- [ ] MTTR <30min (per DO KPIs)

---

## Technical Debt Register

Per [`agents.md`](./agents.md) §13:

| ID | Description | Priority | Owner Agent | Phase |
|----|-------------|----------|-------------|-------|
| TD-01 | Replace in-memory scraper cache with Timescale continuous aggregates | High | Data-Seeder | Phase 2 |
| TD-02 | Comprehensive error handling for Printify API | Medium | Integrations-Engineer | Phase 2 |
| TD-03 | Reduce GPT hallucinations in descriptions | Medium | AI-Engineer | Phase 3 |
| TD-04 | Pagination for trend signals API | Low | Backend-Coder | Phase 3 |

---

## Global Conventions

Per [`agents.md`](./agents.md) §8:

1. **Branch Naming:** `agent/<handle>/<issue-id>-<slug>` (e.g., `agent/backend/42-add-printify-client`)
2. **Commits:** Conventional Commits (`feat(api): add printify SKU endpoint`)
3. **Environment Variables:** Defined in `.env.example`; secrets via AWS SM or Vault
4. **CI Gates:** Pre-commit runs Black & isort (Python) or ESLint & Prettier (TS); unit coverage ≥90%; integration tests green; Snyk critical issues = 0
5. **Docker:** Multi-stage builds; image size <300MB; SBOM generated
6. **Docs:** Each PR updates relevant markdown or `/docs/changelog.md`

---

## Definition of Done

Per [`agents.md`](./agents.md) §17, a feature or PR is DONE when:

1. ✅ The corresponding story in the GitHub Project board is moved to **Done**
2. ✅ All automated checks pass: unit tests, integration tests, e2e tests, lint, security
3. ✅ Documentation, tests, and changelog are updated
4. ✅ Deployment to **staging** completes successfully and smoke tests pass
5. ✅ **Project-Manager Agent** merges to `main` and tags the release

---

## Post-MVP Roadmap

Per [`agents.md`](./agents.md) §12:

### Phase 1 (M4-M6): Stabilize & Enhance
- [ ] Bug backlog burndown
- [ ] A/B optimization for listings
- [ ] Scheduled product drops
- [ ] Enhanced social media posting

### Phase 2 (M7-M9): Scale & Collaborate
- [ ] Agency workspaces with team roles
- [ ] Community prompt pack marketplace
- [ ] Additional POD provider integrations
- [ ] Team analytics dashboard

### Phase 3 (M10-M12): Monetize & Expand
- [ ] Premium tier features
- [ ] Dynamic pricing advisor
- [ ] Shopify integration
- [ ] Amazon Merch integration

---

## Quick Start for Developers

### Prerequisites
- Python 3.11+ (per Backend-Coder §7)
- Node.js 18+ (per Frontend-Coder §1)
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
# Backend tests (per Unit-Tester)
pytest tests/ --cov

# Frontend tests (per Unit-Tester)
cd client && npm test

# E2E tests (per QA-Automator)
cd client && npx playwright test
```

---

## Escalation Path

Per agent specifications §6 (Failure Handling):

1. **Agent Blocked** → Retry once with clarified context
2. **Second Failure** → Create GitHub issue `blocker/*`, notify Architect
3. **Unresolved >24h** → Escalate to Project-Manager → CTO

---

## Appendix: File Structure

```
PODPusher/
├── agents.md                    # Master agent specification
├── agents_*.md                  # Individual agent specs (13 files)
├── services/                    # Backend microservices
│   ├── gateway/                # Main API gateway
│   ├── auth/                   # OAuth & sessions
│   ├── billing/                # Stripe billing (NEW)
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
│   ├── contexts/               # React contexts (NEW)
│   ├── services/               # API clients
│   └── locales/                # i18n translations
├── tests/                      # Python tests
│   └── e2e/                    # Playwright specs
├── alembic/                    # Database migrations
├── docs/                       # Documentation
│   ├── architecture.md
│   ├── i18n_plan.md
│   ├── oauth_flow_plan.md
│   └── internal_docs.md
└── scripts/                    # Utility scripts
```

---

*This plan follows the multi-agent workflow defined in [`agents.md`](./agents.md) and supersedes previous planning documents.*
