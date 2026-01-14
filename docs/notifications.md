# Notifications & Scheduling

This service delivers user-facing alerts, summaries, and reminders for scheduled activity.

## Notification Types

| Type     | Purpose                                          |
| -------- | ------------------------------------------------ |
| system   | Platform events such as quota resets             |
| summary  | Weekly trend highlights                          |
| launch   | Product launch ideas and scheduled drop alerts   |
| info     | General informational messages                   |

## Scheduling Behaviour

An async scheduler enqueues recurring jobs:

- Monthly quota reset - On the first day of each month at 00:00 UTC the image quota counter resets and a `system` notification is created.
- Weekly trending summary - Every Monday at 00:00 UTC users receive the top keywords from the trend scraper as `summary` notifications.
- Daily launch digest - Once per day (13:00 UTC by default) a `launch` notification summarises suggested product ideas pulled from `services/trend_scraper`.
- Scheduled notifications - User defined reminders are stored in the `scheduled_notifications` table and dispatched at the requested time. Failed dispatches retry on the next polling cycle.

Notifications are stored in the database and surfaced via the `/api/notifications` endpoints and the UI bell icon. Delivery stubs exist for email and push channels; real integrations can replace them by providing API keys and setting `NOTIFY_USE_STUB=0`.

## API Overview

- `GET /api/notifications/` - List delivered notifications for the authenticated user.
- `POST /api/notifications/` - Create an immediate notification (internal use).
- `PUT /api/notifications/{id}/read` - Mark a notification as read.
- `GET /api/notifications/scheduled` - List upcoming or historical scheduled notifications.
- `POST /api/notifications/scheduled` - Schedule a future notification with optional metadata payload.
- `DELETE /api/notifications/scheduled/{id}` - Cancel a pending notification.

Scheduler intervals are configurable via `NOTIFY_DISPATCH_INTERVAL_MINUTES` and `NOTIFY_LAUNCH_DIGEST_HOUR` environment variables.
