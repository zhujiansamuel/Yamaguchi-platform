"""
Yamaguchi Dashboard — minimal FastAPI backend
Provides:
  GET  /api/health          health check
  GET  /api/tasks           snapshot of all tasks (JSON)
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
# Mock data — replace each entry with real API calls once services are ready
# ---------------------------------------------------------------------------
MOCK_TASKS = [
    {
        "id": "1",
        "source": "dataapp",
        "title": "数据同步 · Nextcloud WebDAV",
        "status": "running",
        "color": "blue",
        "started_at": "2026-03-01T09:00:00",
        "updated_at": "2026-03-01T09:15:00",
        "detail": "正在从 Nextcloud 拉取最新 Excel 文件",
    },
    {
        "id": "2",
        "source": "dataapp",
        "title": "Celery Worker · 邮件解析",
        "status": "success",
        "color": "green",
        "started_at": "2026-03-01T08:00:00",
        "updated_at": "2026-03-01T08:45:00",
        "detail": "共处理 32 封邮件，入库成功",
    },
    {
        "id": "3",
        "source": "ecsite",
        "title": "商品价格批量更新",
        "status": "success",
        "color": "green",
        "started_at": "2026-03-01T07:30:00",
        "updated_at": "2026-03-01T07:55:00",
        "detail": "更新 SKU 数量：1,204",
    },
    {
        "id": "4",
        "source": "dataapp",
        "title": "Yamato 快递追踪同步",
        "status": "pending",
        "color": "gray",
        "started_at": None,
        "updated_at": "2026-03-01T09:00:00",
        "detail": "等待上一步骤完成后触发",
    },
    {
        "id": "5",
        "source": "webapp",
        "title": "库存报表生成",
        "status": "error",
        "color": "red",
        "started_at": "2026-03-01T06:00:00",
        "updated_at": "2026-03-01T06:10:00",
        "detail": "ConnectionError: database timeout (将在 10 分钟后重试)",
    },
]


def _snapshot() -> dict:
    return {
        "timestamp": datetime.datetime.now().isoformat(),
        "tasks": MOCK_TASKS,
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
    """Server-Sent Events endpoint — pushes task snapshot every 5 seconds."""

    async def event_generator():
        while True:
            payload = json.dumps(_snapshot(), ensure_ascii=False)
            yield f"data: {payload}\n\n"
            await asyncio.sleep(5)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # disable nginx buffering for SSE
        },
    )
