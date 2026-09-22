# Scoutline

Evidence-first recruiting research app: FastAPI backend + React/Vite frontend, no database
(search state lives in an in-memory store, by design).

## Project layout

```
backend/    FastAPI app (main.py), requirements.txt, Dockerfile
frontend/   React + Vite app (src/), package.json, Dockerfile
docker-compose.yml
```

## Run with Docker (recommended)

```bash
cp backend/.env.example backend/.env
# optionally add GROQ_API_KEY / SERPAPI_KEY / GITHUB_TOKEN to backend/.env for live research

docker compose up --build
```

- Frontend: http://localhost:5173
- Backend health check: http://localhost:8000/api/health

Without provider keys, the app still runs — searches will report that live research
is paused rather than inventing fake candidates.

## Run without Docker

Backend:

```bash
cd backend
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # add API keys if you have them
uvicorn main:app --reload --port 8000
```

Frontend (in a second terminal):

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173 — the dev server proxies `/api/*` to the backend on port 8000.

## Notes

- The frontend never receives provider credentials; Groq/SerpAPI/GitHub calls happen
  only in the backend.
- `docker-compose.yml` mounts source as volumes and runs the Vite dev server, so edits
  to `frontend/` and `backend/` hot-reload inside the containers.
