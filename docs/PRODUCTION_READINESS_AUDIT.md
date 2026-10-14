# Production readiness audit

## Baseline observed

The reviewed `main` branch contains a FastAPI backend in `backend/main.py` and a React/TypeScript/Vite frontend in `frontend/`. The backend integrates optional Groq, SerpAPI, and GitHub APIs. API routes cover registration, login/logout, current-user lookup, dashboard, search creation/status, and candidate details.

## Blocking findings

- Users, bearer sessions, searches, progress events, and results are stored in Python dictionaries. A backend restart loses them, and multiple replicas do not share state.
- Search execution uses FastAPI `BackgroundTasks`; work is not durable and cannot be recovered after a worker/process crash.
- The original frontend container ran Vite's development server. Production now uses a multi-stage build and Nginx.
- The original dependencies included frontend packages marked `latest`; exact package versions are now specified, but a committed lockfile is still recommended.
- There was no baseline backend test suite in the reviewed tree. Initial API smoke/authentication tests have been added.
- No deployment target or Jenkins credentials were configured. CI builds and scans; it does not deploy.

## Changes in this branch

- Prometheus request counter and latency histogram with bounded method, route-template, and status labels.
- `/api/ready` endpoint and container health checks.
- Non-root backend container, multi-stage frontend container, Nginx static serving/API proxy, and Docker ignore files.
- Separate production-like Compose file with Prometheus/Grafana monitoring services bound to loopback.
- Prometheus scrape config, alert rules, provisioned Grafana data source/dashboard.
- Declarative Jenkins pipeline for tests, frontend build, config validation, immutable commit-tagged image builds, Gitleaks, and Trivy.
- Local setup, architecture, monitoring, Jenkins, and deployment documentation.

## Remaining work before production

1. Implement SQLAlchemy persistence and Alembic migrations for accounts, sessions, searches, state transitions, and results while preserving API contracts.
2. Move search work to a durable queue and separate worker; add retry/idempotency behavior.
3. Add integration tests against the chosen database/queue and test migrations.
4. Add user ownership checks for search/result routes, token expiry, rate limiting, and redacted structured logs.
5. Configure and test Alertmanager receivers if notifications are required.
6. Configure a deployment target, secret store, TLS/network controls, backup policy, and rollback process.

## Validation limitation

Changes were authored through GitHub's file API. This environment does not provide the repository's local Docker, Python, Node, Jenkins, Prometheus, or Grafana runtime, so no build/test/runtime check is claimed as executed. Run the commands in `docs/LOCAL_SETUP.md` and the Jenkins pipeline before merging.
