# Notifications & Scheduling

This service delivers user-facing alerts and summaries.

## Notification Types

| Type   | Purpose                                     |
| ------ | ------------------------------------------- |
| system | Platform events such as quota resets        |
| summary| Weekly trend highlights                     |
| info   | General informational messages              |

## Scheduling Behaviour

An async scheduler enqueues recurring jobs:

- **Monthly quota reset** – On the first day of each month at 00:00 UTC, user image quotas reset and a `system` notification is created.
- **Weekly trending summary** – Every Monday at 00:00 UTC, the latest top trends are summarised and sent as `summary` notifications.

Notifications are stored in the database and surfaced via the `/api/notifications` endpoints and UI bell icon. Delivery stubs exist for email and push channels; real integrations can replace them by providing API keys and setting `NOTIFY_USE_STUB=0`.
