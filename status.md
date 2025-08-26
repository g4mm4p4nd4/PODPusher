# Status and Outstanding Tasks

This file tracks the remaining work required to bring PODPusher to production readiness.

## Pending PRs

- **Image Review & Tagging PR** – Coming from the `feat/image-review-merge` branch via Codex. Review and merge once complete.

## Outstanding Tasks

1. **Real Integrations** – Implement Printify and Etsy clients, replacing stubs in `services/integration/service.py`. Use environment variables for API keys and handle retries. Stripe billing integration also needs to be built for subscription plans.

2. **Analytics Enhancements** – Replace mocked analytics with real metrics collected from the database and user interactions.
3. **Testing & QA** – Increase unit, integration and end-to-end test coverage. Ensure Playwright tests run reliably in CI.
4. **Monitoring & Observability** – Add structured logging, health checks and metrics for each service.

5. **Documentation** – Update internal docs and API docs as new features are added.
6. **Bulk Product Creation** – Add a CSV/bulk upload endpoint (`/api/bulk_create`) and UI for uploading multiple products, including progress indicators and error handling.
7. **A/B Testing Support** – Create a model and API for A/B tests, enabling sellers to compare titles, descriptions and tags; include UI to set up tests and view metrics.
8. **Notification & Scheduling System** – Implement backend scheduling and a notification service to alert users about quota resets, trending products, and scheduled posts or product launches.
9. **Localization & Internationalization (i18n)** – Extend translation support beyond current pages and adapt currency formats for different locales.
10. Maintain architecture and schema diagrams.
11. **Stub Removal** – Once integrations and features are fully implemented and tested, remove any placeholder or stubbed logic from the codebase.
12. **Social Media Generator** – Add a service that produces captions and images for social posts based on product ideas and trends.


## Instructions to Agents

Please refer to the appended section in `agents.md` for specific instructions on how each agent should tackle these tasks.
