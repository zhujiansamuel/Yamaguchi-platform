"""
Yamaguchi Dashboard — minimal FastAPI backend
Provides:
  GET  /api/health          health check
  GET  /api/tasks           snapshot of all sections (JSON)
  GET  /api/tasks/stream    real-time SSE stream

Data model:
  sections[]
    └── task_groups[]
          └── batches[]
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
# Mock data — five sections:
#   Nextcloud sync / Webapp scraper / Excel tracking / DB tracking / Email
# Replace with real DB/API queries once event APIs are ready.
# ---------------------------------------------------------------------------

def _ws(sid, day, h, m, rr=0, ri=0, ru=0, rs=0, rum=0, status="success", err=None):
    """Helper to generate a webapp scraper ingestion event."""
    base = datetime.datetime(2026, 3, day, h, m)
    return {
        "id": f"wb-{sid}-030{day}",
        "source_name": sid,
        "task_type": "WEBSCRAPER",
        "timestamp": base.isoformat(),
        "status": status,
        "rows_received": rr,
        "rows_inserted": ri,
        "rows_updated": ru,
        "rows_skipped": rs,
        "rows_unmatched": rum,
        "error_message": err,
        "created_at": (base - datetime.timedelta(minutes=3)).isoformat(),
        "received_at": (base - datetime.timedelta(seconds=90)).isoformat(),
        "cleaning_started_at": (base - datetime.timedelta(seconds=60)).isoformat(),
        "completed_at": base.isoformat(),
    }


_NEXTCLOUD_SYNC = [
    {
        "id": "SYNC_PURCHASING",
        "label": "Purchasing",
        "pipeline": "nextcloud",
        "events": [
            {
                "id": "sync-pur-in1",
                "direction": "in",
                "timestamp": "2026-03-02T07:00:00",
                "record_count": 120,
                "conflict_count": 2,
                "trigger": "webhook",
                "status": "success",
                "detail": "从 Nextcloud 读取 Purchasing 数据，120 条记录",
            },
            {
                "id": "sync-pur-out1",
                "direction": "out",
                "timestamp": "2026-03-02T09:30:00",
                "record_count": 95,
                "conflict_count": 0,
                "trigger": "scheduled",
                "status": "success",
                "detail": "写出 Purchasing 数据到 Nextcloud，95 条记录",
            },
            {
                "id": "sync-pur-in2",
                "direction": "in",
                "timestamp": "2026-03-01T07:00:00",
                "record_count": 108,
                "conflict_count": 0,
                "trigger": "webhook",
                "status": "success",
                "detail": "从 Nextcloud 读取 Purchasing 数据，108 条记录",
            },
            {
                "id": "sync-pur-out2",
                "direction": "out",
                "timestamp": "2026-03-01T09:30:00",
                "record_count": 90,
                "conflict_count": 0,
                "trigger": "scheduled",
                "status": "success",
                "detail": "写出 Purchasing 数据到 Nextcloud，90 条记录",
            },
        ],
    },
    {
        "id": "SYNC_OFFICIAL_ACCOUNT",
        "label": "OfficialAccount",
        "pipeline": "nextcloud",
        "events": [
            {
                "id": "sync-oa-in1",
                "direction": "in",
                "timestamp": "2026-03-02T07:02:00",
                "record_count": 45,
                "conflict_count": 0,
                "trigger": "webhook",
                "status": "success",
                "detail": "从 Nextcloud 读取 OfficialAccount 数据，45 条记录",
            },
            {
                "id": "sync-oa-in2",
                "direction": "in",
                "timestamp": "2026-03-01T07:02:00",
                "record_count": 42,
                "conflict_count": 0,
                "trigger": "webhook",
                "status": "success",
                "detail": "从 Nextcloud 读取 OfficialAccount 数据，42 条记录",
            },
        ],
    },
    {
        "id": "SYNC_GIFT_CARD",
        "label": "GiftCard",
        "pipeline": "nextcloud",
        "events": [
            {
                "id": "sync-gc-in1",
                "direction": "in",
                "timestamp": "2026-03-02T07:05:00",
                "record_count": 30,
                "conflict_count": 0,
                "trigger": "scheduled",
                "status": "success",
                "detail": "从 Nextcloud 读取 GiftCard 数据，30 条记录",
            },
            {
                "id": "sync-gc-in2",
                "direction": "in",
                "timestamp": "2026-03-01T07:05:00",
                "record_count": 28,
                "conflict_count": 0,
                "trigger": "scheduled",
                "status": "success",
                "detail": "从 Nextcloud 读取 GiftCard 数据，28 条记录",
            },
        ],
    },
    {
        "id": "SYNC_DEBIT_CARD",
        "label": "DebitCard",
        "pipeline": "nextcloud",
        "events": [
            {
                "id": "sync-dc-in1",
                "direction": "in",
                "timestamp": "2026-03-02T07:08:00",
                "record_count": 15,
                "conflict_count": 0,
                "trigger": "scheduled",
                "status": "success",
                "detail": "从 Nextcloud 读取 DebitCard 数据，15 条记录",
            },
            {
                "id": "sync-dc-in2",
                "direction": "in",
                "timestamp": "2026-03-01T07:08:00",
                "record_count": 0,
                "conflict_count": 0,
                "trigger": "scheduled",
                "status": "error",
                "detail": "读取 DebitCard 失败：Nextcloud 连接超时",
            },
        ],
    },
    {
        "id": "SYNC_CREDIT_CARD",
        "label": "CreditCard",
        "pipeline": "nextcloud",
        "events": [
            {
                "id": "sync-cc-in1",
                "direction": "in",
                "timestamp": "2026-03-02T07:10:00",
                "record_count": 22,
                "conflict_count": 1,
                "trigger": "webhook",
                "status": "success",
                "detail": "从 Nextcloud 读取 CreditCard 数据，22 条记录",
            },
            {
                "id": "sync-cc-out1",
                "direction": "out",
                "timestamp": "2026-03-02T09:35:00",
                "record_count": 20,
                "conflict_count": 0,
                "trigger": "scheduled",
                "status": "success",
                "detail": "写出 CreditCard 数据到 Nextcloud，20 条记录",
            },
        ],
    },
    {
        "id": "SYNC_TEMPORARY_CHANNEL",
        "label": "TemporaryChannel",
        "pipeline": "nextcloud",
        "events": [
            {
                "id": "sync-tc-in1",
                "direction": "in",
                "timestamp": "2026-03-02T07:15:00",
                "record_count": 8,
                "conflict_count": 0,
                "trigger": "scheduled",
                "status": "success",
                "detail": "从 Nextcloud 读取 TemporaryChannel 数据，8 条记录",
            },
        ],
    },
]

_WEBAPP_SCRAPER = [
    {"id": "WEBAPP_SHOP1",  "label": "shop1",  "pipeline": "webapp", "events": [
        _ws("shop1",  2, 6, 31, 148, 120, 18, 7, 3),
        _ws("shop1",  1, 6, 30, 145, 115, 20, 8, 2),
    ]},
    {"id": "WEBAPP_SHOP2",  "label": "shop2",  "pipeline": "webapp", "events": [
        _ws("shop2",  2, 6, 34, 215, 178, 25, 8, 4),
        _ws("shop2",  1, 6, 33, 210, 172, 28, 7, 3),
    ]},
    {"id": "WEBAPP_SHOP3",  "label": "shop3",  "pipeline": "webapp", "events": [
        _ws("shop3",  2, 6, 37,  82,  70,  8, 3, 1),
        _ws("shop3",  1, 6, 36,   0, status="error",
            err="WebScraper.io API 返回 503：服务暂时不可用"),
    ]},
    {"id": "WEBAPP_SHOP4",  "label": "shop4",  "pipeline": "webapp", "events": [
        _ws("shop4",  2, 6, 40, 125, 100, 15, 8, 2),
        _ws("shop4",  1, 6, 39, 122,  98, 16, 6, 2),
    ]},
    {"id": "WEBAPP_SHOP5",  "label": "shop5",  "pipeline": "webapp", "events": [
        _ws("shop5",  2, 6, 45, 312, 260, 38, 10, 4),
        _ws("shop5",  1, 6, 44, 308, 255, 40,  9, 4),
    ]},
    {"id": "WEBAPP_SHOP6",  "label": "shop6",  "pipeline": "webapp", "events": [
        _ws("shop6",  2, 6, 50, 268, 220, 32, 12, 4),
        _ws("shop6",  1, 6, 49, 265, 218, 34,  9, 4),
    ]},
    {"id": "WEBAPP_SHOP7",  "label": "shop7",  "pipeline": "webapp", "events": [
        _ws("shop7",  2, 6, 53,  65, status="error",
            err="清洗失败：KeyError 'jan_code' in shop7_cleaner"),
        _ws("shop7",  1, 6, 52,  65,  52,  8, 3, 2),
    ]},
    {"id": "WEBAPP_SHOP8",  "label": "shop8",  "pipeline": "webapp", "events": [
        _ws("shop8",  2, 6, 56,  92,  76, 12, 3, 1),
        _ws("shop8",  1, 6, 55,  90,  74, 12, 3, 1),
    ]},
    {"id": "WEBAPP_SHOP9",  "label": "shop9",  "pipeline": "webapp", "events": [
        _ws("shop9",  2, 6, 59,  47,  38,  6, 2, 1),
        _ws("shop9",  1, 6, 58,  45,  36,  6, 2, 1),
    ]},
    {"id": "WEBAPP_SHOP10", "label": "shop10", "pipeline": "webapp", "events": [
        _ws("shop10", 2, 7,  2, 188, 155, 22, 9, 2),
        _ws("shop10", 1, 7,  1, 185, 152, 24, 7, 2),
    ]},
    {"id": "WEBAPP_SHOP11", "label": "shop11", "pipeline": "webapp", "events": [
        _ws("shop11", 2, 7,  5,  78,  64,  9, 4, 1),
        _ws("shop11", 1, 7,  4,  76,  62,  9, 4, 1),
    ]},
    {"id": "WEBAPP_SHOP12", "label": "shop12", "pipeline": "webapp", "events": [
        _ws("shop12", 2, 7,  8, 115,  94, 16, 4, 1),
        _ws("shop12", 1, 7,  7, 112,  92, 14, 5, 1),
    ]},
    {"id": "WEBAPP_SHOP13", "label": "shop13", "pipeline": "webapp", "events": [
        _ws("shop13", 2, 7, 11,  98,  82, 11, 4, 1),
        _ws("shop13", 1, 7, 10,  95,  80, 10, 4, 1),
    ]},
    {"id": "WEBAPP_SHOP14", "label": "shop14", "pipeline": "webapp", "events": [
        _ws("shop14", 2, 7, 14, 135, 110, 18, 5, 2),
        _ws("shop14", 1, 7, 13, 132, 108, 18, 4, 2),
    ]},
    {"id": "WEBAPP_SHOP15", "label": "shop15", "pipeline": "webapp", "events": [
        _ws("shop15", 2, 7, 17,  88,  72, 10, 5, 1),
        _ws("shop15", 1, 7, 16,  86,  70, 10, 5, 1),
    ]},
    {"id": "WEBAPP_SHOP16", "label": "shop16", "pipeline": "webapp", "events": [
        _ws("shop16", 2, 7, 20,  58,  47,  7, 3, 1),
        _ws("shop16", 1, 7, 19,  56,  45,  7, 3, 1),
    ]},
    {"id": "WEBAPP_SHOP17", "label": "shop17", "pipeline": "webapp", "events": [
        _ws("shop17", 2, 7, 23, 165, 135, 22, 6, 2),
        _ws("shop17", 1, 7, 22, 162, 132, 22, 6, 2),
    ]},
    {"id": "WEBAPP_SHOP18", "label": "shop18", "pipeline": "webapp", "events": [
        _ws("shop18", 2, 7, 26,  72,  58,  9, 4, 1),
        _ws("shop18", 1, 7, 25,  70,  56, 10, 3, 1),
    ]},
    {"id": "WEBAPP_SHOP19", "label": "shop19", "pipeline": "webapp", "events": [
        _ws("shop19", 2, 7, 29,  43,  35,  5, 2, 1),
        _ws("shop19", 1, 7, 28,  41,  33,  5, 2, 1),
    ]},
    {"id": "WEBAPP_SHOP20", "label": "shop20", "pipeline": "webapp", "events": [
        _ws("shop20", 2, 7, 32, 102,  84, 13, 4, 1),
        _ws("shop20", 1, 7, 31, 100,  82, 13, 4, 1),
    ]},
]

_EXCEL_TRACKING = [
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
]

_DB_TRACKING = [
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
    {"id": "CAE", "label": "确认日期补全", "pipeline": "db", "batches": []},
    {"id": "SAE", "label": "发货日期补全", "pipeline": "db", "batches": []},
    {"id": "EWAD", "label": "预计到达日补全", "pipeline": "db", "batches": []},
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

_EMAIL_PROCESSING = [
    {
        "id": "EMAIL_ANALYSIS",
        "label": "邮件内容分析",
        "pipeline": "email",
        "batches": [
            {
                "id": "ea-b1",
                "source": "email",
                "status": "success",
                "created_at": "2026-03-02T08:00:00",
                "completed_at": "2026-03-02T08:03:00",
                "total_jobs": 45,
                "completed_jobs": 45,
                "failed_jobs": 0,
                "detail": "解析 45 封邮件，提取订单/商品/日期等结构化数据",
            },
            {
                "id": "ea-b2",
                "source": "email",
                "status": "success",
                "created_at": "2026-03-01T08:00:00",
                "completed_at": "2026-03-01T08:02:00",
                "total_jobs": 32,
                "completed_jobs": 32,
                "failed_jobs": 0,
                "detail": "解析 32 封邮件，提取订单/商品/日期等结构化数据",
            },
        ],
    },
    {
        "id": "EMAIL_INITIAL_ORDER",
        "label": "初始订单确认",
        "pipeline": "email",
        "batches": [
            {
                # Today: still running (waiting for email analysis to propagate)
                "id": "eio-b1",
                "source": "email",
                "status": "running",
                "created_at": "2026-03-02T08:03:00",
                "completed_at": None,
                "total_jobs": 45,
                "completed_jobs": 38,
                "failed_jobs": 0,
                "detail": "创建/更新 Purchasing 记录，关联 OfficialAccount",
            },
            {
                "id": "eio-b2",
                "source": "email",
                "status": "success",
                "created_at": "2026-03-01T08:02:00",
                "completed_at": "2026-03-01T08:18:00",
                "total_jobs": 32,
                "completed_jobs": 32,
                "failed_jobs": 0,
                "detail": "创建/更新 Purchasing 记录，关联 OfficialAccount",
            },
        ],
    },
    {
        "id": "EMAIL_NOTIFICATION",
        "label": "订单确认通知",
        "pipeline": "email",
        # No batch today — waiting for initial order to finish
        "batches": [
            {
                "id": "en-b1",
                "source": "email",
                "status": "success",
                "created_at": "2026-03-01T08:18:00",
                "completed_at": "2026-03-01T08:25:00",
                "total_jobs": 28,
                "completed_jobs": 28,
                "failed_jobs": 0,
                "detail": "更新 28 条 Purchasing 记录状态",
            },
        ],
    },
    {
        "id": "EMAIL_SEND",
        "label": "发送通知邮件",
        "pipeline": "email",
        # No batch today — waiting for notification step
        "batches": [
            {
                "id": "es-b1",
                "source": "email",
                "status": "success",
                "created_at": "2026-03-01T08:25:00",
                "completed_at": "2026-03-01T08:30:00",
                "total_jobs": 28,
                "completed_jobs": 28,
                "failed_jobs": 0,
                "detail": "向用户发送确认通知邮件",
            },
        ],
    },
]

MOCK_SECTIONS = [
    {
        "id": "nextcloud_sync",
        "label": "Nextcloud 数据同步",
        "task_groups": _NEXTCLOUD_SYNC,
    },
    {
        "id": "webapp_scraper",
        "label": "价格抓取（Webapp）",
        "task_groups": _WEBAPP_SCRAPER,
    },
    {
        "id": "excel_tracking",
        "label": "追踪任务（Excel 驱动）",
        "task_groups": _EXCEL_TRACKING,
    },
    {
        "id": "db_tracking",
        "label": "追踪任务（DB 驱动）",
        "task_groups": _DB_TRACKING,
    },
    {
        "id": "email",
        "label": "邮件处理",
        "task_groups": _EMAIL_PROCESSING,
    },
]


def _snapshot() -> dict:
    return {
        "timestamp": datetime.datetime.now().isoformat(),
        "sections": MOCK_SECTIONS,
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
