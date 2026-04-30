# PODPusher UI Parity Final Audit Matrix

Audit date: 2026-04-26
Worker: Codex UI parity continuation from `66cf8d5` on `main`

## Scope And Evidence

This pass remediated the remaining parity gaps called out in the prior matrix: composer first paint, product/design visual assets, analytic density, settings density, and `datetime.utcnow()` warning hygiene. The follow-up trend evidence pass replaces Trends-page demo visuals with source-backed market evidence when public examples are available, and hands that evidence into the Listing Composer. Credential-backed Etsy, Printify, Stripe, OpenAI, Slack, and marketplace flows remain non-blocking and explicitly labeled through demo/local or fallback states. Metric provenance fields remain preserved in API payloads and UI surfaces: `source`, `is_estimated`, `updated_at`, and `confidence`.

Runtime evidence was refreshed with the rebuilt app served at `http://localhost:3100`, Playwright Chromium from `/mnt/d/Users/Bear/.codex-data/playwright-browsers`, and route screenshots under `output/playwright/ui-parity/`.

## Validation Results

| Command | Result | Notes |
| --- | --- | --- |
| `TMPDIR=/mnt/d/Users/Bear/.codex-data/tmp PYTHONPYCACHEPREFIX=/mnt/d/Users/Bear/.codex-data/pycache python -m pytest -s -q` | Pass | 306 passed, 2 skipped in 22m50s. Direct `datetime.utcnow()` calls are removed from `services/` and `tests/`. |
| `flake8` | Pass | No lint output after removing the stale settings import. |
| `python scripts/verify_translations.py` | Pass | All translation files contain the base keys. |
| `npm exec --prefix client tsc -- --noEmit --project client/tsconfig.json` | Pass | No TypeScript errors. |
| `npm test --prefix client -- --runInBand --cacheDirectory=/mnt/d/Users/Bear/.codex-data/jest-cache` | Pass | 27 suites, 85 tests passed. |
| `npm run build --prefix client` | Pass | Next.js build succeeded and generated 91 static pages; Browserslist emitted a stale-data notice only. |
| `PLAYWRIGHT_BROWSERS_PATH=/mnt/d/Users/Bear/.codex-data/playwright-browsers PLAYWRIGHT_SKIP_WEB_SERVER=1 client/node_modules/.bin/playwright test --config=output/playwright/ui-parity/playwright.capture.config.ts --reporter=line` | Pass | 9/9 route screenshots captured at 1448x1086. |
| `PLAYWRIGHT_BROWSERS_PATH=/mnt/d/Users/Bear/.codex-data/playwright-browsers PLAYWRIGHT_SKIP_WEB_SERVER=1 client/node_modules/.bin/playwright test tests/e2e/ui_routes.spec.ts tests/e2e/discover_to_composer.spec.ts tests/e2e/search.spec.ts tests/e2e/ab_tests.spec.ts tests/e2e/notifications.spec.ts tests/e2e/localization.spec.ts --workers=1 --reporter=line` | Pass | 22/22 targeted browser e2e tests passed after updating the settings localization spec for the new overview tab. |
| `docker exec podpusher-frontend-1 npm test -- --runTestsByPath __tests__/ListingComposer.test.tsx __tests__/listingsService.test.ts --runInBand` | Pass | 16/16 focused composer activity and listings service tests passed. |
| `docker compose run --rm --no-deps -e DATABASE_URL=sqlite+aiosqlite:////app/listing-composer-test.db gateway python -m pytest tests/test_listing_composer_api.py -q` | Pass | 5/5 isolated listing composer API tests passed with draft pagination, history, queue filtering, export provenance, and non-blocking credential-gated publish status. |
| `PLAYWRIGHT_BROWSERS_PATH=/mnt/d/Users/Bear/.codex-data/playwright-browsers PLAYWRIGHT_SKIP_WEB_SERVER=1 client/node_modules/.bin/playwright test tests/e2e/listings.spec.ts tests/e2e/listing_draft.spec.ts --workers=1 --reporter=line` | Pass | 5/5 browser tests passed for draft persistence, query handoff, publish queue/export, queue filtering, and activity pagination. |
| `PLAYWRIGHT_BROWSERS_PATH=/mnt/d/Users/Bear/.codex-data/playwright-browsers PLAYWRIGHT_SKIP_WEB_SERVER=1 client/node_modules/.bin/playwright test --config=output/playwright/ui-parity/playwright.capture.config.ts --grep "capture /listing-composer" --reporter=line` | Pass | Refreshed `output/playwright/ui-parity/listing-composer.png` for the persisted composer activity panels. |
| `docker exec podpusher-frontend-1 npm exec tsc -- --noEmit --project tsconfig.json` | Pass | Focused TypeScript check after market-evidence UI wiring. |
| `docker exec podpusher-frontend-1 npm test -- --runTestsByPath __tests__/trendsPage.test.tsx __tests__/ListingComposer.test.tsx --runInBand` | Pass | 13/13 focused tests passed for Trends market evidence and Composer evidence handoff. |
| `docker run --rm --network podpusher_default -v /mnt/d/Users/Bear/Documents/GitHub/PODPusher:/app -w /app -e PYTHONDONTWRITEBYTECODE=1 -e DATABASE_URL=sqlite+aiosqlite:///./.codex-trend-tests.db podpusher-gateway python -m pytest -p no:cacheprovider tests/test_trend_ingestion_service.py tests/test_trend_ingestion_api.py tests/test_control_center_api.py tests/test_listing_composer_api.py -q` | Pass | 26/26 focused backend/API tests passed for persisted market examples, insight strategy payloads, draft evidence metadata, and non-blocking credential statuses. |
| `PLAYWRIGHT_BROWSERS_PATH=/mnt/d/Users/Bear/.codex-data/playwright-browsers client/node_modules/.bin/playwright test tests/e2e/discover_to_composer.spec.ts --workers=1 --reporter=line` | Pass | 3/3 browser tests passed, including trend evidence handoff into Composer. |
| `PLAYWRIGHT_BROWSERS_PATH=/mnt/d/Users/Bear/.codex-data/playwright-browsers PLAYWRIGHT_SKIP_WEB_SERVER=1 client/node_modules/.bin/playwright test --config=output/playwright/ui-parity/playwright.capture.config.ts --grep "capture /(trends|listing-composer)" --reporter=line` | Pass | Refreshed Trends and Listing Composer parity screenshots. |

## Screen Matrix

| Screen | Current Implementation | Evidence | Status |
| --- | --- | --- | --- |
| Global shell | Dense dark dashboard shell with nav, search, store/market/country/language/date controls, admin identity, and quota rail. Header fits the 1448px capture without incoherent overlap. | `client/components/Layout.tsx`, `client/components/ControlCenter.tsx`, `output/playwright/ui-parity/overview.png`, `tests/e2e/ui_routes.spec.ts` | Complete |
| Overview | Metric cards are tighter, chart hierarchy now includes grid/point treatment, and above-the-fold panels expose trend, niche, category, seasonal, draft, A/B, and notification context. | `client/pages/index.tsx`, `output/playwright/ui-parity/overview.png`, `client/__tests__/index.test.tsx` | Complete / P2 visual tolerance |
| Trends | Keyword table prioritizes source-backed market evidence, shows public source/product examples when captured, falls back to labeled keyword evidence instead of demo assets, and keeps save/watch/compose flows wired. | `client/pages/trends.tsx`, `output/playwright/ui-parity/trends.png`, `client/__tests__/trendsPage.test.tsx`, `tests/e2e/discover_to_composer.spec.ts` | Complete |
| Seasonal events | Calendar density is tighter, summary metrics are denser, event drilldown and composer handoff remain intact. | `client/pages/seasonal-events.tsx`, `output/playwright/ui-parity/seasonal-events.png`, `client/__tests__/seasonalEventsPage.test.tsx` | Complete / P2 visual tolerance |
| Niche suggestions | Suggested niches and design inspiration now show local demo thumbnails labeled `Demo / local`; save, composer, and A/B handoffs remain wired. | `client/pages/niches.tsx`, `client/components/DemoProductArt.tsx`, `output/playwright/ui-parity/niches.png`, `client/__tests__/nichesPage.test.tsx` | Complete |
| Search & suggestions | Results, inspiration, and comparison cards now include local demo product thumbnails; watchlist, tag generation, save search, and composer handoff remain wired. | `client/pages/search.tsx`, `output/playwright/ui-parity/search.png`, `client/__tests__/searchPage.test.tsx`, `tests/e2e/search.spec.ts` | Complete |
| Listing composer | `/listing-composer` first-paints with a useful local demo draft, provenance-labeled preview, score, compliance checks, tags, persisted draft history, source-backed revision trails, market evidence handoff panel, paginated publish queue visibility, and non-blocking credential messaging. Query handoffs and direct `?draft=` links still prefill context. | `client/components/ListingComposer.tsx`, `client/services/listings.ts`, `services/listing_composer/service.py`, `output/playwright/ui-parity/listing-composer.png`, `client/__tests__/ListingComposer.test.tsx`, `tests/e2e/listings.spec.ts`, `tests/e2e/listing_draft.spec.ts` | Complete |
| A/B testing lab | Experiment table and variant detail include local demo thumbnails; create/pause/duplicate/end/push-winner flows remain local/demo-state safe. | `client/pages/ab-tests.tsx`, `output/playwright/ui-parity/ab-tests.png`, `client/__tests__/abTestsPage.test.tsx`, `tests/e2e/ab_tests.spec.ts` | Complete / P2 visual tolerance |
| Notifications scheduler | Existing dense scheduler, rules, jobs, preferences, Slack non-blocking state, and feed actions remain intact. | `client/pages/notifications.tsx`, `output/playwright/ui-parity/notifications.png`, `client/__tests__/notificationsSchedule.test.tsx`, `tests/e2e/notifications.spec.ts` | Complete |
| Settings & localization | Settings now keeps scoped tabs and adds a dense `Overview` first tab showing localization, brand, integrations, quotas, usage, and users together, matching the reference density decision. | `client/pages/settings.tsx`, `output/playwright/ui-parity/settings.png`, `client/__tests__/settingsPage.test.tsx`, `tests/e2e/localization.spec.ts` | Complete |

## Required Workflow Coverage

| Flow | Evidence | Result |
| --- | --- | --- |
| Discover trend to composer | Trend keyword/design links, market evidence query handoff, composer query prefill, browser route handoff | Covered |
| Composer persisted activity | Draft list/history pagination, direct draft loading, publish queue pagination/filtering, export and queue provenance | Covered |
| Niche to listing and A/B setup | Niche action links, composer and A/B route handoff tests | Covered |
| Search to watchlist/generated tags/composer | Search page actions, API service calls, e2e workflow | Covered |
| Create A/B test and push winner | A/B form/action tests and local/demo integration status | Covered |
| Schedule alert and Slack fallback | Notifications e2e and component tests | Covered |
| Settings localization update | Overview plus scoped Localization tab, API save path, e2e update | Covered |

## Residual Gaps

| Priority | Gap | User Impact | Acceptance Criteria |
| --- | --- | --- | --- |
| P0 | No P0 residual gaps found | Primary parity loops render and pass browser workflow tests | N/A |
| P1 | No P1 residual gaps found | Composer first paint and local visual assets are now present and labeled | N/A |
| P2 | Strict pixel-level chart parity remains approximate on Overview, Trends, Seasonal, and A/B | Current charts are denser and more hierarchical, but not exact recreations of every sample chart treatment | Optional design pass compares chart geometry against `UI_Samples/*.png` with annotated deltas |
| P2 | Search table density is improved but still has cramped columns at 1448px with thumbnails enabled | Operators can complete workflows, but very dense rows may benefit from a list/card hybrid | Add responsive column hiding or a compact card row mode while preserving quick actions |
| P3 | Build emits stale Browserslist data notice | Build passes, but logs include maintenance noise | Update caniuse-lite/browserslist data in a dependency maintenance pass if package updates are allowed |

## Final Assessment

The requested P1 gaps are closed: composer first paint is useful without credentials, product/design placeholders are replaced by local inspectable demo thumbnails, and credential-backed generation remains non-blocking and labeled. P2 density and chart fidelity are materially improved, with settings resolved by adding a dense overview tab while preserving scoped tabs. P3 datetime hygiene is complete for direct `datetime.utcnow()` calls in backend services and tests.
