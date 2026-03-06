# PODPusher Task Breakdown

> **Sprint:** MVP Completion Sprint
> **Target:** Production-ready MVP
> **Authority:** Tasks assigned per agent specifications in [`agents.md`](./agents.md)

---

## Agent Quick Reference

| Agent | Spec File | Key Responsibilities |
|-------|-----------|---------------------|
| **PM** | `agents_project_manager.md` | Orchestration, PR merge, KPI tracking |
| **SW** | `agents_spec_writer.md` | Gherkin specs, acceptance criteria |
| **AR** | `agents_architect.md` | Design, OpenAPI, schemas, security |
| **BC** | `agents_backend_coder.md` | FastAPI, business logic, tests |
| **FC** | `agents_frontend_coder.md` | Next.js, components, i18n |
| **AU** | `agents_auth_integrator.md` | OAuth, tokens, RBAC |
| **AI** | `agents_ai_engineer.md` | Prompts, GPT, content safety |
| **DS** | `agents_data_seeder.md` | Scraping, ETL, trend data |
| **IN** | `agents_integrations_engineer.md` | Printify, Etsy, Stripe |
| **UT** | `agents_unit_tester.md` | PyTest, Jest, coverage |
| **QA** | `agents_qa_automator.md` | E2E, performance, a11y |
| **DO** | `agents_dev_ops_engineer.md` | CI/CD, infra, monitoring |
| **DW** | `agents_docs_writer.md` | User/dev docs, changelog |

---

## Phase 0: Critical MVP Blockers

### 0.1 OAuth UI Integration

**Primary Owner:** Frontend-Coder (FC)
**Supporting:** Auth-Integrator (AU), Unit-Tester (UT), QA-Automator (QA)
**Reference:** FC-05, AU-06

#### 0.1.1 Create OAuthConnect Component [FC]
- [x] Create `client/components/OAuthConnect.tsx`
- [x] Implement provider status fetching from backend
- [x] Add connect button with provider branding (logos)
- [x] Add disconnect button with confirmation modal
- [x] Show token expiry warnings (< 24h remaining)
- [x] Handle loading/error states gracefully

#### 0.1.2 Create Provider Context [FC]
- [x] Create `client/contexts/ProviderContext.tsx`
- [x] Track connected providers (Etsy, Printify, Stripe)
- [x] Expose `isConnected(provider)` helper
- [x] Auto-refresh status on mount

#### 0.1.3 Update Settings Page [FC]
- [x] Add "Connected Accounts" section to settings.tsx
- [x] Render OAuthConnect for each provider
- [x] Show connection status badges
- [x] Add "Manage Billing" link for Stripe

#### 0.1.4 Extend OAuth Service [FC]
- [x] Add `getProviderStatus()` to `client/services/oauth.ts`
- [x] Add `disconnectProvider()` function
- [x] Handle API errors with user-friendly messages

#### 0.1.5 Gate Generation Flows [FC]
- [x] Update generate.tsx to check provider connections
- [x] Show connection requirements before generation
- [x] Block publish if required providers disconnected

#### 0.1.6 Backend Token Refresh [AU]
- [x] Verify refresh token rotation in `services/auth/service.py`
- [x] Add background token pruning scheduler
- [x] Implement webhook ingestion for Stripe account updates

#### 0.1.7 Unit Tests [UT]
- [x] Test OAuthConnect component
- [x] Test ProviderContext
- [x] Test oauth.ts service functions
- [x] Ensure ≥90% coverage (per UT-02)

#### 0.1.8 E2E Tests [QA]
- [x] Create `tests/e2e/oauth_connect.spec.ts`
- [x] Test happy path: connect provider
- [x] Test disconnect flow
- [x] Test expired token warning
- [x] Test generation gating

---

### 0.2 Stripe Billing Integration

**Primary Owner:** Integrations-Engineer (IN)
**Supporting:** Backend-Coder (BC), Auth-Integrator (AU), Unit-Tester (UT)
**Reference:** IN-03, IN-07, BC-03

#### 0.2.1 Create Billing Service [IN]
- [x] Create `services/billing/__init__.py`
- [x] Create `services/billing/api.py` with FastAPI router
- [x] Create `services/billing/service.py` with billing logic
- [x] Create `services/billing/plans.py` with plan definitions

#### 0.2.2 Implement Webhook Handler [IN]
- [x] Create `services/billing/webhooks.py`
- [x] Handle `invoice.paid` - activate subscription
- [x] Handle `invoice.payment_failed` - notify user
- [x] Handle `customer.subscription.created` - set quotas
- [x] Handle `customer.subscription.updated` - update quotas
- [x] Handle `customer.subscription.deleted` - downgrade
- [x] Verify webhook signatures (per IN-07)

#### 0.2.3 Customer Portal Integration [IN]
- [x] Add `GET /api/billing/portal` endpoint
- [x] Generate Stripe portal session URL
- [x] Return redirect URL to frontend

#### 0.2.4 Link Billing to Quotas [BC]
- [x] Update `services/common/quotas.py`
- [x] Query user's plan tier from billing
- [x] Apply tier-specific limits
- [x] Handle overage scenarios (return 402 per AU-05)

#### 0.2.5 Mount in Gateway [BC]
- [x] Import billing router in `services/gateway/api.py`
- [x] Mount at `/api/billing`
- [x] Add health check for billing service

#### 0.2.6 Unit Tests [UT]
- [x] Create `tests/test_billing.py`
- [x] Create `tests/test_billing_webhooks.py`
- [x] Test webhook signature verification
- [x] Test quota updates on plan change
- [x] Ensure ≥90% coverage

---

## Phase 1: Core Experience Polish

### 1.1 i18n Expansion

**Primary Owner:** Frontend-Coder (FC)
**Supporting:** Docs-Writer (DW), QA-Automator (QA)
**Reference:** FC §7, `docs/i18n_plan.md`

#### 1.1.1 Audit Hard-coded Strings [FC]
- [x] Audit `client/pages/analytics.tsx` - extract strings
- [x] Audit `client/pages/bulk-upload.tsx` - extract strings
- [x] Audit `client/pages/notifications.tsx` - extract strings
- [x] Audit `client/pages/search.tsx` - extract strings
- [x] Audit `client/pages/settings.tsx` - extract strings
- [x] Audit `client/pages/ab_tests.tsx` - extract strings
- [x] Audit all components in `client/components/`

#### 1.1.2 Create Extraction Script [FC]
- [x] Create `scripts/i18n_extract.ts`
- [x] Scan for untranslated strings
- [x] Output missing keys to JSON
- [x] Add to npm scripts

#### 1.1.3 Expand Translations [FC + DW]
- [x] Add missing keys to `client/locales/en/common.json` [FC]
- [x] Add translations to `client/locales/es/common.json` [DW]
- [x] Create `client/locales/fr/common.json` [DW]
- [x] Create `client/locales/de/common.json` [DW]

#### 1.1.4 Implement ICU Formatting [FC]
- [x] Add `Intl.NumberFormat` wrapper utility
- [x] Update price displays to use formatter
- [x] Add locale metadata to API responses [BC]
- [x] Handle currency symbol placement by locale

#### 1.1.5 Update i18n Config [FC]
- [x] Add new locales to `next-i18next.config.js`
- [x] Update language switcher with new options
- [x] ~~Test RTL support~~ — Deferred (internal tool only, no Arabic/Hebrew needed)

#### 1.1.6 E2E Locale Tests [QA]
- [x] Update `tests/e2e/localization.spec.ts`
- [x] Test all pages with ES locale
- [x] Test all pages with FR locale
- [x] Test all pages with DE locale
- [x] Test currency formatting

---

### 1.2 Live Trend Scrapers

**Primary Owner:** Data-Seeder (DS)
**Supporting:** Backend-Coder (BC), Unit-Tester (UT), DevOps-Engineer (DO)
**Reference:** DS-01, DS-02, DS-06

#### 1.2.1 TikTok Scraper [DS]
- [x] Implement `scrape_tiktok()` in sources.py
- [x] Navigate to trending page
- [x] Extract hashtags and engagement counts
- [x] Handle rate limiting
- [x] Add retry logic with jitter

#### 1.2.2 Instagram Scraper [DS]
- [x] Implement `scrape_instagram()` in sources.py
- [x] Extract explore/trending content
- [x] Parse hashtag engagement
- [x] Handle login walls gracefully

#### 1.2.3 Twitter/X Scraper [DS]
- [x] Implement `scrape_twitter()` in sources.py
- [x] Extract trending topics
- [x] Get engagement metrics
- [x] Handle API changes

#### 1.2.4 Pinterest Scraper [DS]
- [x] Implement `scrape_pinterest()` in sources.py
- [x] Extract trending pins
- [x] Get category trends
- [x] Parse save/repin counts

#### 1.2.5 Etsy Trending Scraper [DS]
- [x] Implement `scrape_etsy_trending()` in sources.py
- [x] Extract trending searches
- [x] Get bestseller categories
- [x] Parse related trends

#### 1.2.6 Scraper Infrastructure [DS]
- [x] Add proxy rotation support
- [x] Implement circuit breaker pattern
- [x] Add scrape failure alerting
- [x] Create manual refresh endpoint [BC]

#### 1.2.7 Monitoring & Alerting [DO]
- [x] Add Prometheus metrics for scraping
- [x] Create Grafana dashboard for scrape health
- [x] Configure alerts for ≥5% failure rate
- [x] Document runbook for scraper outages

#### 1.2.8 Unit Tests [UT]
- [x] Create `tests/test_trend_scrapers.py`
- [x] Mock Playwright responses
- [x] Test error handling
- [x] Test normalization

---

### 1.3 Settings Page Polish

**Primary Owner:** Frontend-Coder (FC)
**Supporting:** Backend-Coder (BC)
**Reference:** FC-01, FC-03

#### 1.3.1 User Preferences [FC]
- [x] Add notification channel toggles (email/push)
- [x] Add default language selector
- [x] Add currency preference dropdown
- [x] Add timezone selector

#### 1.3.2 Social Configuration [FC]
- [x] Enhance SocialSettings component
- [x] Add Instagram handle input
- [x] Add TikTok handle input
- [x] Add Twitter handle input
- [x] Validate handle formats

#### 1.3.3 Quota Display [FC]
- [x] Enhance UserQuota component
- [x] Add visual progress bars
- [x] Show usage breakdown by resource type
- [x] Add "Upgrade" CTA button
- [x] Link upgrade to Stripe portal

#### 1.3.4 Backend Preferences API [BC]
- [x] Add preferences endpoints if missing
- [x] Validate preference values
- [x] Persist to database

---

## Phase 2: Enhanced Reliability

### 2.1 Error Handling

**Primary Owner:** Backend-Coder (BC)
**Supporting:** Frontend-Coder (FC), Integrations-Engineer (IN)
**Reference:** BC-04, IN-05, TD-02

#### 2.1.1 Standardize API Errors [BC]
- [x] Create `services/common/errors.py`
- [x] Define `APIError` Pydantic model
- [x] Create error code enum
- [x] Add request ID to all responses

#### 2.1.2 Printify Error Mapping [IN] (TD-02)
- [x] Map all Printify API error codes
- [x] Create user-friendly message templates
- [x] Add retry logic for transient errors
- [x] Implement circuit breaker

#### 2.1.3 Etsy Error Mapping [IN]
- [x] Map Etsy API error codes
- [x] Create user-friendly messages
- [x] Handle listing fee errors
- [x] Handle quota exceeded errors

#### 2.1.4 OpenAI Error Mapping [AI]
- [x] Map content policy errors
- [x] Map rate limit errors
- [x] Map token limit errors
- [x] Create user-friendly feedback

#### 2.1.5 Frontend Error Boundary [FC]
- [x] Create `client/components/ErrorBoundary.tsx`
- [x] Catch and display errors gracefully
- [x] Add "Try Again" action
- [x] Log errors to analytics

---

### 2.2 Rate Limiting

**Primary Owner:** Backend-Coder (BC)
**Supporting:** Auth-Integrator (AU), Frontend-Coder (FC)
**Reference:** BC-08, BC §7

#### 2.2.1 Backend Rate Limits [BC]
- [x] Install fastapi-limiter
- [x] Configure per-user limits by plan
- [x] Configure per-IP limits for public endpoints
- [x] Add rate limit headers

#### 2.2.2 External API Rate Limits [BC]
- [x] Implement aiolimiter for Etsy (10 req/s per BC §7)
- [x] Implement aiolimiter for Printify (5 req/s per BC §7)
- [x] Add retry with jitter

#### 2.2.3 Frontend Handling [FC]
- [x] Detect 429 responses
- [x] Show rate limit message to user
- [x] Display retry-after countdown

---

### 2.3 Performance

**Primary Owner:** Backend-Coder (BC)
**Supporting:** Frontend-Coder (FC), DevOps-Engineer (DO)
**Reference:** BC KPIs, FC KPIs, TD-01

#### 2.3.1 Backend Caching [BC]
- [x] Add Redis caching for trends (5min TTL)
- [x] Cache ideation results
- [x] Cache user quotas

#### 2.3.2 Database Optimization [BC] (TD-01)
- [x] Add proper indexes
- [x] Configure connection pooling
- [x] Replace in-memory cache with Timescale continuous aggregates
- [x] Profile slow queries

#### 2.3.3 Frontend Optimization [FC]
- [x] Add React.memo to heavy components
- [x] Implement list virtualization
- [x] Add dynamic imports for code splitting
- [x] Optimize image loading

#### 2.3.4 Performance Monitoring [DO]
- [x] Create Grafana dashboard for latency
- [x] Add p50, p95, p99 metrics
- [x] Configure alerts for latency regression

---

## Phase 3: Launch Preparation

### 3.1 Security Audit

**Primary Owner:** Architect (AR)
**Supporting:** DevOps-Engineer (DO), Backend-Coder (BC)
**Reference:** AR-05, DO-06, `agents.md` §14

#### 3.1.1 Input Validation [AR + BC]
- [ ] Audit all endpoint inputs
- [ ] Verify Pydantic validation
- [ ] Check for SQL injection
- [ ] Check for XSS

#### 3.1.2 Authentication Review [AR + AU]
- [ ] Verify token validation
- [ ] Check CSRF protection
- [ ] Audit session management
- [ ] Review RBAC implementation

#### 3.1.3 Secrets Audit [DO]
- [ ] Scan codebase for secrets
- [ ] Verify .env.example completeness
- [ ] Document rotation schedule
- [ ] Verify encryption at rest

#### 3.1.4 Vulnerability Scan [DO]
- [ ] Run Snyk scan
- [ ] Run Trivy container scan
- [ ] Generate SBOM
- [ ] Fix critical vulnerabilities

#### 3.1.5 Threat Model [AR]
- [ ] Create STRIDE analysis
- [ ] Document trust boundaries
- [ ] Update `/docs/SECURITY.md`

---

### 3.2 Documentation

**Primary Owner:** Docs-Writer (DW)
**Supporting:** All agents
**Reference:** DW-01, DW-02, DW-03

#### 3.2.1 User Documentation [DW]
- [ ] Write onboarding guide
- [ ] Write dashboard walkthrough
- [ ] Create FAQ document
- [ ] Write troubleshooting guide

#### 3.2.2 Developer Documentation [DW]
- [ ] Update OpenAPI documentation [AR]
- [ ] Write integration guides
- [ ] Add SDK examples
- [ ] Document environment setup

#### 3.2.3 Provider Guides [DW]
- [ ] Write Etsy connection guide
- [ ] Write Printify connection guide
- [ ] Write Stripe billing guide

#### 3.2.4 Release Notes [DW]
- [ ] Update `/docs/changelog.md`
- [ ] Document breaking changes
- [ ] Add migration steps

---

### 3.3 Load Testing

**Primary Owner:** DevOps-Engineer (DO)
**Supporting:** QA-Automator (QA), Backend-Coder (BC)
**Reference:** QA-02, DO-05, `agents.md` §2

#### 3.3.1 Create Test Suite [QA]
- [ ] Create k6 load test scripts
- [ ] Test trend scraping endpoint
- [ ] Test idea generation endpoint
- [ ] Test image generation endpoint
- [ ] Test listing publish endpoint

#### 3.3.2 Run Load Tests [QA]
- [ ] Test 500 concurrent users
- [ ] Test 1000 concurrent users
- [ ] Test 2000 concurrent users
- [ ] Test 10000 daily image jobs

#### 3.3.3 Monitoring Setup [DO]
- [ ] Create Grafana dashboards
- [ ] Configure SLO alerts
- [ ] Set up PagerDuty integration
- [ ] Document runbooks

---

## Technical Debt

### TD-01: Timescale Continuous Aggregates [DS + BC]
- [x] Design aggregate schema
- [x] Migrate from in-memory cache
- [ ] Update trend queries
- [ ] Test performance improvement

### TD-02: Printify Error Handling [IN]
- [ ] Map all Printify error codes
- [ ] Add retry logic for transient errors
- [ ] Add circuit breaker
- [ ] Create user-friendly messages

### TD-03: GPT Hallucination Reduction [AI]
- [ ] Add output validation
- [ ] Implement content filters
- [ ] Add user feedback mechanism
- [ ] Tune prompts based on feedback

### TD-04: Trend Signals Pagination [BC]
- [ ] Add cursor-based pagination
- [ ] Update API endpoints
- [ ] Update frontend components
- [ ] Add pagination tests

---

## Completion Tracking

| Phase | Tasks | Agent | Completed | Progress |
|-------|-------|-------|-----------|----------|
| Phase 0.1 | 8 | FC, AU, UT, QA | 8 | 100% |
| Phase 0.2 | 6 | IN, BC, UT | 6 | 100% |
| Phase 1.1 | 6 | FC, DW, QA | 6 | 100% |
| Phase 1.2 | 8 | DS, BC, UT, DO | 8 | 100% |
| Phase 1.3 | 4 | FC, BC | 4 | 100% |
| Phase 2.1 | 5 | BC, FC, IN, AI | 5 | 100% |
| Phase 2.2 | 3 | BC, AU, FC | 3 | 100% |
| Phase 2.3 | 4 | BC, FC, DO | 4 | 100% |
| Phase 3.1 | 5 | AR, DO, BC, AU | 0 | 0% |
| Phase 3.2 | 4 | DW, AR | 0 | 0% |
| Phase 3.3 | 3 | DO, QA | 0 | 0% |
| Tech Debt | 4 | DS, BC, IN, AI | 1 | 25% |
| **Total** | **60** | | **49** | **82%** |

---

## Agent Workload Summary

| Agent | Task Count | Priority Tasks |
|-------|------------|----------------|
| Frontend-Coder (FC) | 18 | OAuth UI, i18n, Settings |
| Backend-Coder (BC) | 12 | Billing quotas, Rate limiting, Performance |
| Integrations-Engineer (IN) | 8 | Stripe billing, Error mapping |
| Data-Seeder (DS) | 7 | Live scrapers, TD-01 |
| Unit-Tester (UT) | 6 | All test coverage |
| QA-Automator (QA) | 5 | E2E tests, Load tests |
| DevOps-Engineer (DO) | 6 | Monitoring, Security scan, Infra |
| Auth-Integrator (AU) | 3 | Token refresh, RBAC review |
| Docs-Writer (DW) | 5 | Translations, User docs |
| Architect (AR) | 4 | Security audit, OpenAPI |
| AI-Engineer (AI) | 2 | Error mapping, TD-03 |

---

## Escalation Contacts

Per agent specifications §6:

1. **First escalation:** Architect
2. **Second escalation:** Project-Manager
3. **Critical security:** DevOps-Engineer + CTO
4. **Unresolved >24h:** CTO

---

*Last Updated: February 2026*
*Follows [`agents.md`](./agents.md) multi-agent workflow*
