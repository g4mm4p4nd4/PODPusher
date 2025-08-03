# Status and Outstanding Tasks

This file tracks the remaining work required to bring PODPusher to production readiness.

## Pending PRs

- **User Plans & Quotas PR** – Coming from the `feat/user-quota-merge` branch via Codex. Review and merge once it passes tests.
- **Image Review & Tagging PR** – Coming from the `feat/image-review-merge` branch via Codex. Review and merge once complete.

## Outstanding Tasks

1. **Real Integrations** – Implement Printify and Etsy clients, replacing stubs in `services/integration/service.py`. Use environment variables for API keys and handle retries. Stripe billing integration also needs to be built for subscription plans.

2. **Analytics Enhancements** – Replace mocked analytics with real metrics collected from the database and user interactions.
3. **Listing Composer Enhancements** – Finalise the character-count and tag-suggestion features; ensure they are merged and tested.
4. **Testing & QA** – Increase unit, integration and end-to-end test coverage. Ensure Playwright tests run reliably in CI.
5. **Monitoring & Observability** – Add structured logging, health checks and metrics for each service.

6. **Documentation** – Update internal docs and API docs as new features are added.
7. **Bulk Product Creation** – Add a CSV/bulk upload endpoint (`/api/bulk_create`) and UI for uploading multiple products, including progress indicators and error handling.
8. **Advanced Search & Filtering** – Build a `/api/search` endpoint with filtering options (category, trend, rating) and add a search page with filter controls.
9. **A/B Testing Support** – Create a model and API for A/B tests, enabling sellers to compare titles, descriptions and tags; include UI to set up tests and view metrics.
10. **Notification & Scheduling System** – Implement backend scheduling and a notification service to alert users about quota resets, trending products, and scheduled posts or product launches.
11. **Localization & Internationalization (i18n)** – Integrate translation support (e.g., next-i18next), provide a language switcher in the UI and adapt currency formats for different locales.
12. Maintain architecture and schema diagrams.
13. **Stub Removal** – Once integrations and features are fully implemented and tested, remove any placeholder or stubbed logic from the codebase.
14. **Social Media Generator** – Add a service that produces captions and images for social posts based on product ideas and trends.


## Instructions to Agents

Please refer to the appended section in `agents.md` for specific instructions on how each agent should tackle these tasks.
