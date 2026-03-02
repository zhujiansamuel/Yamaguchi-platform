"""
Yamaguchi Dashboard — minimal FastAPI backend
Provides:
  GET  /api/health          health check
  GET  /api/tasks           snapshot of all task groups (JSON)
  GET  /api/tasks/stream    real-time SSE stream
"""

import asyncio
import datetime
import json

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

app = FastAPI(title="Yamaguchi Dashboard API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Mock data — 13 tracking task groups (Excel-driven + DB-driven)
# Replace batches with real DB/API queries once dataapp event API is ready.
# ---------------------------------------------------------------------------
MOCK_TASK_GROUPS = [
    # ── Excel-driven ─────────────────────────────────────────────────────────
    {
        "id": "OWRYT",
        "label": "官网 → Yamato 追踪",
        "pipeline": "excel",
        "batches": [
            {
                "id": "owryt-b1",
                "source": "excel",
                "status": "running",
                "created_at": "2026-03-02T08:50:00",
                "completed_at": None,
                "total_jobs": 20,
                "completed_jobs": 13,
                "failed_jobs": 0,
                "detail": "OWRYT-20260302.xlsx",
            },
            {
                "id": "owryt-b2",
                "source": "excel",
                "status": "success",
                "created_at": "2026-03-01T09:00:00",
                "completed_at": "2026-03-01T09:38:00",
                "total_jobs": 18,
                "completed_jobs": 18,
                "failed_jobs": 0,
                "detail": "OWRYT-20260301.xlsx",
            },
        ],
    },
    {
        "id": "RTJPT",
        "label": "官网 → 日本郵便 追踪",
        "pipeline": "excel",
        "batches": [
            {
                "id": "rtjpt-b1",
                "source": "excel",
                "status": "success",
                "created_at": "2026-03-01T10:00:00",
                "completed_at": "2026-03-01T10:42:00",
                "total_jobs": 12,
                "completed_jobs": 12,
                "failed_jobs": 0,
                "detail": "RTJPT-20260301.xlsx",
            },
        ],
    },
    {
        "id": "OWT",
        "label": "官网直接追踪",
        "pipeline": "excel",
        "batches": [],
    },
    {
        "id": "YTO",
        "label": "Yamato 单件追踪",
        "pipeline": "excel",
        "batches": [
            {
                "id": "yto-b1",
                "source": "excel",
                "status": "error",
                "created_at": "2026-03-01T08:00:00",
                "completed_at": "2026-03-01T08:10:00",
                "total_jobs": 8,
                "completed_jobs": 3,
                "failed_jobs": 5,
                "detail": "YTO-20260301.xlsx · ConnectionError",
            },
        ],
    },
    {
        "id": "YT10",
        "label": "Yamato 10件批量",
        "pipeline": "excel",
        "batches": [
            {
                "id": "yt10-b1",
                "source": "excel",
                "status": "success",
                "created_at": "2026-03-01T07:30:00",
                "completed_at": "2026-03-01T07:55:00",
                "total_jobs": 30,
                "completed_jobs": 30,
                "failed_jobs": 0,
                "detail": "YT10-20260301.xlsx",
            },
        ],
    },
    {
        "id": "JPTO",
        "label": "日本郵便 单件追踪",
        "pipeline": "excel",
        "batches": [],
    },
    {
        "id": "JPT10",
        "label": "日本郵便 10件批量",
        "pipeline": "excel",
        "batches": [
            {
                "id": "jpt10-b1",
                "source": "excel",
                "status": "success",
                "created_at": "2026-03-02T07:00:00",
                "completed_at": "2026-03-02T07:22:00",
                "total_jobs": 40,
                "completed_jobs": 40,
                "failed_jobs": 0,
                "detail": "JPT10-20260302.xlsx",
            },
            {
                "id": "jpt10-b2",
                "source": "excel",
                "status": "success",
                "created_at": "2026-03-01T07:00:00",
                "completed_at": "2026-03-01T07:25:00",
                "total_jobs": 35,
                "completed_jobs": 35,
                "failed_jobs": 0,
                "detail": "JPT10-20260301.xlsx",
            },
        ],
    },
    # ── DB-driven ─────────────────────────────────────────────────────────────
    {
        "id": "TNE",
        "label": "追踪号补全",
        "pipeline": "db",
        "batches": [
            {
                "id": "tne-b1",
                "source": "db",
                "status": "running",
                "created_at": "2026-03-02T09:00:00",
                "completed_at": None,
                "total_jobs": 15,
                "completed_jobs": 7,
                "failed_jobs": 0,
                "detail": "purchasing_query_tracking_number_empty_a1b2",
            },
            {
                "id": "tne-b2",
                "source": "db",
                "status": "success",
                "created_at": "2026-03-01T09:00:00",
                "completed_at": "2026-03-01T09:28:00",
                "total_jobs": 20,
                "completed_jobs": 20,
                "failed_jobs": 0,
                "detail": "purchasing_query_tracking_number_empty_c3d4",
            },
        ],
    },
    {
        "id": "JPT10-DB",
        "label": "日本郵便批量 (DB)",
        "pipeline": "db",
        "batches": [
            {
                "id": "jpt10db-b1",
                "source": "db",
                "status": "success",
                "created_at": "2026-03-02T07:30:00",
                "completed_at": "2026-03-02T07:45:00",
                "total_jobs": 1,
                "completed_jobs": 1,
                "failed_jobs": 0,
                "detail": "purchasing_query_japan_post_tracking_10_e5f6",
            },
        ],
    },
    {
        "id": "CAE",
        "label": "确认日期补全",
        "pipeline": "db",
        "batches": [],
    },
    {
        "id": "SAE",
        "label": "发货日期补全",
        "pipeline": "db",
        "batches": [],
    },
    {
        "id": "EWAD",
        "label": "预计到达日补全",
        "pipeline": "db",
        "batches": [],
    },
    {
        "id": "TFC",
        "label": "灵活捕获",
        "pipeline": "db",
        "batches": [
            {
                "id": "tfc-b1",
                "source": "db",
                "status": "success",
                "created_at": "2026-03-01T06:00:00",
                "completed_at": "2026-03-01T06:15:00",
                "total_jobs": 5,
                "completed_jobs": 5,
                "failed_jobs": 0,
                "detail": "confirmed_at=notnull,batch_encoding=SPECIAL-20260301",
            },
        ],
    },
]


def _snapshot() -> dict:
    return {
        "timestamp": datetime.datetime.now().isoformat(),
        "task_groups": MOCK_TASK_GROUPS,
    }


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
    """Server-Sent Events endpoint — pushes task_groups snapshot every 10 seconds."""

    async def event_generator():
        while True:
            payload = json.dumps(_snapshot(), ensure_ascii=False)
            yield f"data: {payload}\n\n"
            await asyncio.sleep(10)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
