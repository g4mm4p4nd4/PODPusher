# POD Automator AI

This repository contains stub microservices for the POD Automator AI system. Each service is a small FastAPI application and Celery task worker.

## Requirements
- Python 3.11+
- Redis and PostgreSQL for local development

Install dependencies:
```bash
pip install -r requirements.txt
```

## Running Services
Use Docker Compose to start all services:
```bash
docker-compose up --build
```

This will start the gateway, microservices, Postgres, Redis and the Celery worker.

You can also run the worker locally with ./scripts/start_worker.sh

Run tests and lint checks:
```bash
black .
flake8
pytest
```

## Frontend Dashboard

The dashboard lives in the `client/` directory and uses Next.js with Tailwind CSS.
To start it locally:

```bash
cd client
npm install
npm run dev
```

## Trend Categories
The `/trends` service exposes popular niches such as animals and pets, activism,
families and couples, humor and memes, job or hobby related topics, health and
fitness, sustainability, love, music and food. If a category query parameter is
provided, only trends from that niche are returned.

## Seasonal Events
Use `/events/{month}` to retrieve notable holidays for that month. For example:

```bash
curl http://localhost:8002/events/february
```

returns Valentine’s Day, the Super Bowl and more.

## Product Ideas
Top print‑on‑demand categories include apparel, home decor, drinkware and
accessories. Among apparel, t‑shirts, sportswear and leggings are the most
popular products.

## Trending Product Categories
The `/product-categories` endpoint returns 2025’s leading niches based on market
research. Categories include apparel, home_decor, pet_items, jewelry,
accessories, tech_accessories, athletic_accessories and holiday_items. These
lists show that unisex t‑shirts, hoodies, leggings, mugs and posters lead sales.

Start the frontend and navigate to `/categories` to view them.

## Design Inspirations
The `/design-ideas` endpoint returns trending design themes for 2025 such as
photo uploads, besties & couples, animals & pets and more. Each category
includes example product ideas like personalized acrylic plaques or photo
blankets. View them in the dashboard at `/design`.

## Product Suggestions
`/product-suggestions` combines trending categories with design inspirations so
you can quickly brainstorm new listings. Categories include apparel, home decor,
pet items, jewelry, accessories, tech accessories, athletic accessories and
holiday items. Design themes span photo upload, besties/couples, word repeat,
text quotes, animals/pets, landscapes, cartoon characters/superheroes, 3D
effects, brush strokes, pop culture, crypto themes, funny daily life,
minimalism, vintage/retro, y2k nostalgia, goblincore/cottagecore and eco humor.
Visit `/suggestions` in the dashboard to see up to ten phrases like "sunset
mountain posters" or "paw print blankets" mixed with product types.

## Localization

The dashboard is fully translated using `next-i18next`. Translation files are located in `client/locales/<lang>/common.json`. Use the language switcher in the navigation bar to change languages. To add a new locale, create a folder with translations matching the keys in the English file and update `client/next-i18next.config.js`.

## Notifications & Scheduling

The backend includes a notifications service with a background scheduler. Monthly jobs reset image quotas for all users and create a reminder notification. Weekly jobs send a trending keywords summary based on the latest scraped data. Visit `/notifications` in the dashboard to view and mark messages as read. Unread counts appear beside a bell icon in the navigation bar.

## Search API

Filter products using the `/api/search` endpoint. You can pass `q`, `category`,
`tag` and `rating_min` query parameters. Example:

```bash
curl "http://localhost:8000/api/search?q=dog&category=apparel&tag=funny&rating_min=3"
```

## A/B Testing

Create experiments using the `/ab_tests` API. Post a JSON payload with a test
name and variant list:

```bash
curl -X POST http://localhost:8000/ab_tests -H 'Content-Type: application/json' \
  -d '{"name": "Title Test", "variants": ["A", "B"]}'
```

Record user interactions with `/ab_tests/{variant_id}/impression` and
`/ab_tests/{variant_id}/click`. Retrieve conversion metrics with
`/ab_tests/{test_id}/metrics` or `/ab_tests/metrics` for all tests. The dashboard
page at `/ab_tests` lets you create tests and view results.
