"""
Yamaguchi Dashboard — FastAPI backend
Provides:
  GET  /api/health          health check
  GET  /api/tasks           snapshot of all sections (JSON)
  GET  /api/tasks/stream    real-time SSE stream

Data model:
  sections[]
    └── task_groups[]
          └── batches[] | events[]
"""

import asyncio
import datetime
import json
import logging
import os
import time

import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

logger = logging.getLogger("dashboard")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

app = FastAPI(title="Yamaguchi Dashboard API", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Configuration (from environment variables)
# ---------------------------------------------------------------------------

DATAAPP_API_URL = os.getenv("DATAAPP_API_URL", "http://localhost:8000")
DATAAPP_SERVICE_TOKEN = os.getenv("DATAAPP_SERVICE_TOKEN", "")
WEBAPP_API_URL = os.getenv("WEBAPP_API_URL", "http://localhost:8001")
WEBAPP_SERVICE_TOKEN = os.getenv("WEBAPP_SERVICE_TOKEN", "")
FETCH_INTERVAL_S = int(os.getenv("FETCH_INTERVAL_S", "30"))
FETCH_TIMEOUT_S = int(os.getenv("FETCH_TIMEOUT_S", "10"))
TIME_WINDOW_DAYS = int(os.getenv("TIME_WINDOW_DAYS", "2"))

# ---------------------------------------------------------------------------
# Cache
# ---------------------------------------------------------------------------

_cache: dict = {
    "sections": [],
    "timestamp": 0.0,
    "stale": False,
}
_lock = asyncio.Lock()

# ---------------------------------------------------------------------------
# Downstream API fetchers
# ---------------------------------------------------------------------------


async def _fetch_json(url: str, token: str, auth_scheme: str = "Token") -> list | dict | None:
    """Fetch JSON from a downstream API endpoint. Returns None on failure."""
    try:
        async with httpx.AsyncClient(timeout=FETCH_TIMEOUT_S) as client:
            r = await client.get(
                url,
                headers={"Authorization": f"{auth_scheme} {token}"},
            )
            r.raise_for_status()
            return r.json()
    except Exception as e:
        logger.warning("Failed to fetch %s: %s", url, e)
        return None


# ---------------------------------------------------------------------------
# Section builders — transform downstream API responses into dashboard format
# ---------------------------------------------------------------------------


def _build_nextcloud_section(data: list | None) -> dict:
    """
    data: [{model_name, events: [{id, direction, timestamp, ...}]}]
    """
    task_groups = []
    if data:
        for group in data:
            model_name = group.get("model_name", "unknown")
            task_groups.append({
                "id": f"SYNC_{model_name.upper()}",
                "label": model_name,
                "pipeline": "nextcloud",
                "events": group.get("events", []),
            })
    return {
        "id": "nextcloud_sync",
        "label": "Nextcloud 数据同步",
        "task_groups": task_groups,
    }


def _build_webapp_section(data: list | None) -> dict:
    """
    data: [{source_name, events: [{id, source_name, timestamp, ...}]}]
    """
    task_groups = []
    if data:
        for group in data:
            source_name = group.get("source_name", "unknown")
            task_groups.append({
                "id": f"WEBAPP_{source_name.upper()}",
                "label": source_name,
                "pipeline": "webapp",
                "events": group.get("events", []),
            })
    return {
        "id": "webapp_scraper",
        "label": "价格抓取（Webapp）",
        "task_groups": task_groups,
    }


def _build_tracking_section(data: list | None, *, source_type: str) -> dict:
    """
    data: [{task_name, source_type, label, batches: [...]}]
    Filter by source_type ('excel' or 'db').
    """
    task_groups = []
    if data:
        for group in data:
            if group.get("source_type") != source_type:
                continue
            task_name = group.get("task_name", "unknown")
            task_groups.append({
                "id": task_name.upper(),
                "label": group.get("label", task_name),
                "pipeline": source_type,
                "batches": group.get("batches", []),
            })

    if source_type == "excel":
        return {
            "id": "excel_tracking",
            "label": "追踪任务（Excel 驱动）",
            "task_groups": task_groups,
        }
    else:
        return {
            "id": "db_tracking",
            "label": "追踪任务（DB 驱动）",
            "task_groups": task_groups,
        }


def _build_email_section(data: list | None) -> dict:
    """
    data: [{stage, label, batches: [{id, created_at, ...}]}]
    """
    task_groups = []
    if data:
        for group in data:
            stage = group.get("stage", "unknown")
            task_groups.append({
                "id": f"EMAIL_{stage.upper()}",
                "label": group.get("label", stage),
                "pipeline": "email",
                "batches": group.get("batches", []),
            })
    return {
        "id": "email",
        "label": "邮件处理",
        "task_groups": task_groups,
    }


# ---------------------------------------------------------------------------
# Refresh loop — pulls data from downstream APIs every FETCH_INTERVAL_S
# ---------------------------------------------------------------------------


async def _refresh_sections():
    """Fetch from all downstream APIs and rebuild the cached sections."""
    async with _lock:
        days = f"?days={TIME_WINDOW_DAYS}"

        nextcloud, tracking, email, scraper = await asyncio.gather(
            _fetch_json(
                f"{DATAAPP_API_URL}/api/acquisition/dashboard/nextcloud-sync/{days}",
                DATAAPP_SERVICE_TOKEN,
                auth_scheme="Bearer",
            ),
            _fetch_json(
                f"{DATAAPP_API_URL}/api/acquisition/dashboard/tracking-batches/{days}",
                DATAAPP_SERVICE_TOKEN,
                auth_scheme="Bearer",
            ),
            _fetch_json(
                f"{DATAAPP_API_URL}/api/aggregation/dashboard/email-tasks/{days}",
                DATAAPP_SERVICE_TOKEN,
                auth_scheme="Bearer",
            ),
            _fetch_json(
                f"{WEBAPP_API_URL}/api/dashboard/scraper-events/{days}",
                WEBAPP_SERVICE_TOKEN,
                auth_scheme="Token",
            ),
        )

        sections = [
            _build_nextcloud_section(nextcloud),
            _build_webapp_section(scraper),
            _build_tracking_section(tracking, source_type="excel"),
            _build_tracking_section(tracking, source_type="db"),
            _build_email_section(email),
        ]

        _cache["sections"] = sections
        _cache["timestamp"] = time.time()
        _cache["stale"] = any(x is None for x in [nextcloud, tracking, email, scraper])

        if _cache["stale"]:
            failed = []
            if nextcloud is None:
                failed.append("nextcloud")
            if tracking is None:
                failed.append("tracking")
            if email is None:
                failed.append("email")
            if scraper is None:
                failed.append("scraper")
            logger.warning("Stale data — failed to fetch: %s", ", ".join(failed))
        else:
            logger.info("Refreshed all sections successfully")


def _snapshot() -> dict:
    return {
        "timestamp": datetime.datetime.now().isoformat(),
        "sections": _cache.get("sections", []),
        "stale": _cache.get("stale", False),
    }


# ---------------------------------------------------------------------------
# Startup — background refresh loop
# ---------------------------------------------------------------------------


@app.on_event("startup")
async def start_refresh_loop():
    async def loop():
        while True:
            try:
                await _refresh_sections()
            except Exception:
                logger.exception("Refresh loop error")
            await asyncio.sleep(FETCH_INTERVAL_S)

    asyncio.create_task(loop())


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@app.get("/api/health")
def health():
    return {"status": "ok", "timestamp": datetime.datetime.now().isoformat()}


@app.get("/api/tasks")
def get_tasks():
    return _snapshot()


@app.get("/api/tasks/stream")
async def stream_tasks():
    """Server-Sent Events — pushes sections snapshot every 10 seconds."""

    async def event_generator():
        while True:
            payload = json.dumps(_snapshot(), ensure_ascii=False)
            yield f"data: {payload}\n\n"
            await asyncio.sleep(10)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
