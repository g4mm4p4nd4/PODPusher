# PODPusher Task Breakdown

> **Sprint:** MVP Completion Sprint
> **Target:** Production-ready MVP

---

## Phase 0: Critical MVP Blockers

### 0.1 OAuth UI Integration

#### 0.1.1 Create OAuthConnect Component
- [ ] Create `client/components/OAuthConnect.tsx`
- [ ] Implement provider status fetching from backend
- [ ] Add connect button with provider branding (logos)
- [ ] Add disconnect button with confirmation modal
- [ ] Show token expiry warnings (< 24h remaining)
- [ ] Handle loading/error states gracefully

#### 0.1.2 Create Provider Context
- [ ] Create `client/contexts/ProviderContext.tsx`
- [ ] Track connected providers (Etsy, Printify, Stripe)
- [ ] Expose `isConnected(provider)` helper
- [ ] Auto-refresh status on mount

#### 0.1.3 Update Settings Page
- [ ] Add "Connected Accounts" section to settings.tsx
- [ ] Render OAuthConnect for each provider
- [ ] Show connection status badges
- [ ] Add "Manage Billing" link for Stripe

#### 0.1.4 Extend OAuth Service
- [ ] Add `getProviderStatus()` to `client/services/oauth.ts`
- [ ] Add `disconnectProvider()` function
- [ ] Handle API errors with user-friendly messages

#### 0.1.5 Gate Generation Flows
- [ ] Update generate.tsx to check provider connections
- [ ] Show connection requirements before generation
- [ ] Block publish if required providers disconnected

#### 0.1.6 Add E2E Tests
- [ ] Create `tests/e2e/oauth_connect.spec.ts`
- [ ] Test happy path: connect provider
- [ ] Test disconnect flow
- [ ] Test expired token warning
- [ ] Test generation gating

---

### 0.2 Stripe Billing Integration

#### 0.2.1 Create Billing Service
- [ ] Create `services/billing/__init__.py`
- [ ] Create `services/billing/api.py` with FastAPI router
- [ ] Create `services/billing/service.py` with billing logic
- [ ] Create `services/billing/plans.py` with plan definitions

#### 0.2.2 Implement Webhook Handler
- [ ] Create `services/billing/webhooks.py`
- [ ] Handle `invoice.paid` - activate subscription
- [ ] Handle `invoice.payment_failed` - notify user
- [ ] Handle `customer.subscription.created` - set quotas
- [ ] Handle `customer.subscription.updated` - update quotas
- [ ] Handle `customer.subscription.deleted` - downgrade
- [ ] Verify webhook signatures

#### 0.2.3 Customer Portal Integration
- [ ] Add `GET /api/billing/portal` endpoint
- [ ] Generate Stripe portal session URL
- [ ] Return redirect URL to frontend

#### 0.2.4 Link Billing to Quotas
- [ ] Update `services/common/quotas.py`
- [ ] Query user's plan tier from billing
- [ ] Apply tier-specific limits
- [ ] Handle overage scenarios

#### 0.2.5 Mount in Gateway
- [ ] Import billing router in `services/gateway/api.py`
- [ ] Mount at `/api/billing`
- [ ] Add health check for billing service

#### 0.2.6 Add Tests
- [ ] Create `tests/test_billing.py`
- [ ] Create `tests/test_billing_webhooks.py`
- [ ] Test webhook signature verification
- [ ] Test quota updates on plan change

---

## Phase 1: Core Experience Polish

### 1.1 i18n Expansion

#### 1.1.1 Audit Hard-coded Strings
- [ ] Audit `client/pages/analytics.tsx` - extract strings
- [ ] Audit `client/pages/bulk-upload.tsx` - extract strings
- [ ] Audit `client/pages/notifications.tsx` - extract strings
- [ ] Audit `client/pages/search.tsx` - extract strings
- [ ] Audit `client/pages/settings.tsx` - extract strings
- [ ] Audit `client/pages/ab_tests.tsx` - extract strings
- [ ] Audit all components in `client/components/`

#### 1.1.2 Create Extraction Script
- [ ] Create `scripts/i18n_extract.ts`
- [ ] Scan for untranslated strings
- [ ] Output missing keys to JSON
- [ ] Add to npm scripts

#### 1.1.3 Expand Translations
- [ ] Add missing keys to `client/locales/en/common.json`
- [ ] Add translations to `client/locales/es/common.json`
- [ ] Create `client/locales/fr/common.json`
- [ ] Create `client/locales/de/common.json`

#### 1.1.4 Implement ICU Formatting
- [ ] Add `Intl.NumberFormat` wrapper utility
- [ ] Update price displays to use formatter
- [ ] Add locale metadata to API responses
- [ ] Handle currency symbol placement by locale

#### 1.1.5 Update i18n Config
- [ ] Add new locales to `next-i18next.config.js`
- [ ] Update language switcher with new options
- [ ] Test RTL support (future Arabic/Hebrew)

#### 1.1.6 Expand E2E Tests
- [ ] Update `tests/e2e/localization.spec.ts`
- [ ] Test all pages with ES locale
- [ ] Test currency formatting
- [ ] Test language persistence

---

### 1.2 Live Trend Scrapers

#### 1.2.1 TikTok Scraper
- [ ] Implement `scrape_tiktok()` in sources.py
- [ ] Navigate to trending page
- [ ] Extract hashtags and engagement counts
- [ ] Handle rate limiting
- [ ] Add retry logic

#### 1.2.2 Instagram Scraper
- [ ] Implement `scrape_instagram()` in sources.py
- [ ] Extract explore/trending content
- [ ] Parse hashtag engagement
- [ ] Handle login walls gracefully

#### 1.2.3 Twitter/X Scraper
- [ ] Implement `scrape_twitter()` in sources.py
- [ ] Extract trending topics
- [ ] Get engagement metrics
- [ ] Handle API changes

#### 1.2.4 Pinterest Scraper
- [ ] Implement `scrape_pinterest()` in sources.py
- [ ] Extract trending pins
- [ ] Get category trends
- [ ] Parse save/repin counts

#### 1.2.5 Etsy Trending Scraper
- [ ] Implement `scrape_etsy_trending()` in sources.py
- [ ] Extract trending searches
- [ ] Get bestseller categories
- [ ] Parse related trends

#### 1.2.6 Scraper Infrastructure
- [ ] Add proxy rotation support
- [ ] Implement circuit breaker pattern
- [ ] Add scrape failure alerting
- [ ] Create manual refresh endpoint

#### 1.2.7 Add Tests
- [ ] Create `tests/test_trend_scrapers.py`
- [ ] Mock Playwright responses
- [ ] Test error handling
- [ ] Test normalization

---

### 1.3 Settings Page Polish

#### 1.3.1 User Preferences
- [ ] Add notification channel toggles (email/push)
- [ ] Add default language selector
- [ ] Add currency preference dropdown
- [ ] Add timezone selector

#### 1.3.2 Social Configuration
- [ ] Enhance SocialSettings component
- [ ] Add Instagram handle input
- [ ] Add TikTok handle input
- [ ] Add Twitter handle input
- [ ] Validate handle formats

#### 1.3.3 Quota Display
- [ ] Enhance UserQuota component
- [ ] Add visual progress bars
- [ ] Show usage breakdown by resource type
- [ ] Add "Upgrade" CTA button
- [ ] Link upgrade to Stripe portal

---

## Phase 2: Enhanced Reliability

### 2.1 Error Handling

#### 2.1.1 Standardize API Errors
- [ ] Create `services/common/errors.py`
- [ ] Define `APIError` Pydantic model
- [ ] Create error code enum
- [ ] Add request ID to all responses

#### 2.1.2 Provider Error Mapping
- [ ] Map Printify error codes
- [ ] Map Etsy error codes
- [ ] Map OpenAI content policy errors
- [ ] Create user-friendly message templates

#### 2.1.3 Frontend Error Boundary
- [ ] Create `client/components/ErrorBoundary.tsx`
- [ ] Catch and display errors gracefully
- [ ] Add "Try Again" action
- [ ] Log errors to analytics

---

### 2.2 Rate Limiting

#### 2.2.1 Backend Rate Limits
- [ ] Install fastapi-limiter
- [ ] Configure per-user limits by plan
- [ ] Configure per-IP limits for public endpoints
- [ ] Add rate limit headers

#### 2.2.2 Frontend Handling
- [ ] Detect 429 responses
- [ ] Show rate limit message to user
- [ ] Display retry-after countdown

---

### 2.3 Performance

#### 2.3.1 Backend Optimization
- [ ] Add Redis caching for trends (5min TTL)
- [ ] Add database query indexes
- [ ] Configure connection pooling
- [ ] Profile slow endpoints

#### 2.3.2 Frontend Optimization
- [ ] Add React.memo to heavy components
- [ ] Implement list virtualization
- [ ] Add dynamic imports for code splitting
- [ ] Optimize image loading

---

## Phase 3: Launch Preparation

### 3.1 Security Audit
- [ ] Validate all user inputs
- [ ] Verify SQL injection protection
- [ ] Test XSS prevention
- [ ] Add CSRF tokens
- [ ] Audit secret storage
- [ ] Run Snyk vulnerability scan

### 3.2 Documentation
- [ ] Write user onboarding guide
- [ ] Generate OpenAPI documentation
- [ ] Write Etsy connection guide
- [ ] Write Printify connection guide
- [ ] Create FAQ document
- [ ] Document environment variables

### 3.3 Load Testing
- [ ] Create k6 or Locust test suite
- [ ] Test 2000 concurrent users
- [ ] Test 10000 daily image generations
- [ ] Identify bottlenecks
- [ ] Configure Grafana dashboards
- [ ] Set up alert rules

---

## Technical Debt

### TD-01: Timescale Continuous Aggregates
- [ ] Design aggregate schema
- [ ] Migrate from in-memory cache
- [ ] Update trend queries
- [ ] Test performance improvement

### TD-02: Printify Error Handling
- [ ] Map all Printify error codes
- [ ] Add retry logic for transient errors
- [ ] Add circuit breaker
- [ ] Create user-friendly messages

### TD-03: GPT Hallucination Reduction
- [ ] Add output validation
- [ ] Implement content filters
- [ ] Add user feedback mechanism
- [ ] Tune prompts based on feedback

### TD-04: Trend Signals Pagination
- [ ] Add cursor-based pagination
- [ ] Update API endpoints
- [ ] Update frontend components
- [ ] Add pagination tests

---

## Completion Tracking

| Phase | Tasks | Completed | Progress |
|-------|-------|-----------|----------|
| Phase 0 | 12 | 0 | 0% |
| Phase 1 | 21 | 0 | 0% |
| Phase 2 | 11 | 0 | 0% |
| Phase 3 | 14 | 0 | 0% |
| **Total** | **58** | **0** | **0%** |

---

*Last Updated: January 2026*
