# Status and Outstanding Tasks

This file tracks the remaining work required to bring PODPusher to production readiness.

## Pending PRs

- **Image Review & Tagging PR** – Coming from the `feat/image-review-merge` branch via Codex. Review and merge once complete.

## Outstanding Tasks

1. **Monitoring & Observability** – Add structured logging, health checks and metrics for each service.
2. **Documentation** – Update internal docs and API docs as new features are added.
3. **Notification & Scheduling System** – Implement backend scheduling and a notification service to alert users about quota resets, trending products, and scheduled posts or product launches.
4. **Localization & Internationalization (i18n)** – Extend translation support beyond current pages and adapt currency formats for different locales.
5. Maintain architecture and schema diagrams.
6. **High-Resolution Image Generation Service** – Integrate configurable OpenAI and Gemini providers for image generation (Integrations Engineer).

## Completed
- A/B Testing Support – Flexible engine with experiment types, weighted traffic and scheduling.
- Real Integrations – Printify and Etsy clients implemented with stub fallbacks.

- Stub Removal – Placeholder logic eliminated and integrations call real APIs when keys are present.

- Re-implemented listing composer enhancements (drag-and-drop fields, improved tag suggestions, draft saving, multi-language input).
- Analytics Enhancements – Replace mocked analytics with real metrics collected from the database and user interactions.
- Social Media Generator – Rule-based captions and images with localisation and dashboard UI.
- Bulk Product Creation – CSV/JSON bulk upload endpoint and UI implemented.
- Testing & QA – Expanded unit, integration and Playwright end-to-end test coverage with CI integration.

## Instructions to Agents

Please refer to the appended section in `agents.md` for specific instructions on how each agent should tackle these tasks.