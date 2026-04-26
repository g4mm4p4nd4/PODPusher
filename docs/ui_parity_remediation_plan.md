# PODPusher UI Parity Remediation Plan

This plan converts the wireframe audit into build-ready workstreams. It is written so multiple agents can work in parallel without colliding.

## Current Baseline

Implemented:

- Dark internal control center shell with left nav, top search, store/language/admin controls, quota rail, and dense panels.
- Aggregate APIs and read models for overview, trends, seasonal events, niches, search, composer, A/B tests, notifications, and settings.
- Provenance metadata on aggregate responses.
- Persistence for brand profiles, saved niches, saved searches, watchlist items, seasonal saves, notification rules, listing draft revisions, listing optimization rows, A/B actions, and settings dashboard data.

Known limitation:

- Browser screenshot/e2e validation is blocked until Playwright Chromium is installed inside an approved workspace path.

## Workstream A: Shell, Global Filters, and Visual System

Owner: frontend worker.

Owns:

- `client/components/Layout.tsx`
- `client/components/ControlCenter.tsx`
- shared page-level filter/date components
- shared drawer/detail/action components
- page imports of shared components

Requirements:

- Replace text abbreviation nav marks with proper icon buttons or a consistent icon system.
- Add a reusable global date range control matching the wireframes.
- Add query-param support for global date range, store, marketplace, country, language, category, and search where applicable.
- Add reusable action bar and drawer/detail panel components for row/card drilldowns.
- Add first-class loading, empty, error, disabled, and success states to shared components.
- Preserve dense internal-tool desktop layout; mobile may stack but must not overlap.

Acceptance criteria:

- Every wireframe page can render the shared date filter or intentionally opt out.
- All shared filters can initialize from and write to query params.
- All primary action buttons have disabled/loading/success states.
- Unit tests cover shell navigation, global search deep link, date filter query state, and shared panel states.

## Workstream B: Data Contracts, Provenance, and Mutations

Owner: backend worker.

Owns:

- `services/control_center/service.py`
- aggregate API modules under `services/dashboard`, `services/seasonal`, `services/niches`, `services/settings`
- existing APIs under `services/search`, `services/listing_composer`, `services/ab_tests`, `services/notifications`
- `services/models.py`
- Alembic migrations
- API tests

Requirements:

- Ensure every page filter accepted by the UI is accepted by the corresponding endpoint.
- Add explicit response fields for `actions_available`, `integration_status`, and `next_drilldowns` where pages expose row/card actions.
- Add mutation endpoints for currently inert actions: composer publish queue, export, search generate tags, A/B create test, notification schedule management, settings save, invite user, and brand profile create/update.
- Keep credential-backed Etsy, Printify, Stripe, OpenAI, Slack, and marketplace flows non-blocking with visible status and fallback data.
- Preserve `source`, `is_estimated`, `updated_at`, and `confidence` on every metric-like value.

Acceptance criteria:

- API smoke returns `200` for all dashboard endpoints and all mutation endpoints.
- Missing credentials never break dashboard rendering.
- Tests prove filters affect returned data or response metadata.
- Tests prove saved/mutated entities persist or return a clearly labeled demo state.

## Workstream C: Overview, Trends, and Seasonal Events

Owner: page slice worker.

Owns:

- `client/pages/index.tsx`
- `client/pages/trends.tsx`
- `client/pages/seasonal-events.tsx`
- related service client methods and tests

Requirements:

- Overview: add date range control, clickable cards, clickable recent drafts, event drilldowns, and category drilldowns.
- Trends: add date range and more-filters control; wire Export CSV; add keyword row actions for save, send/use in composer, watch, and tag cluster add.
- Trends: design idea cards need `Use in Composer` handoff that pre-fills composer context.
- Seasonal: expose category and horizon filters; add month navigation, Today button, priority legend, richer event detail drawer, and save state.
- Seasonal: selected event detail must include recommended keywords, category demand, niche angles, launch window, listing count opportunity, and saved status.

Acceptance criteria:

- Filter changes call endpoints with matching params and update visible data.
- Every row/card action either mutates state or opens a drilldown.
- Discover-to-composer from trends and seasonal events pre-fills composer.
- Component tests cover filter changes, selected detail state, and at least two row actions.

## Workstream D: Niche Suggestions, Search, and Composer Handoffs

Owner: workflow handoff worker.

Owns:

- `client/pages/niches.tsx`
- `client/pages/search.tsx`
- `client/components/ListingComposer.tsx`
- `client/pages/listing-composer.tsx`
- `client/services/controlCenter.ts`
- `client/services/listings.ts`

Requirements:

- Niche profile must include tone, audience, interests, banned topics, and preferred products.
- Niche actions must support Save Niche, Create Listing, and Start A/B Test.
- Search must include category, rating, price band, marketplace, season, and niche filters.
- Search actions must support Add to Watchlist, Send to Composer, Generate Tags, compare selected items, save search, and recent query reuse.
- Composer must consume query params from niches/search/trends/seasonal handoffs and prefill niche, keyword, product type, tags, and audience where available.
- Composer metadata fields must match the wireframe: materials, occasion, holiday, recipient, and style.

Acceptance criteria:

- `/listing-composer?niche=...&keyword=...` pre-fills the composer.
- Watchlist, saved search, saved niche, and profile saves call real endpoints and show success/error states.
- Start A/B Test from a niche/search result opens or preloads the A/B creation flow.
- Tests cover niche-to-composer, search-to-watchlist, search-to-composer, and query-prefill behavior.

## Workstream E: Composer Publish Queue and Export

Owner: integration/API worker with frontend support.

Owns:

- composer endpoints and service layer
- listing draft revision/optimization persistence
- publish queue API and UI state
- export endpoint/UI action

Requirements:

- `Publish Queue` must create a queued listing job or an explicit demo queue item.
- `Export` must return a downloadable JSON/CSV payload or document why export is disabled.
- Composer score and compliance should refresh after generation, save, and relevant edits.
- Publish queue must show pending/success/error state and retain draft ID.

Acceptance criteria:

- Publish queue mutation persists an automation/listing job record or deterministic demo record.
- Export returns a file payload with title, description, tags, metadata, score, compliance, and provenance.
- Tests cover publish queue success/failure and export payload shape.

## Workstream F: A/B Testing Lab

Owner: A/B feature worker.

Owns:

- `client/pages/ab-tests.tsx`
- `services/ab_tests/*`
- A/B model/migration updates if needed

Requirements:

- Add wired Create A/B Test flow with product selector, variable type, variants, traffic split, and create endpoint.
- Add table filters for search, status, and date range.
- Add variant A/B detail visualization and winner confidence details.
- Push Winner to Listing must update winner status or return explicit demo-state metadata.

Acceptance criteria:

- Create A/B Test creates an experiment bound to a product/listing.
- Pause, duplicate, end, and push winner actions update visible state.
- Tests cover create, action mutation, and selected experiment detail.

## Workstream G: Notifications, Scheduler, Settings, and Localization

Owner: operations/settings worker.

Owns:

- `client/pages/notifications.tsx`
- `client/pages/settings.tsx`
- `services/notifications/*`
- `services/settings/*`
- user/settings/preference APIs as needed

Requirements:

- Notifications: wire Manage Schedules, schedule creation/editing, active alert toggle, channel preferences, and Slack placeholder status.
- Notifications: weekly timeline should match the reference grid closely enough to inspect jobs by day/time.
- Settings: tabs must scope content instead of showing everything at once.
- Settings: localization fields must be editable and saved.
- Settings: brand profiles must support create/edit/default active profile.
- Settings: integrations must expose connect/configure status without breaking when credentials are absent.
- Settings: quotas must drill into usage ledger details.
- Settings: users/roles must support invite, role change, status, and permissions display.

Acceptance criteria:

- Save Changes persists localization/settings changes.
- Manage Schedules creates or edits scheduled jobs.
- Slack configure remains a visible non-blocking placeholder unless credentials exist.
- Tests cover settings tab switching, localization save, schedule rule save, and notification preferences.

## Workstream H: QA, Visual Evidence, and Regression Coverage

Owner: QA worker.

Owns:

- Jest/component tests
- backend API tests
- Playwright/e2e flows
- screenshot evidence
- final parity matrix

Requirements:

- Re-run the UI parity audit matrix after implementation.
- Add e2e flows:
  - discover trend to composer
  - niche to listing
  - search to watchlist
  - search to generated tags
  - create A/B test
  - push winner to listing
  - schedule alert
  - settings localization update
- Capture desktop screenshots for every route when Playwright browser dependencies are available.

Acceptance criteria:

- Backend tests pass.
- Frontend typecheck passes.
- Frontend tests pass.
- Build passes.
- E2E either passes or documents the exact environment blocker.
- Final audit matrix has no P0 gaps.

## Standard Agent Prompt

Use this prompt for each worker, replacing bracketed fields.

```text
You are the [workstream] implementation agent for PODPusher UI parity.

Goal:
Bring [screens/features] to parity with the commissioned wireframes and docs/ui_parity_remediation_plan.md.

Read first:
- AGENTS.md
- docs/ui_parity_remediation_plan.md
- UI_Samples/[relevant screenshots]
- [owned frontend files]
- [owned backend files]
- [owned tests]

Strict scope:
- You own [file paths/modules].
- You do not own [file paths/modules].
- Do not revert unrelated changes.
- Keep Etsy, Printify, Stripe, OpenAI, Slack, and marketplace credentials non-blocking.

Functional requirements:
- Implement the controls, panels, actions, drilldowns, and states listed in your workstream.
- Every primary action must either mutate real state or show an explicit unavailable/demo state.
- Every cross-page handoff must transfer context through query params, IDs, or saved state.

Backend/API requirements:
- Add or update endpoints, models, migrations, and service-layer functions as needed.
- Include provenance on estimated or externally sourced values.
- Add fallback integration status when credentials are missing.

Tests:
- Add/update backend, frontend, and e2e tests listed in your workstream.
- Run the relevant commands and report exact results.

Definition of done:
- All acceptance criteria for your workstream pass.
- The final response lists changed files, validation commands, and remaining blockers.
```

## Integration Order

1. Workstream B first when new API contracts are needed.
2. Workstream A can run in parallel if it only edits shared UI primitives.
3. Workstreams C, D, F, and G run after or alongside their needed data contracts.
4. Workstream E should run after composer query-prefill exists.
5. Workstream H runs last and updates the final parity matrix.
