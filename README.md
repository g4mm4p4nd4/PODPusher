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
