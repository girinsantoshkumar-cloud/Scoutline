# Scoutline

Scoutline is a recruiting research application built with **FastAPI** and **React + TypeScript + Vite**. It searches public professional signals through optional Groq, SerpAPI, and GitHub integrations and displays the evidence behind candidate matching.

## Architecture

- `backend/`: FastAPI API, provider integrations, authentication, search orchestration, Prometheus metrics.
- `frontend/`: React UI. Development uses Vite; production builds static assets and serves them through Nginx.
- `prometheus/`: scrape configuration and initial alert rules.
- `grafana/`: provisioned Prometheus data source and service dashboard.
- `Jenkinsfile`: CI tests, frontend build, configuration validation, image build, secret and vulnerability scans.

## Quick start: development

```bash
cp backend/.env.example backend/.env
# Edit backend/.env and add the provider keys you have.
docker compose up --build
```

Open the frontend at http://localhost:5173 and the API docs at http://localhost:8000/docs.

Stop the stack with `docker compose down`.

## Production-like local stack

```bash
docker compose -f docker-compose.production.yml up --build -d frontend backend
```

Open http://localhost:8080. The frontend is served as static assets by Nginx, which proxies `/api/` to FastAPI. Configure provider keys in `backend/.env` first.

## Monitoring

```bash
export GRAFANA_ADMIN_PASSWORD='set-a-strong-local-password'
docker compose -f docker-compose.production.yml --profile monitoring up --build -d
```

- Prometheus: http://127.0.0.1:9090
- Grafana: http://127.0.0.1:3000
- Metrics: available internally at backend `/metrics`

Prometheus and Grafana are bound to loopback in the production-like Compose file. Alert rules are provisioned, but no Alertmanager notification receiver is configured.

## Tests

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r backend/requirements-dev.txt
(cd backend && python -m pytest -q tests)
```

## Important production limitations

**This repository is not yet fully production-ready.** Accounts, bearer sessions, searches, progress events, and candidate results are stored in process memory and are lost when the backend restarts. Search execution uses in-process FastAPI background tasks rather than a durable queue. Do not run multiple backend replicas or promise durable job recovery until PostgreSQL persistence, migrations, and durable background processing have been implemented and tested.

The Jenkins pipeline does not deploy to a cloud environment. Deployment credentials and a target environment must be configured separately. See:

- [Production readiness audit](docs/PRODUCTION_READINESS_AUDIT.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Local setup](docs/LOCAL_SETUP.md)
- [Jenkins setup](docs/JENKINS_SETUP.md)
- [Monitoring](docs/MONITORING.md)
- [Deployment and rollback](docs/DEPLOYMENT.md)

Never commit `backend/.env` or any real API key. Configure secrets through the deployment environment or Jenkins credentials.
