# Tracking Number Empty Worker (Worker #4) 工作流程

本文档描述 Tracking Number Empty Worker 的完整数据处理链路，从数据库查询到 WebScraper 任务发布。

---

## 目录

1. [概述](#概述)
2. [Phase 1: 数据查询与任务发布](#phase-1-数据查询与任务发布)
3. [Phase 1.5: 任务发布控制](#phase-15-任务发布控制)
4. [Phase 2-3: WebScraper 抓取与数据落库](#phase-2-3-webscraper-抓取与数据落库)
5. [配置说明](#配置说明)
6. [手动触发](#手动触发)
7. [监控与故障排查](#监控与故障排查)

---

## 概述

### 业务场景

Tracking Number Empty Worker 是针对缺失追踪号的 Purchasing 记录的自动查询解决方案，特点是：
- 针对 `tracking_number` 为空的记录
- 针对 `order_number` 以 'w' 开头的 Apple 官网订单
- 使用 Apple Store 订单查询页面获取追踪信息
- 一次处理最多 20 条记录

### 与其他 Worker 的区别

| Worker | 目标 | 数据源 | 查询方式 |
|--------|------|--------|----------|
| **Worker #4 (本 Worker)** | 获取追踪号 | Purchasing (tracking_number 为空) | Apple Store URL |
| **Worker #8 (Japan Post)** | 更新配送状态 | Purchasing (tracking_number 已有) | Japan Post URL |

### 技术架构

```
┌─────────────────────────────────────────────────────────────────┐
│ Phase 1: Worker Query & Publish                                 │
│ ┌──────────────────────────────────────────────────────────┐   │
│ │ TrackingNumberEmptyWorker                                │   │
│ │ - Query Purchasing (20 records, tracking_number empty)   │   │
│ │ - Construct Apple Store URLs                             │   │
│ │ - Create TrackingBatch                                   │   │
│ │ - Dispatch to publish queue (20 tasks)                   │   │
│ └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ Phase 1.5: Publish Control                                      │
│ ┌──────────────────────────────────────────────────────────┐   │
│ │ publish_tracking_batch (Celery Task) × 20                │   │
│ │ - Call WebScraper API (sitemap: 1421177)                 │   │
│ │ - Create TrackingJob per URL                             │   │
│ │ - Rate limit: 6s sleep (150/15min)                       │   │
│ └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ Phase 2-3: WebScraper & Webhook (Same as other tracking tasks)  │
│ ┌──────────────────────────────────────────────────────────┐   │
│ │ - WebScraper scrapes Apple Store page                    │   │
│ │ - Extracts tracking number & delivery info               │   │
│ │ - Sends webhook on completion                            │   │
│ │ - Updates Purchasing.tracking_number                     │   │
│ └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Phase 1: 数据查询与任务发布

### 1.1 Worker 配置

**文件**: `apps/data_acquisition/workers/tracking_number_empty.py`

**Celery 配置**:
- **队列**: `tracking_number_empty`
- **Redis DB**: 5
- **容器**: `data-platform-celery-tracking-number-empty`
- **并发度**: 1
- **超时**: 120 秒

### 1.2 选取条件

```python
# 数据库查询条件
Purchasing.objects.filter(
    # 1. order_number 以 'w' 开头（不区分大小写）
    Q(order_number__istartswith='w'),

    # 2. 有关联的 official_account
    Q(official_account__isnull=False),

    # 3. official_account.email 不为空
    Q(official_account__email__isnull=False),
    ~Q(official_account__email=''),

    # 4. tracking_number 为空
    Q(tracking_number__isnull=True) | Q(tracking_number=''),
).exclude(
    # 5. 排除已完成状态
    latest_delivery_status__in=['配達完了', 'お届け先にお届け済み']
).select_related(
    'official_account'
)
```

**每次查询数量**: 最多 20 条记录（`MAX_RECORDS = 20`）

### 1.3 URL 构造

**Apple Store 订单查询 URL 格式**:
```
https://store.apple.com/go/jp/vieworder/{order_number}/{email}
```

**示例**:
```
https://store.apple.com/go/jp/vieworder/W123456789/user@example.com
```

**关键点**:
- `order_number`: Purchasing 的订单号
- `email`: OfficialAccount 的邮箱地址

### 1.4 TrackingBatch 创建

```python
batch = TrackingBatch.objects.create(
    file_path=f'purchasing_query_tracking_number_empty_{batch_short}',
    task_name='official_website_redirect_to_yamato_tracking',
    batch_uuid=uuid.uuid4(),
    total_jobs=len(records),  # 最多 20
    status='pending'
)
```

### 1.5 任务发布

```python
for idx, record in enumerate(records):
    url = f"https://store.apple.com/go/jp/vieworder/{order_number}/{email}"
    custom_id = f"owryt-{batch_short}-{idx:04d}"

    # 调用统一的发布任务
    publish_tracking_batch.apply_async(
        args=[
            'official_website_redirect_to_yamato_tracking',
            url,
            batch_uuid_str,
            custom_id,
            idx
        ],
        countdown=idx * 2  # 每个任务间隔 2 秒
    )
```

**发布策略**:
- 每个 URL 作为独立任务发布
- 使用 `countdown` 参数错开发布时间（每 2 秒一个）
- 总共最多 20 个任务

---

## Phase 1.5: 任务发布控制

### 1.5.1 发布任务配置

复用现有的 `publish_tracking_batch` 任务：

**文件**: `apps/data_acquisition/tasks.py`

**Celery 配置**:
- **队列**: `publish_tracking_queue`
- **超时**: 60 秒
- **重试**: 0 次

### 1.5.2 WebScraper 配置

使用 `official_website_redirect_to_yamato_tracking` 配置：

```python
TRACKING_TASK_CONFIGS = {
    'official_website_redirect_to_yamato_tracking': {
        'path_keyword': 'official_website_redirect_to_yamato_tracking',
        'filename_prefix': 'OWRYT-',
        'api_token': WEBSCRAPER_API_TOKEN,
        'sitemap_id': 1421177,
        'custom_id_prefix': 'owryt',
        'display_name': 'Official Website Redirect to Yamato Tracking',
    },
}
```

### 1.5.3 发布流程

```python
def publish_tracking_batch(task_name, url, batch_uuid_str, custom_id, index):
    # 1. 查找 TrackingBatch
    tracking_batch = TrackingBatch.objects.get(batch_uuid=batch_uuid_str)

    # 2. 断点续传检查
    if TrackingJob.objects.filter(batch=tracking_batch, custom_id=custom_id).exists():
        return {'status': 'skipped'}

    # 3. 调用 WebScraper API
    payload = {
        "sitemap_id": 1421177,
        "driver": "fulljs",
        "page_load_delay": 2000,
        "request_interval": 2000,
        "start_urls": [url],
        "custom_id": custom_id
    }

    response = requests.post(api_url, json=payload, timeout=30)

    # 4. 创建 TrackingJob
    if response.status_code in [200, 201, 202]:
        TrackingJob.objects.create(
            batch=tracking_batch,
            job_id=job_id,
            custom_id=custom_id,
            target_url=url,
            index=index,
            status='pending'
        )

    # 5. 强制睡眠 6 秒
    time.sleep(6)
```

---

## Phase 2-3: WebScraper 抓取与数据落库

此阶段与其他追踪任务共享相同的处理流程。

### 2.1 WebScraper 执行

**Sitemap ID**: `1421177`

WebScraper 会：
1. 访问 Apple Store 订单页面
2. 提取追踪号和配送信息
3. 完成后发送 webhook

### 2.2 Webhook 处理

**端点**: `POST /api/acquisition/webscraper/webscraper-tracking/`

**Source 识别**: 通过 `custom_id` 前缀 `owryt-` 识别

### 2.3 数据落库

Tracker 会更新 Purchasing 记录的以下字段：
- `tracking_number`: 追踪号
- `latest_delivery_status`: 最新配送状态
- `shipping_method`: 配送方式
- `estimated_delivery_date`: 预计送达日期

---

## 配置说明

### 4.1 环境变量

```python
# Redis DB 配置
REDIS_DB_TRACKING_NUMBER_EMPTY = 5

# WebScraper API
WEB_SCRAPER_API_TOKEN = "your-api-token"
```

### 4.2 Docker 配置

**docker-compose.yml**:
```yaml
celery_worker_tracking_number_empty:
  container_name: data-platform-celery-tracking-number-empty
  command: celery_worker_tracking_number_empty
  # ... 其他配置
```

**docker/entrypoint.sh**:
```bash
celery_worker_tracking_number_empty)
    exec celery -A apps.data_acquisition.workers.celery_tracking_number_empty worker \
        --loglevel=info \
        --concurrency=1 \
        --queues=tracking_number_empty \
        --hostname=tracking_number_empty@%h \
        --max-tasks-per-child=100 \
        --time-limit=120 \
        --soft-time-limit=110
    ;;
```

---

## 手动触发

### 5.1 Django Management Command

**命令**: `python manage.py run_tracking_number_empty`

**选项**:

| 选项 | 说明 | 示例 |
|------|------|------|
| `--count N` | 队列 N 个任务 | `--count 3` |
| `--sync` | 同步执行（不使用 Celery） | `--sync` |
| `--dry-run` | 只显示匹配记录，不执行 | `--dry-run` |

**使用示例**:

```bash
# 查看匹配的记录（不执行）
python manage.py run_tracking_number_empty --dry-run

# 同步执行一次（用于测试）
python manage.py run_tracking_number_empty --sync

# 队列 1 个异步任务
python manage.py run_tracking_number_empty

# 队列 3 个异步任务
python manage.py run_tracking_number_empty --count 3
```

### 5.2 直接调用任务

```python
# 异步调用
from apps.data_acquisition.workers.tasks_tracking_number_empty import process_record
result = process_record.delay()
print(f"Task ID: {result.id}")

# 同步调用（用于测试）
from apps.data_acquisition.workers.tracking_number_empty import TrackingNumberEmptyWorker
worker = TrackingNumberEmptyWorker()
result = worker.run()
print(result)
```

---

## 监控与故障排查

### 6.1 日志关键字

**Phase 1 - Worker 查询**:
```bash
# 查看 Worker 日志
docker logs data-platform-celery-tracking-number-empty 2>&1 | grep "\[tracking_number_empty_worker\]"

# 关键日志
[tracking_number_empty_worker] Found 20 matching records
[tracking_number_empty_worker] Created TrackingBatch abc12345 with 20 jobs
[tracking_number_empty_worker] Dispatched task 1/20: owryt-abc12345-0000 for order W123456
[tracking_number_empty_worker] Execution complete: dispatched 20 tasks
```

**Phase 1.5 - 任务发布**:
```bash
# 查看发布日志
docker logs data-platform-celery-tracking-phase1 2>&1 | grep "owryt-"

# 关键日志
[Task xxx] Publishing single URL: task=official_website_redirect_to_yamato_tracking, custom_id=owryt-abc12345-0000
[Task xxx] Successfully published: owryt-abc12345-0000 (job_id=123456)
```

### 6.2 数据库查询

**查看匹配的记录**:
```python
from apps.data_aggregation.models import Purchasing
from django.db.models import Q

# 查询符合条件的记录
candidates = Purchasing.objects.filter(
    Q(order_number__istartswith='w'),
    Q(official_account__isnull=False),
    Q(official_account__email__isnull=False),
    ~Q(official_account__email=''),
    Q(tracking_number__isnull=True) | Q(tracking_number=''),
).exclude(
    latest_delivery_status__in=['配達完了', 'お届け先にお届け済み']
)

print(f"Found {candidates.count()} matching records")

for p in candidates[:10]:
    print(f"  {p.order_number}: {p.official_account.email}")
```

**查看最近的批次**:
```python
from apps.data_acquisition.models import TrackingBatch, TrackingJob

# 最近的批次
latest_batch = TrackingBatch.objects.filter(
    file_path__startswith='purchasing_query_tracking_number_empty_'
).order_by('-created_at').first()

if latest_batch:
    print(f"Batch: {latest_batch.batch_uuid}")
    print(f"Status: {latest_batch.status}")
    print(f"Progress: {latest_batch.completed_jobs}/{latest_batch.total_jobs}")

    # 查看任务
    for job in latest_batch.jobs.all()[:5]:
        print(f"  {job.custom_id}: {job.status}")
```

### 6.3 SyncLog 记录

```python
from apps.data_acquisition.models import SyncLog

# 查看最近的同步日志
logs = SyncLog.objects.filter(
    operation_type__in=[
        'tracking_number_empty_triggered',
        'tracking_number_empty_completed'
    ]
).order_by('-timestamp')[:10]

for log in logs:
    print(f"{log.timestamp}: {log.operation_type}")
    print(f"  Success: {log.success}")
    print(f"  Message: {log.message}")
```

### 6.4 常见问题

#### 问题 1: Worker 未查询到记录

**可能原因**:
1. 没有符合条件的记录
2. 所有记录都已有 tracking_number
3. 所有记录都已完成配送

**排查**:
```bash
# 使用 dry-run 查看
python manage.py run_tracking_number_empty --dry-run
```

#### 问题 2: official_account 为空

**可能原因**:
- Purchasing 记录创建时未关联 OfficialAccount
- OfficialAccount 的 email 为空

**排查**:
```python
# 检查有 order_number 但无 official_account 的记录
Purchasing.objects.filter(
    order_number__istartswith='w',
    official_account__isnull=True
).count()
```

#### 问题 3: WebScraper 任务失败

**排查步骤**:
1. 检查 TrackingJob 状态
2. 查看 WebScraper 后台的任务详情
3. 验证 Apple Store URL 是否可访问

---

## 附录

### A. 相关文件清单

**Worker**:
- `apps/data_acquisition/workers/tracking_number_empty.py`
- `apps/data_acquisition/workers/celery_tracking_number_empty.py`
- `apps/data_acquisition/workers/tasks_tracking_number_empty.py`
- `apps/data_acquisition/management/commands/run_tracking_number_empty.py`

**配置**:
- `docker-compose.yml`
- `docker/entrypoint.sh`

**共享组件**:
- `apps/data_acquisition/tasks.py` (publish_tracking_batch)
- `apps/data_acquisition/views.py` (WebScraperTrackingViewSet)
- `apps/data_acquisition/models.py` (TrackingBatch, TrackingJob, SyncLog)

### B. 数据流图

```
Purchasing DB (tracking_number is empty)
    ↓ (query with filters)
TrackingNumberEmptyWorker
    ↓ (max 20 records)
For each record:
    ↓
    Construct Apple Store URL
    ↓ (https://store.apple.com/go/jp/vieworder/{order}/{email})
Create TrackingBatch (total_jobs=20)
    ↓
For each URL (with countdown):
    ↓
    publish_tracking_batch.apply_async
    ↓
publish_tracking_queue
    ↓ (process by phase1 worker)
Call WebScraper API (sitemap: 1421177)
    ↓
Create TrackingJob (status=pending)
    ↓ (sleep 6s)
WebScraper.io (scraping Apple Store page)
    ↓ (completed)
Send Webhook
    ↓
process_webscraper_tracking
    ↓
Update Purchasing.tracking_number
    ↓
TrackingJob.mark_completed()
    ↓
TrackingBatch.update_progress()
```

### C. 版本历史

- **2026-01-22**: 初始版本
  - 从 BasePlaywrightWorker 重构为独立 Worker 类
  - 新选取条件（基于 order_number 和 official_account）
  - 使用 Apple Store URL 构造
  - 复用 publish_tracking_batch 发布机制

---

## 参考文档

- [Japan Post Tracking 10 工作流程](./JAPAN_POST_TRACKING_10_WORKFLOW.md)
- [追踪任务流程 Part 1: Excel 处理与任务发布](./TRACKING_FLOW_PART1_PUBLISHING.md)
- [追踪任务流程 Part 2: Webhook 处理与数据落库](./TRACKING_FLOW_PART2_WEBHOOK.md)
- [Data Acquisition Workers](./DATA_ACQUISITION_WORKERS.md)
