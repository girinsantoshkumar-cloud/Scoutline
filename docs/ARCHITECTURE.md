# Scoutline architecture

## Current application flow

```text
Browser
  |
  | HTTP :8080
  v
Nginx static frontend ---- /api/* ----> FastAPI backend :8000
                                           |-- Groq (optional requirement extraction)
                                           |-- SerpAPI (optional web research)
                                           |-- GitHub API (public profile research)
                                           |-- in-memory users/sessions/searches (current limitation)

Prometheus :9090 --scrapes /metrics--> FastAPI
Grafana :3000 ----queries-----------> Prometheus
```

## Production-like container topology

- **frontend:** multi-stage Node build produces static assets; Nginx serves the SPA and proxies `/api/` to the backend.
- **backend:** FastAPI/Uvicorn runs as a non-root user and exposes API health and Prometheus metrics.
- **prometheus:** optional monitoring profile; scrapes the backend over an internal Docker network.
- **grafana:** optional monitoring profile; provisions Prometheus as a data source and loads the dashboard from files.

Prometheus and Grafana ports bind to `127.0.0.1` by default. Do not expose these management interfaces publicly without authentication, TLS, and network controls.

## Important architecture limitation

The current backend still stores accounts, sessions, searches, events, and candidate results in process memory. The production-like Compose file does not pretend PostgreSQL or a queue is integrated. Add persistence and a durable worker as a separate, API-compatible change before operating multiple replicas or promising durable search jobs.
