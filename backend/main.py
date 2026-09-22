from __future__ import annotations

import asyncio
import json
import os
import re
import uuid
from datetime import datetime, timezone
from typing import Any

import httpx
from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    groq_api_key: str = ""
    serpapi_key: str = ""
    github_token: str = ""
    cors_origins: str = "http://localhost:5173"


settings = Settings()
app = FastAPI(title="Scoutline API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in settings.cors_origins.split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class SearchRequest(BaseModel):
    title: str = Field(min_length=2, max_length=120)
    description: str = Field(min_length=20, max_length=10000)
    count: int = Field(default=10, ge=5, le=20)
    location: str = ""
    experience: str = ""
    required_technologies: list[str] = []
    preferred_technologies: list[str] = []


class SearchRecord(BaseModel):
    id: str
    title: str
    description: str
    count: int
    status: str = "queued"
    stage: str = "Queued"
    progress: int = 0
    events: list[str] = []
    requirements: dict[str, Any] = {}
    candidates: list[dict[str, Any]] = []
    error: str | None = None
    created_at: str


searches: dict[str, SearchRecord] = {}


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        cleaned = re.sub(r"\s+", " ", value.strip())
        key = cleaned.lower()
        if cleaned and key not in seen:
            seen.add(key)
            result.append(cleaned)
    return result


def extract_json(text: str) -> dict[str, Any]:
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError("AI response did not contain JSON")
    return json.loads(match.group(0))


async def groq_json(system: str, prompt: str) -> dict[str, Any]:
    if not settings.groq_api_key:
        raise RuntimeError("AI analysis unavailable: GROQ_API_KEY is not configured.")
    headers = {"Authorization": f"Bearer {settings.groq_api_key}", "Content-Type": "application/json"}
    payload = {
        "model": "llama-3.3-70b-versatile",
        "temperature": 0.1,
        "messages": [{"role": "system", "content": system}, {"role": "user", "content": prompt}],
        "response_format": {"type": "json_object"},
    }
    async with httpx.AsyncClient(timeout=45) as client:
        response = await client.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload)
        response.raise_for_status()
        return extract_json(response.json()["choices"][0]["message"]["content"])


async def extract_requirements(request: SearchRequest) -> dict[str, Any]:
    if settings.groq_api_key:
        prompt = f"""Analyze this recruiting brief. Return JSON only with keys: role, required_skills, preferred_skills, technologies, frameworks, experience_requirements, role_requirements, project_requirements, search_queries. Each skill/query is a short string. Do not invent requirements that are not supported by the brief.\nTITLE: {request.title}\nDESCRIPTION: {request.description}"""
        data = await groq_json("You are an evidence-first recruiting analyst. Prefer precise, deduplicated terms.", prompt)
        return {
            "role": data.get("role") or request.title,
            "required_skills": unique(data.get("required_skills", [])),
            "preferred_skills": unique(data.get("preferred_skills", [])),
            "technologies": unique(data.get("technologies", [])),
            "frameworks": unique(data.get("frameworks", [])),
            "experience_requirements": unique(data.get("experience_requirements", [])),
            "role_requirements": unique(data.get("role_requirements", [])),
            "project_requirements": unique(data.get("project_requirements", [])),
            "search_queries": unique(data.get("search_queries", []))[:6],
        }
    # This is a deterministic fallback for wiring/UX validation, not candidate data.
    terms = re.findall(r"[A-Za-z][A-Za-z0-9+#.-]{1,}", request.description)
    known = {term.lower(): term for term in terms if len(term) > 2}
    tech = [known[key] for key in ["python", "fastapi", "postgresql", "docker", "aws", "kubernetes", "typescript", "react", "java", "go"] if key in known]
    required = [term for term in tech if term.lower() in request.description.lower()]
    return {"role": request.title, "required_skills": unique(required), "preferred_skills": [], "technologies": unique(tech), "frameworks": [], "experience_requirements": [], "role_requirements": [], "project_requirements": [], "search_queries": [f"{request.title} GitHub", f"{request.title} developer portfolio"]}


async def serp_search(query: str, count: int) -> list[dict[str, Any]]:
    if not settings.serpapi_key:
        raise RuntimeError("Web search temporarily unavailable: SERPAPI_KEY is not configured.")
    params = {"engine": "google", "q": query, "api_key": settings.serpapi_key, "num": min(count, 10)}
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.get("https://serpapi.com/search.json", params=params)
        response.raise_for_status()
        return response.json().get("organic_results", [])


async def github_search(query: str, count: int) -> list[dict[str, Any]]:
    headers = {"Accept": "application/vnd.github+json"}
    if settings.github_token:
        headers["Authorization"] = f"Bearer {settings.github_token}"
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.get("https://api.github.com/search/users", params={"q": query, "per_page": min(count, 20)}, headers=headers)
        response.raise_for_status()
        return response.json().get("items", [])


async def github_profile(login: str) -> dict[str, Any]:
    headers = {"Accept": "application/vnd.github+json"}
    if settings.github_token:
        headers["Authorization"] = f"Bearer {settings.github_token}"
    async with httpx.AsyncClient(timeout=30) as client:
        profile_response, repo_response = await asyncio.gather(
            client.get(f"https://api.github.com/users/{login}", headers=headers),
            client.get(f"https://api.github.com/users/{login}/repos", params={"sort": "updated", "per_page": 8}, headers=headers),
        )
        profile_response.raise_for_status(); repo_response.raise_for_status()
        return {"profile": profile_response.json(), "repos": repo_response.json()}


def score_candidate(profile: dict[str, Any], requirements: dict[str, Any]) -> dict[str, Any]:
    repos = profile.get("repos", [])
    corpus = " ".join([profile.get("profile", {}).get("bio", "") or ""] + [f"{r.get('name', '')} {r.get('description', '') or ''} {' '.join((r.get('topics') or []))} {' '.join((r.get('language') or '',))}" for r in repos]).lower()
    required = requirements.get("required_skills", [])
    preferred = requirements.get("preferred_skills", [])
    checks = []
    for skill in required:
        found = skill.lower() in corpus
        checks.append({"name": skill, "status": "verified" if found else "unverified", "evidence": f"Public GitHub profile or repository text mentions {skill}." if found else "Not verified from public GitHub evidence."})
    preferred_checks = [{"name": skill, "status": "partial" if skill.lower() in corpus else "unverified", "evidence": f"Public repository evidence mentions {skill}." if skill.lower() in corpus else "Not verified from public evidence."} for skill in preferred]
    required_verified = sum(item["status"] == "verified" for item in checks)
    preferred_verified = sum(item["status"] == "partial" for item in preferred_checks)
    denominator = max(1, len(checks) * 2 + len(preferred_checks))
    points = required_verified * 2 + preferred_verified
    project_count = len([r for r in repos if r.get("description") or r.get("language")])
    match = round(points / denominator * 100)
    return {"match": match, "skills": checks + preferred_checks, "evidence_coverage": round((required_verified + preferred_verified) / max(1, len(checks) + len(preferred_checks)) * 100), "relevant_projects": project_count, "repositories": repos[:6]}


def candidate_from_github(data: dict[str, Any], requirements: dict[str, Any]) -> dict[str, Any]:
    profile = data["profile"]
    scoring = score_candidate(data, requirements)
    return {"id": profile.get("login"), "name": profile.get("name") or profile.get("login"), "login": profile.get("login"), "avatar_url": profile.get("avatar_url"), "profile_url": profile.get("html_url"), "github_url": profile.get("html_url"), "bio": profile.get("bio"), "location": profile.get("location"), "public_repos": profile.get("public_repos", 0), "role": "Public role not verified", "match": scoring["match"], "evidence_coverage": scoring["evidence_coverage"], "skills": scoring["skills"], "repositories": scoring["repositories"], "sources": [{"label": "GitHub profile", "url": profile.get("html_url")}], "experience": [], "summary": "Summary is limited to publicly available GitHub evidence. No employment claim is made without a public source."}


async def run_search(search_id: str, request: SearchRequest) -> None:
    record = searches[search_id]
    try:
        record.status = "running"; record.stage = "Analyzing job description"; record.progress = 12; record.events.append("Job description analyzed")
        record.requirements = await extract_requirements(request)
        record.stage = "Generating search strategy"; record.progress = 25; record.events.append("Search queries generated")
        if not settings.github_token and not settings.serpapi_key:
            record.status = "blocked"; record.stage = "Awaiting live integrations"; record.progress = 25; record.error = "Add SERPAPI_KEY and/or GITHUB_TOKEN to run live public-web research. No candidates were fabricated."; record.events.append("Live research paused because provider keys are missing"); return
        queries = record.requirements.get("search_queries", [])[:4] or [f"{request.title} GitHub"]
        record.stage = "Searching public web"; record.progress = 38; record.events.append("Searching public sources")
        web_results: list[dict[str, Any]] = []
        if settings.serpapi_key:
            for query in queries[:2]:
                web_results.extend(await serp_search(query, request.count))
        record.stage = "Searching GitHub"; record.progress = 54; record.events.append("Searching GitHub public profiles")
        github_items: list[dict[str, Any]] = []
        if settings.github_token:
            for query in queries[:2]:
                github_items.extend(await github_search(query, request.count))
        logins = unique([item.get("login", "") for item in github_items if item.get("login")])[: request.count]
        candidates: list[dict[str, Any]] = []
        for index, login in enumerate(logins):
            record.stage = f"Investigating candidate {index + 1}/{len(logins)}"; record.progress = 58 + round((index + 1) / max(1, len(logins)) * 35); record.events.append(f"Investigating {login}: GitHub projects and skills")
            try:
                candidates.append(candidate_from_github(await github_profile(login), record.requirements))
            except httpx.HTTPError:
                continue
        if not candidates and web_results:
            record.events.append(f"{len(web_results)} public web results discovered; no GitHub identity could be verified")
        record.candidates = sorted(candidates, key=lambda item: (item["match"], item["evidence_coverage"]), reverse=True)
        record.status = "completed"; record.stage = "Research complete"; record.progress = 100; record.events.append(f"{len(record.candidates)} candidate profiles verified from public GitHub evidence")
    except httpx.HTTPError as error:
        record.status = "error"; record.stage = "Provider error"; record.error = f"Research provider error: {error}"; record.events.append("A provider request failed; no fallback candidates were created")
    except Exception as error:
        record.status = "error"; record.stage = "Research error"; record.error = str(error); record.events.append("Research stopped safely without inventing evidence")


@app.get("/api/health")
async def health() -> dict[str, Any]:
    return {"ok": True, "providers": {"groq": bool(settings.groq_api_key), "serpapi": bool(settings.serpapi_key), "github": bool(settings.github_token)}, "storage": "in-memory session store (database intentionally deferred)"}


@app.get("/api/dashboard")
async def dashboard() -> dict[str, Any]:
    items = list(searches.values())
    return {"stats": {"candidates_found": sum(len(item.candidates) for item in items), "searches_completed": sum(item.status == "completed" for item in items), "candidates_investigated": sum(len(item.candidates) for item in items), "average_evidence_coverage": round(sum((candidate["evidence_coverage"] for item in items for candidate in item.candidates), 0) / max(1, sum(len(item.candidates) for item in items)))}, "recent_searches": [item.model_dump() for item in sorted(items, key=lambda item: item.created_at, reverse=True)[:8]]}


@app.post("/api/search", status_code=202)
async def create_search(request: SearchRequest, background_tasks: BackgroundTasks) -> SearchRecord:
    search_id = str(uuid.uuid4())
    record = SearchRecord(id=search_id, title=request.title, description=request.description, count=request.count, created_at=now())
    searches[search_id] = record
    background_tasks.add_task(run_search, search_id, request)
    return record


@app.get("/api/search/{search_id}")
async def get_search(search_id: str) -> SearchRecord:
    if search_id not in searches:
        raise HTTPException(404, "Search not found")
    return searches[search_id]


@app.get("/api/search/{search_id}/candidates")
async def get_candidates(search_id: str) -> list[dict[str, Any]]:
    if search_id not in searches:
        raise HTTPException(404, "Search not found")
    return searches[search_id].candidates


@app.get("/api/candidates/{candidate_id}")
async def get_candidate(candidate_id: str) -> dict[str, Any]:
    for search in searches.values():
        for candidate in search.candidates:
            if candidate["id"] == candidate_id:
                return candidate
    raise HTTPException(404, "Candidate not found")
