# Local setup

## Prerequisites

- Docker Engine and Docker Compose v2
- Git
- Optional for tests outside Docker: Python 3.12+ and Node.js 20+

## Configure provider credentials

From the repository root:

```bash
cp backend/.env.example backend/.env
```

Edit `backend/.env` and set only the provider keys you have. Keep this file local; never commit it. Live candidate research needs the relevant provider key(s). The app may report a blocked live search when integrations are not configured.

## Run the existing development Compose stack

```bash
docker compose up --build
```

Open the Vite frontend at http://localhost:5173 and API docs at http://localhost:8000/docs. Stop with `Ctrl+C`; remove containers with `docker compose down`.

## Run the production-like stack

Build and start the frontend and backend:

```bash
docker compose -f docker-compose.production.yml up --build -d frontend backend
```

Open http://localhost:8080. Nginx serves built static assets and proxies API calls to FastAPI. The backend is not published directly to the host in this Compose file.

Stop it:

```bash
GRAFANA_ADMIN_PASSWORD="$GRAFANA_ADMIN_PASSWORD" docker compose -f docker-compose.production.yml down
```

## Run local backend tests

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r backend/requirements-dev.txt
(cd backend && python -m pytest -q tests)
```

## Enable monitoring

Set a non-default local Grafana password in your shell, then launch the monitoring profile:

```bash
export GRAFANA_ADMIN_PASSWORD='replace-with-a-strong-local-password'
docker compose -f docker-compose.production.yml --profile monitoring up --build -d
```

- App: http://localhost:8080
- Prometheus: http://127.0.0.1:9090
- Grafana: http://127.0.0.1:3000 (default username `admin`, unless `GRAFANA_ADMIN_USER` is set)

Do not use the example password in a real environment. Monitoring data is stored in named Docker volumes. To stop services without deleting metrics/dashboard state, run `docker compose -f docker-compose.production.yml --profile monitoring down`. Do not add `-v` unless you intend to delete those volumes.

## Troubleshooting

- If the frontend is healthy but API calls fail, inspect `docker compose -f docker-compose.production.yml logs backend frontend`.
- If live research is blocked, check provider keys in `backend/.env` without printing their values.
- If monitoring targets are down, verify the backend is healthy and inspect Prometheus at http://127.0.0.1:9090/targets.
- A healthy process does not mean data is durable. The current application state is in-memory and is lost when the backend restarts.
