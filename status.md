# Status and Outstanding Tasks

This file tracks the remaining work required to bring PODPusher to production readiness.

## Pending PRs

- **Image Review & Tagging PR** – Coming from the `feat/image-review-merge` branch via Codex. Review and merge once complete.

## Outstanding Tasks

1. **Analytics Enhancements** – Replace mocked analytics with real metrics collected from the database and user interactions.
2. **Testing & QA** – Increase unit, integration and end-to-end test coverage. Ensure Playwright tests run reliably in CI.
3. **Monitoring & Observability** – Add structured logging, health checks and metrics for each service.

4. **Documentation** – Update internal docs and API docs as new features are added.
5. **Bulk Product Creation** – Add a CSV/bulk upload endpoint (`/api/bulk_create`) and UI for uploading multiple products, including progress indicators and error handling.
6. **Notification & Scheduling System** – Implement backend scheduling and a notification service to alert users about quota resets, trending products, and scheduled posts or product launches.
7. **Localization & Internationalization (i18n)** – Extend translation support beyond current pages and adapt currency formats for different locales.
8. Maintain architecture and schema diagrams.
9. **Stub Removal** – Once integrations and features are fully implemented and tested, remove any placeholder or stubbed logic from the codebase.
10. **Social Media Generator** – Add a service that produces captions and images for social posts based on product ideas and trends.

## Completed
- A/B Testing Support – Flexible engine with experiment types, weighted traffic and scheduling.
- Real Integrations – Printify and Etsy clients implemented with stub fallbacks.

- Re-implemented listing composer enhancements (drag-and-drop fields, improved tag suggestions, draft saving, multi-language input).


## Instructions to Agents

Please refer to the appended section in `agents.md` for specific instructions on how each agent should tackle these tasks.