# Scoutline

Evidence-first recruiting research app: FastAPI backend + React/Vite frontend, no database
(search state lives in an in-memory store, by design).

## Project layout
backend/    FastAPI app (main.py), requirements.txt, Dockerfile
frontend/   React + Vite app (src/), package.json, Dockerfile


- The frontend never receives provider credentials; Groq/SerpAPI/GitHub calls happen
  only in the backend.