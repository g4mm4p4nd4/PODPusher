# Social Media Generator Specification

## Objective
Provide sellers with an automated tool to generate platform-ready social media posts for newly created products and schedule them, reducing time from listing to promotion.

**KPIs**
- 95% of social posts generated in under 5 seconds.
- ≥ 99% generation success rate.
- At least 30% of beta users share generated posts within the first week.

## Scope
- Generate AI captions and mock-up images for selected listings.
- Support Instagram, TikTok, Twitter and Pinterest.
- Allow optional scheduling metadata for future publishing.
- Provide copy-to-clipboard and asset download; no direct publishing (see Non-Goals).

## Personas & Needs
- **Side-Hustle Seller** – wants one-click posts for new listings to save time.
- **Social Influencer** – wants to monetise memes quickly across platforms.

See [AGENTS.md §4](../../agents.md#4--personas--problem-statements) for full persona definitions.

## User Stories
1. **Side-Hustle Seller**
   - *As a* seller viewing a product detail page
   - *I want* to generate an Instagram post automatically
   - *So that* I can promote the product without manual design.
   - **Acceptance:** Given I am on a product detail page, when I click **Generate social post** and choose **Instagram**, then the system returns a caption and mock-up image ready for posting.
2. **Social Influencer**
   - *As a* user with connected social accounts
   - *I want* to schedule a meme drop across multiple platforms
   - *So that* I can engage followers before the trend fades.
   - **Acceptance:** Given I have connected Twitter and TikTok, when I request posts for both platforms, then previews for each appear and I can schedule them individually.

## User Flow
1. User selects a listing or product.
2. System shows connected social accounts; user selects one or more platforms.
3. User optionally edits caption template and image style.
4. Frontend calls `POST /api/social/generate`.
5. Backend queues generation job and returns a `job_id`.
6. Frontend displays progress via polling `GET /api/social/{job_id}` or WebSockets.
7. When job completes, user previews posts and can copy assets or schedule.

## Data Requirements
- **Inputs:** `listing_id` (UUID), `platforms` (array enum: instagram|tiktok|twitter|pinterest), optional `style`, `tone`.
- **Outputs:** `caption` (string), `image_url` (string), `hashtags` (array), `platform` (enum), `status` (enum), `scheduled_at` (datetime, optional)
- Persist to `social_posts` table: `id`, `user_id`, `listing_id`, `platform`, `caption`, `image_url`, `created_at`, `scheduled_at`, `status`.

## API Contract
### POST `/api/social/generate`
**Request**
```json
{
  "listing_id": "uuid",
  "platforms": ["instagram"],
  "style": "lifestyle",
  "tone": "playful"
}
```
**Response 202**
```json
{
  "job_id": "uuid",
  "status": "queued"
}
```

### GET `/api/social/{job_id}`
**Response 200**
```json
{
  "job_id": "uuid",
  "status": "succeeded",
  "results": [
    {
      "platform": "instagram",
      "caption": "...",
      "image_url": "https://...",
      "hashtags": ["..."]
    }
  ]
}
```
- Implement endpoints and business logic per [Backend‑Coder responsibilities BC‑01/BC‑02](../../agents_backend_coder.md#2--responsibilities); use FastAPI async patterns and service/repository separation.

## Frontend Requirements
- Add a `/social-generator` page and component accessible from product detail pages.
- Manage state with React Query and integrate typed client for the above endpoints.
- Follow design system and accessibility rules; see [Frontend‑Coder responsibilities FC‑01/FC‑02](../../agents_frontend_coder.md#2--responsibilities).
- Show loading/errors, allow copy-to-clipboard and scheduling actions.

## Acceptance Tests
1. **Generate single-platform post**
   - Given a listing exists and the user connected Instagram
   - When the user generates a post for Instagram
   - Then a caption and image are returned within 5 seconds and saved to history.
2. **Generate multi-platform posts**
   - Given a listing exists and the user connected Twitter and TikTok
   - When the user requests posts for both platforms
   - Then results for each platform appear and can be scheduled individually.

## Non-Goals
- Actual publishing to social networks (future integration).
- Post-performance analytics.

## References
- Personas & objectives: [AGENTS.md §4–§5](../../agents.md#4--personas--problem-statements)
- Backend implementation: [AGENTS.Backend_Coder.md](../../agents_backend_coder.md)
- Frontend implementation: [AGENTS.Frontend_Coder.md](../../agents_frontend_coder.md)

## Feasibility & Open Questions
- **Backend-Coder**
  - *Feasibility:* API shapes align with BC‑01/BC‑02; asynchronous job pattern fits existing Celery setup.
  - *Open Questions:*
    - Should caption/image generation reuse existing prompt templates or require new ones?
    - Where will scheduled posts run if auto-publishing is added later?
- **Frontend-Coder**
  - *Feasibility:* Page and state usage align with FC‑01/FC‑02; no blockers identified for Next.js 14.
  - *Open Questions:*
    - Are design assets available for multi-platform previews?
    - How should unsaved caption edits be handled on navigation?
