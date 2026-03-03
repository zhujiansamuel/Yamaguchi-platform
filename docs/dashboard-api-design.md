# Dashboard API 设计说明

> 版本：v1.0 · 日期：2026-03-03
> 适用范围：dashboard 后端（FastAPI）与 dataapp（Django 5.2）、webapp（Django 5.2）的集成对接

---

## 1. 总体架构

```
┌─────────────────────────────────────────────────┐
│              浏览器 / 移动端                      │
│          Vue 3 前端（dashboard/frontend）         │
└──────────────────────┬──────────────────────────┘
                       │ SSE / HTTP
                       ▼
┌─────────────────────────────────────────────────┐
│       Dashboard 后端  (dashboard/backend)        │
│       FastAPI · /api/tasks/stream (SSE)          │
│       /api/tasks (snapshot)                      │
│                                                  │
│  每 30 秒聚合一次下游数据，缓存后推送至前端         │
└──────────┬────────────────────────┬─────────────┘
           │ HTTP + Token           │ HTTP + Token
           ▼                        ▼
┌──────────────────────┐  ┌──────────────────────┐
│  dataapp             │  │  webapp               │
│  Django 5.2 + DRF    │  │  Django 5.2 + DRF    │
│                      │  │                      │
│  /api/acquisition/   │  │  /api/dashboard/      │
│  dashboard/...       │  │  scraper-events/      │
└──────────────────────┘  └──────────────────────┘
           │                        │
           ▼                        ▼
    PostgreSQL (dataapp)    PostgreSQL (webapp)
```

Dashboard 后端**不直接访问数据库**，只调用下游项目的 REST API。

---

## 2. 通用约定

### 2.1 认证

下游 API 均使用 DRF Token 认证（`SimpleTokenAuthentication`）。

```
Authorization: Token <service_token>
```

每个项目各创建一个只读 Service Account Token，存入 Dashboard 后端环境变量。

| 环境变量 | 说明 |
|---------|------|
| `DATAAPP_API_URL` | 如 `http://dataapp:8000` |
| `DATAAPP_SERVICE_TOKEN` | dataapp 服务账户 Token |
| `WEBAPP_API_URL` | 如 `http://webapp:8000` |
| `WEBAPP_SERVICE_TOKEN` | webapp 服务账户 Token |

### 2.2 时间窗口

所有接口默认返回 **最近 2 天** 的数据（`?days=2`）。
Dashboard 后端调用时固定传 `days=2`，前端时间轴范围由数据自动计算。

### 2.3 错误处理

- 下游接口调用失败时，Dashboard 后端返回**上次缓存的数据**，同时在 section 上附加 `"stale": true` 标记。
- 若从未成功获取，则该 section 返回空数组。

### 2.4 缓存策略

- 全量快照：每 **30 秒** 从下游拉取一次，结果存内存。
- SSE 推送：每 **10 秒** 推一次（取缓存），`now` 时钟由前端本地维护。
- 单次下游请求超时：`10s`。

---

## 3. 各 Section API 设计

### 3.1 Nextcloud 数据同步

**数据来源：** `dataapp` · 模型 `SyncLog` + `NextcloudSyncState`

**现有模型字段（已有，无需新增）：**

```python
# SyncLog（data_acquisition/models.py）
operation_type   # 区分 in/out 的关键字段（见下方映射）
sync_state       # FK → NextcloudSyncState
success          # bool
error_message    # 失败原因
created_at       # 事件时间戳
celery_task_id
details          # JSONField，存放 record_count / conflict_count / trigger / detail

# NextcloudSyncState（data_acquisition/models.py）
model_name       # Purchasing / OfficialAccount / GiftCard / ...
file_path        # Nextcloud 文件路径
```

**operation_type 与 direction 映射：**

| operation_type | dashboard direction | 含义 |
|---------------|---------------------|------|
| `sync_completed` | `"in"` | Excel → DB 同步完成 |
| `sync_failed` | `"in"` | Excel → DB 同步失败 |
| `excel_writeback` | `"out"` | DB → Excel 回写完成 |
| `writeback_skipped` | `"out"` (可忽略) | 回写跳过 |

**SyncLog.details 约定格式（需在 dataapp 写入时保证）：**

```json
{
  "record_count": 120,
  "conflict_count": 2,
  "trigger": "webhook",
  "detail": "从 Nextcloud 读取 Purchasing 数据，120 条记录"
}
```

**需新增的 dataapp 接口：**

```
GET /api/acquisition/dashboard/nextcloud-sync/
Authorization: Token <service_token>
Query: ?days=2
```

响应：

```json
[
  {
    "model_name": "Purchasing",
    "events": [
      {
        "id": "synclog-uuid",
        "direction": "in",
        "timestamp": "2026-03-02T07:00:00",
        "record_count": 120,
        "conflict_count": 2,
        "trigger": "webhook",
        "status": "success",
        "detail": "从 Nextcloud 读取 Purchasing 数据，120 条记录"
      }
    ]
  },
  ...
]
```

**查询逻辑（dataapp 视图实现参考）：**

```python
from django.utils import timezone
from datetime import timedelta

since = timezone.now() - timedelta(days=days)

# 按 model_name 分组
states = NextcloudSyncState.objects.all()
for state in states:
    logs = SyncLog.objects.filter(
        sync_state=state,
        operation_type__in=['sync_completed', 'sync_failed',
                            'excel_writeback'],
        created_at__gte=since,
    ).order_by('-created_at')
    # 转换并输出
```

---

### 3.2 追踪任务（Excel 驱动 & DB 驱动）

**数据来源：** `dataapp` · 模型 `TrackingBatch`

**现有模型字段（已有，无需新增）：**

```python
# TrackingBatch（data_acquisition/models.py）
batch_uuid       # UUID
task_name        # 任务类型标识（见下方任务列表）
total_jobs       # 总 job 数
completed_jobs   # 已完成
failed_jobs      # 失败数
status           # pending / processing / completed / partial
created_at
completed_at
```

**status 字段映射至 dashboard：**

| TrackingBatch.status | dashboard status |
|---------------------|-----------------|
| `pending` | `pending` |
| `processing` | `running` |
| `completed` | `success` |
| `partial` | `error`（部分失败，error_message 注明） |

**已知 task_name 与分类：**

| task_name | 分类 | dashboard label |
|-----------|------|----------------|
| `official_website_redirect_to_yamato_tracking` | excel | 官网 → Yamato 追踪 |
| `redirect_to_japan_post_tracking_10` (待确认) | excel | — |
| `japan_post_tracking_order` (待确认) | excel | — |
| `japan_post_tracking_10` (待确认) | excel | — |
| `yamato_to_official_website` (待确认) | excel | — |
| `return_to_japan_post_tracking` (待确认) | excel | — |
| `outbound_webscraper_tracking` (待确认) | excel | — |
| `purchasing_query_*` 前缀 | db | DB 驱动追踪 |

> ⚠️ 建议在 `TrackingBatch` 增加 `source_type` 字段（`excel` / `db`），
> 避免依赖 `task_name` 前缀做分类判断。

**需新增的 dataapp 接口：**

```
GET /api/acquisition/dashboard/tracking-batches/
Authorization: Token <service_token>
Query: ?days=2
```

响应（所有 TrackingBatch 按 task_name 分组，Excel 和 DB 混合返回，由 Dashboard 后端二次分组）：

```json
[
  {
    "task_name": "official_website_redirect_to_yamato_tracking",
    "source_type": "excel",
    "label": "官网 → Yamato 追踪",
    "batches": [
      {
        "id": "batch-uuid",
        "created_at": "2026-03-02T08:00:00",
        "completed_at": "2026-03-02T08:45:00",
        "status": "success",
        "total_jobs": 10,
        "completed_jobs": 10,
        "failed_jobs": 0,
        "source": "excel",
        "detail": "OWRYT-20260302 共 10 条"
      }
    ]
  },
  ...
]
```

**备注：**

- `label` 字段由 dataapp 维护（参考 `TRACKING_TASK_CONFIGS` 中的描述）
- 若 `source_type` 字段还未添加，Dashboard 后端可根据 `task_name` 是否包含 `purchasing_query_` 做临时区分

---

### 3.3 邮件处理

**数据来源：** `dataapp` · **需新增** `EmailProcessingLog` 模型

**现有相关模型：**

```python
# MailMessage（data_aggregation/models.py）
ingested_at      # 邮件摄取时间
is_extracted     # 是否已提取订单信息
```

**建议新增模型（data_aggregation/models.py）：**

```python
class EmailProcessingLog(models.Model):
    STAGE_CHOICES = [
        ('analysis',      '邮件分析'),
        ('initial_order', '初始确认'),
        ('notification',  '通知生成'),
        ('send',          '邮件发送'),
    ]
    STATUS_CHOICES = [
        ('pending',    '待处理'),
        ('running',    '进行中'),
        ('success',    '成功'),
        ('error',      '异常'),
    ]

    stage          = models.CharField(max_length=30, choices=STAGE_CHOICES)
    status         = models.CharField(max_length=20, choices=STATUS_CHOICES)
    celery_task_id = models.CharField(max_length=255, blank=True)
    total_items    = models.IntegerField(default=0)   # 处理邮件总数
    completed_items = models.IntegerField(default=0)
    failed_items   = models.IntegerField(default=0)
    error_message  = models.TextField(blank=True)
    created_at     = models.DateTimeField(auto_now_add=True)
    completed_at   = models.DateTimeField(null=True, blank=True)
    detail         = models.TextField(blank=True)

    class Meta:
        db_table = 'email_processing_logs'
        indexes = [models.Index(fields=['stage', 'created_at'])]
```

**需新增的 dataapp 接口：**

```
GET /api/aggregation/dashboard/email-tasks/
Authorization: Token <service_token>
Query: ?days=2
```

响应（4 个阶段各返回最近批次）：

```json
[
  {
    "stage": "analysis",
    "label": "邮件分析",
    "batches": [
      {
        "id": "log-uuid",
        "created_at": "2026-03-02T09:00:00",
        "completed_at": "2026-03-02T09:02:00",
        "status": "success",
        "total_jobs": 12,
        "completed_jobs": 12,
        "failed_jobs": 0,
        "source": "email",
        "detail": "分析 12 封新邮件"
      }
    ]
  },
  {
    "stage": "initial_order",
    "label": "初始确认",
    "batches": [
      {
        "id": "log-uuid",
        "created_at": "2026-03-02T09:05:00",
        "completed_at": null,
        "status": "running",
        "total_jobs": 12,
        "completed_jobs": 7,
        "failed_jobs": 0,
        "source": "email",
        "detail": "生成初始确认邮件"
      }
    ]
  },
  {
    "stage": "notification",
    "label": "通知生成",
    "batches": [{ ..., "created_at": null, "status": "pending" }]
  },
  {
    "stage": "send",
    "label": "邮件发送",
    "batches": [{ ..., "created_at": null, "status": "pending" }]
  }
]
```

**`created_at: null` 的含义：** 该阶段尚未触发（pipeline 等待上游完成）。前端已有"等待触发"处理逻辑。

---

### 3.4 价格抓取（Webapp）

**数据来源：** `webapp` · 模型 `DataIngestionLog`（已有，直接对接）

**现有模型字段：**

```python
# DataIngestionLog（AppleStockChecker/models.py）
batch_id           # UUID（主键）
source_name        # shop1 ~ shop20（含 shop5_1 等子源）
task_type          # XLSX / WEBSCRAPER / JSON_SHOP1
status             # PENDING / RECEIVING / CLEANING / COMPLETED / FAILED
created_at
received_at        # 下载完成
cleaning_started_at
completed_at
rows_received
rows_after_cleaning  # 清洗后行数（对应 dashboard rows_inserted 近似值）
rows_inserted
rows_updated
rows_skipped
rows_unmatched
error_message
dry_run, dedupe, upsert  # 配置标志
```

**source_name 合并规则（shop5_1~5_4 → shop5）：**

由 webapp API 视图在聚合时完成，使用正则 `^(shop\d+)` 提取父级 shop 名称。

**需新增的 webapp 接口：**

```
GET /api/dashboard/scraper-events/
Authorization: Token <service_token>
Query: ?days=2
```

响应（按父级 source 分组，每组内按 completed_at 倒序）：

```json
[
  {
    "source_name": "shop1",
    "events": [
      {
        "id": "batch-uuid",
        "source_name": "shop1",
        "task_type": "WEBSCRAPER",
        "timestamp": "2026-03-02T06:31:00",
        "status": "success",
        "rows_received": 148,
        "rows_inserted": 120,
        "rows_updated": 18,
        "rows_skipped": 7,
        "rows_unmatched": 3,
        "error_message": null,
        "created_at": "2026-03-02T06:28:00",
        "received_at": "2026-03-02T06:29:30",
        "cleaning_started_at": "2026-03-02T06:29:35",
        "completed_at": "2026-03-02T06:31:00"
      }
    ]
  },
  ...
]
```

**`timestamp` 字段：** 取 `completed_at`（已完成）或 `created_at`（失败时）。

**`status` 映射：**

| DataIngestionLog.status | dashboard status |
|------------------------|-----------------|
| `PENDING` | `pending` |
| `RECEIVING` | `running` |
| `CLEANING` | `running` |
| `COMPLETED` | `success` |
| `FAILED` | `error` |

---

## 4. Dashboard 后端聚合逻辑

### 4.1 配置（backend/config.py，待创建）

```python
import os

DATAAPP_API_URL   = os.getenv("DATAAPP_API_URL",   "http://dataapp:8000")
DATAAPP_TOKEN     = os.getenv("DATAAPP_SERVICE_TOKEN", "")
WEBAPP_API_URL    = os.getenv("WEBAPP_API_URL",    "http://webapp:8000")
WEBAPP_TOKEN      = os.getenv("WEBAPP_SERVICE_TOKEN",  "")
FETCH_INTERVAL_S  = int(os.getenv("FETCH_INTERVAL_S", "30"))
FETCH_TIMEOUT_S   = int(os.getenv("FETCH_TIMEOUT_S",  "10"))
TIME_WINDOW_DAYS  = int(os.getenv("TIME_WINDOW_DAYS",  "2"))
```

### 4.2 聚合流程（backend/main.py 重构目标）

```python
import httpx
import asyncio

_cache: dict = {}        # {"sections": [...], "timestamp": float, "stale": bool}
_lock = asyncio.Lock()

async def _fetch_json(url: str, token: str) -> dict | list | None:
    try:
        async with httpx.AsyncClient(timeout=FETCH_TIMEOUT_S) as client:
            r = await client.get(url, headers={"Authorization": f"Token {token}"})
            r.raise_for_status()
            return r.json()
    except Exception as e:
        logger.warning(f"Failed to fetch {url}: {e}")
        return None

async def _refresh_sections():
    async with _lock:
        # 并发拉取 4 个下游接口
        days = f"?days={TIME_WINDOW_DAYS}"
        nextcloud, tracking, email, scraper = await asyncio.gather(
            _fetch_json(f"{DATAAPP_API_URL}/api/acquisition/dashboard/nextcloud-sync/{days}", DATAAPP_TOKEN),
            _fetch_json(f"{DATAAPP_API_URL}/api/acquisition/dashboard/tracking-batches/{days}", DATAAPP_TOKEN),
            _fetch_json(f"{DATAAPP_API_URL}/api/aggregation/dashboard/email-tasks/{days}", DATAAPP_TOKEN),
            _fetch_json(f"{WEBAPP_API_URL}/api/dashboard/scraper-events/{days}", WEBAPP_TOKEN),
        )

        sections = []
        sections.append(_build_nextcloud_section(nextcloud))
        sections.append(_build_webapp_section(scraper))
        sections.append(_build_tracking_section(tracking, source_type="excel"))
        sections.append(_build_tracking_section(tracking, source_type="db"))
        sections.append(_build_email_section(email))

        _cache["sections"]  = sections
        _cache["timestamp"] = time.time()
        _cache["stale"]     = any(x is None for x in [nextcloud, tracking, email, scraper])
```

### 4.3 构建函数签名

```python
def _build_nextcloud_section(data: list | None) -> dict:
    """data: [{model_name, events:[{id, direction, timestamp, ...}]}]"""

def _build_webapp_section(data: list | None) -> dict:
    """data: [{source_name, events:[{id, source_name, timestamp, ...}]}]"""

def _build_tracking_section(data: list | None, *, source_type: str) -> dict:
    """
    data: [{task_name, source_type, label, batches:[...]}]
    source_type: "excel" | "db"
    过滤 data 中 source_type 匹配的分组。
    """

def _build_email_section(data: list | None) -> dict:
    """data: [{stage, label, batches:[...]}]"""
```

### 4.4 定时刷新

```python
@app.on_event("startup")
async def start_refresh_loop():
    async def loop():
        while True:
            await _refresh_sections()
            await asyncio.sleep(FETCH_INTERVAL_S)
    asyncio.create_task(loop())
```

---

## 5. 各项目需要新增 / 修改的内容

### 5.1 dataapp（data_acquisition app）

| 类型 | 文件 | 内容 |
|------|------|------|
| 新增视图 | `views.py` 或新建 `dashboard_views.py` | `NextcloudSyncDashboardView` |
| 新增视图 | 同上 | `TrackingBatchDashboardView` |
| 新增序列化器 | `serializers.py` 或新建 | Nextcloud + Tracking 序列化器 |
| 修改 URL | `urls.py` | 新增 `/dashboard/` 前缀路由 |
| 修改 SyncLog | 写入逻辑 | 确保 `details` JSON 包含 `record_count`、`conflict_count`、`trigger`、`detail` |
| 建议新增字段 | `TrackingBatch` 模型 | `source_type = CharField(choices=['excel','db'], max_length=10)` |
| 生成 migration | — | 若新增 `source_type` 字段 |

### 5.2 dataapp（data_aggregation app）

| 类型 | 文件 | 内容 |
|------|------|------|
| 新增模型 | `models.py` | `EmailProcessingLog`（见 §3.3 定义） |
| 新增 migration | — | 对应 `EmailProcessingLog` |
| 修改 Celery 任务 | email 相关 tasks | 在各阶段开始/结束时写入 `EmailProcessingLog` |
| 新增视图 | `views.py` 或新建 | `EmailTaskDashboardView` |
| 新增序列化器 | `serializers.py` | Email 序列化器 |
| 修改 URL | `urls.py` | 新增 `/dashboard/` 路由 |

### 5.3 webapp（AppleStockChecker app）

| 类型 | 文件 | 内容 |
|------|------|------|
| 新增视图 | `views.py` 或新建 `dashboard_views.py` | `ScraperEventDashboardView` |
| 新增序列化器 | `serializers.py` 或新建 | `DataIngestionLogDashboardSerializer` |
| 修改 URL | `urls.py` | 新增 `/api/dashboard/scraper-events/` 路由 |
| 创建 Service Token | Django Admin | 创建只读服务账户 |

### 5.4 Dashboard 后端（dashboard/backend）

| 类型 | 文件 | 内容 |
|------|------|------|
| 新增配置 | `config.py`（新建） | 下游 URL + Token + 间隔参数 |
| 重构 `main.py` | `main.py` | 删除 mock 数据，改用 `_refresh_sections()` 聚合 |
| 新增转换逻辑 | `builders.py`（新建） | 4 个 `_build_*_section()` 函数 |
| 修改 docker-compose | `docker-compose.yml` | 注入 4 个环境变量 |

---

## 6. 字段映射速查表

### Nextcloud → Dashboard Event

| 来源字段 | dashboard event 字段 | 说明 |
|---------|---------------------|------|
| `SyncLog.id` (str) | `id` | |
| `operation_type` | `direction` | `sync_*` → `"in"`, `excel_writeback` → `"out"` |
| `created_at` | `timestamp` | |
| `details.record_count` | `record_count` | |
| `details.conflict_count` | `conflict_count` | |
| `details.trigger` | `trigger` | `"webhook"` \| `"scheduled"` |
| `success` | `status` | `True` → `"success"`, `False` → `"error"` |
| `error_message` | （modal 内展示） | |
| `details.detail` | `detail` | |
| `sync_state.model_name` | group `label` | |

### TrackingBatch → Dashboard Batch

| 来源字段 | dashboard batch 字段 | 说明 |
|---------|---------------------|------|
| `batch_uuid` | `id` | |
| `created_at` | `created_at` | |
| `completed_at` | `completed_at` | |
| `status` | `status` | 见 §3.2 映射表 |
| `total_jobs` | `total_jobs` | |
| `completed_jobs` | `completed_jobs` | |
| `failed_jobs` | `failed_jobs` | |
| `source_type` | `source` | `"excel"` \| `"db"` |
| `task_name` | （用于分组） | |

### DataIngestionLog → Dashboard Event

| 来源字段 | dashboard event 字段 | 说明 |
|---------|---------------------|------|
| `batch_id` | `id` | |
| `source_name` | `source_name` | |
| `task_type` | `task_type` | |
| `completed_at` 或 `created_at` | `timestamp` | 优先 `completed_at` |
| `status` | `status` | 见 §3.4 映射表 |
| `rows_received` | `rows_received` | |
| `rows_inserted` | `rows_inserted` | |
| `rows_updated` | `rows_updated` | |
| `rows_skipped` | `rows_skipped` | |
| `rows_unmatched` | `rows_unmatched` | |
| `error_message` | `error_message` | |
| `created_at` | `created_at` | |
| `received_at` | `received_at` | |
| `cleaning_started_at` | `cleaning_started_at` | |
| `completed_at` | `completed_at` | |

---

## 7. 新增 URL 汇总

### dataapp 新增路由（`/api/acquisition/urls.py`）

```python
path("dashboard/nextcloud-sync/",   NextcloudSyncDashboardView.as_view(),   name="dashboard-nextcloud-sync"),
path("dashboard/tracking-batches/", TrackingBatchDashboardView.as_view(),   name="dashboard-tracking-batches"),
```

### dataapp 新增路由（`/api/aggregation/urls.py`）

```python
path("dashboard/email-tasks/", EmailTaskDashboardView.as_view(), name="dashboard-email-tasks"),
```

### webapp 新增路由（`urls.py`）

```python
path("api/dashboard/scraper-events/", ScraperEventDashboardView.as_view(), name="dashboard-scraper-events"),
```

---

## 8. 实施检查清单

### Phase 1：数据层准备（dataapp + webapp）

- [ ] dataapp — 确认 `SyncLog.details` 在写入时包含 `record_count`、`conflict_count`、`trigger`
- [ ] dataapp — `TrackingBatch` 新增 `source_type` 字段并 migrate（可选：先用 task_name 临时区分）
- [ ] dataapp — 创建 `EmailProcessingLog` 模型并 migrate
- [ ] dataapp — 在 email Celery 任务各阶段写入 `EmailProcessingLog`
- [ ] webapp — 无模型变更

### Phase 2：API 层（dataapp + webapp）

- [ ] dataapp — 实现 `NextcloudSyncDashboardView` + 序列化器 + URL
- [ ] dataapp — 实现 `TrackingBatchDashboardView` + 序列化器 + URL
- [ ] dataapp — 实现 `EmailTaskDashboardView` + 序列化器 + URL
- [ ] dataapp — 创建 Service Account Token（Django Admin 或 management command）
- [ ] webapp — 实现 `ScraperEventDashboardView` + 序列化器 + URL（含 source_name 合并逻辑）
- [ ] webapp — 创建 Service Account Token

### Phase 3：Dashboard 后端重构

- [ ] 新建 `backend/config.py`，读取环境变量
- [ ] 新建 `backend/builders.py`，实现 4 个 `_build_*_section()` 函数
- [ ] 重构 `backend/main.py`：删除 mock 数据，接入 `_refresh_sections()` 聚合逻辑
- [ ] 在 `docker-compose.yml` 中注入 `DATAAPP_API_URL`、`DATAAPP_SERVICE_TOKEN`、`WEBAPP_API_URL`、`WEBAPP_SERVICE_TOKEN`

### Phase 4：验证

- [ ] 用 `curl` 手动调用 4 个下游接口，确认响应格式正确
- [ ] 启动 Dashboard 后端，确认 `/api/tasks` 返回真实数据
- [ ] 前端 SSE 正常接收，甘特图/卡片视图正常渲染

---

*本文档反映 2026-03-03 时的系统状态，后续接口调整请同步更新。*
