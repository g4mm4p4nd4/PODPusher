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
