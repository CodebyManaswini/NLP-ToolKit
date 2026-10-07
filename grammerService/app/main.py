"""
Grammar Checking Service
--------------------------
Thin FastAPI microservice wrapping a self-hosted LanguageTool server.
LanguageTool does the actual grammar/style analysis; this service
exposes a clean, simplified REST API (POST /check, GET /health).

Runs alongside a `languagetool` container (image: erikvl87/languagetool,
port 8010) — see docker-compose.yml.
"""

import logging
import os
import time

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("grammar-service")

# In Docker Compose this resolves to the `languagetool` service name.
# Running locally without compose, override via env var to http://localhost:8010.
LANGUAGETOOL_URL = os.getenv("LANGUAGETOOL_URL", "http://localhost:8010")
DEFAULT_LANGUAGE = "en-US"
REQUEST_TIMEOUT = 15.0

app = FastAPI(
    title="Grammar Checking Service",
    description="Wraps a self-hosted LanguageTool server for grammar/style checks.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class CheckRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=20000)
    language: str = Field(default=DEFAULT_LANGUAGE)


class GrammarIssue(BaseModel):
    message: str
    short_message: str
    offset: int
    length: int
    replacements: list[str]
    rule_id: str
    category: str


class CheckResponse(BaseModel):
    text: str
    language: str
    issue_count: int
    issues: list[GrammarIssue]
    check_time_ms: float


class HealthResponse(BaseModel):
    status: str
    languagetool_reachable: bool


def _normalize_matches(matches: list[dict]) -> list[GrammarIssue]:
    issues = []
    for m in matches:
        issues.append(
            GrammarIssue(
                message=m.get("message", ""),
                short_message=m.get("shortMessage", "") or m.get("message", "")[:60],
                offset=m.get("offset", 0),
                length=m.get("length", 0),
                replacements=[r["value"] for r in m.get("replacements", [])[:5]],
                rule_id=m.get("rule", {}).get("id", "UNKNOWN"),
                category=m.get("rule", {}).get("category", {}).get("name", "Other"),
            )
        )
    return issues


@app.get("/health", response_model=HealthResponse)
async def health():
    reachable = False
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            r = await client.get(f"{LANGUAGETOOL_URL}/v2/languages")
            reachable = r.status_code == 200
    except Exception:
        logger.warning("LanguageTool backend not reachable")

    return HealthResponse(
        status="ok" if reachable else "degraded",
        languagetool_reachable=reachable,
    )


@app.post("/check", response_model=CheckResponse)
async def check(request: CheckRequest):
    start = time.time()
    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            r = await client.post(
                f"{LANGUAGETOOL_URL}/v2/check",
                data={"language": request.language, "text": request.text},
            )
            r.raise_for_status()
            data = r.json()
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=502, detail=f"LanguageTool error: {e}")
    except httpx.RequestError as e:
        raise HTTPException(status_code=503, detail=f"LanguageTool unreachable: {e}")

    elapsed_ms = (time.time() - start) * 1000
    issues = _normalize_matches(data.get("matches", []))

    return CheckResponse(
        text=request.text,
        language=request.language,
        issue_count=len(issues),
        issues=issues,
        check_time_ms=round(elapsed_ms, 2),
    )


@app.get("/")
def root():
    return {"service": "grammar-checking-service", "endpoints": ["/check (POST)", "/health (GET)"]}