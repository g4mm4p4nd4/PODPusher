# Status and Outstanding Tasks

This file tracks the remaining work required to bring PODPusher to production readiness.

## Pending PRs

- **User Plans & Quotas PR** – Coming from the `feat/user-quota-merge` branch via Codex. Review and merge once it passes tests.
- **Image Review & Tagging PR** – Coming from the `feat/image-review-merge` branch via Codex. Review and merge once complete.

## Outstanding Tasks

1. **Real Integrations** – Implement Printify and Etsy clients, replacing stubs in `services/integration/service.py`. Use environment variables for API keys and handle retries. Stripe billing integration also needs to be built for subscription plans.
2. **Social Media Generator** – Add a service that produces captions and images for social posts based on product ideas and trends.
3. **Analytics Enhancements** – Replace mocked analytics with real metrics collected from the database and user interactions.
4. **Listing Composer Enhancements** – Finalise the character-count and tag-suggestion features; ensure they are merged and tested.
5. **Testing & QA** – Increase unit, integration and end-to-end test coverage. Ensure Playwright tests run reliably in CI.
6. **Monitoring & Observability** – Add structured logging, health checks and metrics for each service.
7. **Documentation** – Update internal docs and API docs as new features are added. Maintain architecture and schema diagrams.
8. **Stub Removal** – Once integrations are tested, remove any placeholder or stubbed logic from the codebase.

## Instructions to Agents

Please refer to the appended section in `agents.md` for specific instructions on how each agent should tackle these tasks.
