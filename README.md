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
