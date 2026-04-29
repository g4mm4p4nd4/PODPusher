# PODPusher

PODPusher is the local development repo for POD Automator AI, a print-on-demand automation platform. The current development focus is proving the public trend discovery pipeline end to end before any Etsy, Printify, Stripe, or OpenAI credential-backed publishing work is enabled.

## Current Development State

The project now has a Docker Desktop oriented local stack that can run the trend pipeline without marketplace or paid API keys.

Implemented in the current slice:

- Public trend ingestion defaults to live mode with `TREND_INGESTION_STUB=0`.
- Trend discovery uses a deterministic provider chain:
  1. ScrapeGraphAI with Playwright and local Ollama.
  2. Existing selector-based source scraping.
  3. Google Trends RSS fallback.
- Public-only mode rejects cookie files, exported browser sessions, login URLs, usernames, and passwords.
- Scraper refresh status reports per-source method and counts for collected, persisted, failed, fallback, and skipped work.
- Prometheus and Grafana are included in Compose for local observability.
- Postgres uses the installed async driver through `postgresql+psycopg://...`.
- Billing, OAuth, Etsy, Printify, Stripe, and OpenAI credential paths remain non-blocking for local internal-tool testing.

Publishing to Etsy and Printify is intentionally out of scope until non-stub trend coverage is verified locally.

## Stack

| Area | Runtime |
| --- | --- |
| Backend services | Python, FastAPI, SQLModel, Celery |
| Trend extraction | ScrapeGraphAI, Playwright, Ollama, selector fallback, Google Trends RSS |
| Frontend | Next.js, React, TypeScript, Tailwind CSS |
| Data and queue | PostgreSQL, Redis |
| Observability | Prometheus, Grafana, structured logs |
| Local orchestration | Docker Compose |

## Local Docker Desktop Run

Start the full no-key local stack:

```bash
docker compose up --build
```

Compose starts:

- `gateway` on `http://localhost:8000`
- `trend_ingestion` on `http://localhost:8007`
- `frontend` on `http://localhost:3000`
- `prometheus` on `http://localhost:9090`
- `grafana` on `http://localhost:3001`
- `postgres`, `redis`, `ollama`, `ollama-pull`, `worker`, and `migrate`

Grafana is provisioned with the default local login:

```text
admin / admin
```

The Ollama init service pulls the default `llama3.2` model used by ScrapeGraphAI.

## Trend Smoke Test

After `docker compose up --build` is healthy, trigger a trend refresh through the gateway:

```bash
curl -X POST -H "X-User-Id: 1" http://localhost:8000/api/trends/refresh
```

Inspect the refresh audit payload:

```bash
curl http://localhost:8000/api/trends/live/status
```

Expected evidence for this slice:

- `last_mode` is `live`.
- `source_methods` contains non-stub attempts such as `scrapegraph`, `selector_fallback`, `rss_fallback`, or visible `failed` entries for blocked public pages.
- `signals_persisted` is greater than zero after a successful fallback path.
- Counts are populated for collected, persisted, failed, fallback, and skipped work.

Retrieve live trend data:

```bash
curl "http://localhost:8000/api/trends/live?lookback_hours=72&limit=25"
```

Open Grafana at `http://localhost:3001` and inspect the `Scraper Health` dashboard for scrape attempts, method usage, persisted keywords, fallback usage, failures, and request latency.

## Local Configuration

The default no-key settings are documented in `.env.example` and mirrored by `docker-compose.yml`.

Important defaults:

```text
DATABASE_URL=postgresql+psycopg://user:pass@db:5432/pod
TREND_INGESTION_STUB=0
TREND_INGESTION_SCRAPEGRAPH=1
SCRAPEGRAPH_MODEL=ollama/llama3.2
OLLAMA_BASE_URL=http://ollama:11434
BILLING_STUB_MODE=true
OPENAI_USE_STUB=1
```

Do not configure cookies, exported sessions, login URLs, usernames, or passwords for trend ingestion in this phase. The service rejects those settings before scraping starts.

## Local Python Development

Use Python 3.11+.

```bash
pip install -r requirements.txt
alembic upgrade head
```

Run focused checks:

```bash
python -m py_compile services/trend_ingestion/service.py services/trend_ingestion/scrapegraph_adapter.py
python -m flake8 services/trend_ingestion/service.py services/trend_ingestion/scrapegraph_adapter.py tests/test_trend_ingestion_service.py tests/test_trend_ingestion_utils.py tests/test_runtime_config_contract.py
python -m pytest -q tests/test_trend_ingestion_service.py tests/test_trend_ingestion_utils.py tests/test_runtime_config_contract.py tests/test_observability.py
```

General repo checks:

```bash
black .
flake8
pytest
```

## Frontend Dashboard

The dashboard lives in `client/`.

```bash
cd client
npm install
npm run dev
```

When running through Compose, the frontend is exposed at `http://localhost:3000` and points at the gateway on `http://localhost:8000`.

## Main API Surfaces

Trend pipeline:

- `POST /api/trends/refresh`
- `GET /api/trends/live`
- `GET /api/trends/live/status`

Additional product research and workflow APIs include:

- `/events/{month}`
- `/product-categories`
- `/design-ideas`
- `/product-suggestions`
- `/api/search`
- `/suggest-tags`
- `/ab_tests`

## Documentation

- Local observability and trend smoke: `docs/observability.md`
- Database migrations: `docs/migrations.md`
- Codex WSL setup: `docs/codex-wsl.md`
- Scraper outage runbook: `docs/runbooks/scraper-outage.md`

## Development Boundary

Current priority is validating public trend discovery and observability in Docker Desktop. Etsy, Printify, Stripe, OAuth, and OpenAI credential-backed workflows should stay stubbed or non-blocking until the trend coverage has been manually verified.


## Overview & Purpose
PODPusher provides a local development environment for POD Automator AI, a print-on-demand automation platform. The repository lets developers validate the trend discovery and publishing pipeline end to end before enabling integrations with external marketplaces and credential-based services like Etsy, Printify, Stripe, and OpenAI.

## Features & Tech Stack

**Key features**:

- Local Docker stack to run gateway, trend ingestion, frontend, monitoring, and supporting services.
- Deterministic trend discovery using ScrapeGraphAI with Playwright and local Ollama models.
- Grafana and Prometheus dashboards for observability of scrape attempts, method usage, and failures.
- Preconfigured Postgres and Redis instances with migration scripts.
- Stubs and test harnesses for third-party marketplace and payment integrations.
- Frontend dashboard to view trend results and trigger refreshes.

**Tech stack**:

| Component       | Technology/Notes                    |
|-----------------|--------------------------------------|
| Backend         | Python 3 (FastAPI) and ScrapeGraphAI |
| Frontend        | React with Node.js                   |
| Data stores     | PostgreSQL, Redis                    |
| Observability   | Prometheus, Grafana                  |
| Deployment      | Docker Compose                       |
| LLM Integration | Ollama with Llama 3.2 models         |

## Installation & Usage

Follow these steps to run the project locally:

```bash
# Clone the repository and enter the directory
git clone https://github.com/g4mm4p4nd4/PODPusher.git
cd PODPusher

# Start the full local stack using Docker Compose
# This brings up the gateway, trend ingestion, frontend, database, and monitoring services
docker compose --profile default up --build

# (Optional) To develop the frontend separately
cd client
npm install
npm run dev

# (Optional) To run Python tests and linting
pip install -r requirements.txt
pytest
flake8
```

## Business & Entrepreneurial Value

PODPusher demonstrates how businesses can automate product research and publishing workflows in the print-on-demand space. By encapsulating trend discovery, design generation, and marketplace integration in a single platform, organizations can license the technology to merchants as a subscription service or offer premium tiers for advanced analytics and bulk publishing. The modular architecture allows integration with multiple storefronts and payment providers, creating opportunities for partnerships, upsells, and bespoke solutions. Efficient automation reduces operational overhead and accelerates time-to-market, unlocking new revenue streams.

## Consumer Value

End users benefit from a streamlined, transparent workflow that removes the manual effort of monitoring trends, designing products, and managing listings across marketplaces. The local dashboard and API surface make it easy to refresh trends, view analytics, and customize settings without dealing with API keys during early development. Once integrated with marketplaces, consumers can deploy new products faster, respond to emerging trends, and enjoy greater flexibility in customizing their storefronts while maintaining data privacy and control.
