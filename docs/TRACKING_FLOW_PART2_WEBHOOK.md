# 追踪任务流程文档 - Part 2: Webhook 处理与数据落库

本文档描述追踪任务流程的后半部分，从 WebScraper webhook 回调开始，到数据解析和数据库更新完成。

**相关文档**:
- [追踪任务流程 Part 1: Excel 处理与任务发布](./TRACKING_FLOW_PART1_PUBLISHING.md)
- [Worker 架构文档](./WORKER_ARCHITECTURE.md)

---

## 阶段四：Webhook 回调处理

### 4.1 Webhook 接收

**文件**: `apps/data_acquisition/views.py:661-730`

**类**: `WebScraperTrackingViewSet`

**端点**: `POST /api/acquisition/webscraper/webscraper-tracking/`

**权限**: `AllowAny`（通过 Token 验证）

### 4.2 Token 验证

**验证函数**: `_check_token(request, path_token=None)`

**Token 来源**:
1. Header: `X-Webhook-Token`
2. Query: `token` 或 `t`
3. Body: `token` 或 `t`

**验证逻辑**:
```python
WEBSCRAPER_WEBHOOK_TOKEN  # 专用 Token
# 或
BATCH_STATS_API_TOKEN      # 通用 Token
```

**失败响应**: `403 Forbidden`

### 4.3 参数解析

**请求参数**:
```json
{
  "scrapingjob_id": "string",  // WebScraper job ID
  "job_id": "string",           // 别名
  "source": "string",           // Tracker 名称（可选）
  "sitemap_name": "string",     // 用于映射 source（可选）
  "custom_id": "string"         // 用于映射 source（可选）
}
```

**查询参数**:
- `dry_run`: 是否试运行（默认 false）
- `dedupe`: 是否去重（默认 true）
- `upsert`: 是否 upsert 模式（默认 false）
- `batch_id`: 批次 UUID（可选）

### 4.4 Source 解析

**解析函数**: `_resolve_source(request)`

**解析优先级**:
1. 直接指定: `request.data.get("source")`
2. Sitemap 映射: `WEB_SCRAPER_SOURCE_MAP.get(sitemap_name)`
3. Custom ID 映射: 根据 `custom_id` 前缀匹配

**示例映射**:
```python
WEB_SCRAPER_SOURCE_MAP = {
    "official-website-sitemap": "official_website_redirect_to_yamato_tracking",
    "japan-post-sitemap": "redirect_to_japan_post_tracking",
}
```

### 4.5 Tracker 验证

```python
from .trackers.registry_tracker import get_tracker
tracker = get_tracker(source_name)  # 抛出 KeyError 如果不存在
```

**失败响应**: `400 Bad Request - "未知任务: {source_name}"`

### 4.6 任务调度

```python
task = process_webscraper_tracking.delay(
    source_name=source_name,
    job_id=job_id,
    batch_uuid=str(batch_uuid),
    request_data=request.data,
    dry_run=dry_run,
    dedupe=dedupe,
    upsert=upsert
)
```

**成功响应**: `202 Accepted`
```json
{
  "mode": "webhook",
  "accepted": true,
  "task_id": "celery-task-uuid",
  "job_id": "webscraper-job-id",
  "source": "official_website_redirect_to_yamato_tracking",
  "dry_run": false,
  "dedupe": true,
  "upsert": false,
  "batch_id": "batch-uuid"
}
```

---

## 阶段五：数据解析与数据库更新

### 5.1 异步任务处理

**文件**: `apps/data_acquisition/tasks.py:341-429`

**任务**: `process_webscraper_tracking`

**Worker**: `celery_worker_tracking_phase2`（tracking_webhook_queue）

**配置**:
- `bind=True`: 绑定 self
- `max_retries=3`: 最多重试 3 次
- `default_retry_delay=60`: 重试间隔 60 秒
- `time_limit=300`: 5 分钟超时
- `concurrency=2`: 2 个并发

### 5.2 幂等性检查

**dedupe 模式**（默认启用）:
```python
if dedupe:
    existing = SyncLog.objects.filter(
        operation_type='webscraper_tracking',
        details__job_id=job_id
    ).exists()

    if existing:
        return {'status': 'already_processed', 'job_id': job_id}
```

**作用**: 防止重复处理相同的 job_id

### 5.3 CSV 数据获取

**函数**: `fetch_webscraper_export_sync(job_id, format="csv")`

**文件**: `apps/data_aggregation/utils.py:277-288`

**实现**:
```python
import httpx
from django.conf import settings

url = settings.WEB_SCRAPER_EXPORT_URL_TEMPLATE.format(job_id=job_id)
headers = {"Authorization": f"Bearer {settings.WEB_SCRAPER_API_TOKEN}"}

with httpx.Client(timeout=60.0) as client:
    response = client.get(url, headers=headers, follow_redirects=True)
    response.raise_for_status()
    return response.content
```

**URL 示例**:
```
https://api.webscraper.io/api/v1/scraping-job/12345/export?format=csv
```

### 5.4 CSV 解析

**解析代码**:
```python
import pandas as pd
import io

try:
    df = pd.read_csv(io.BytesIO(content), encoding="utf-8-sig")
except pd.errors.ParserError as e:
    return {
        'status': 'error',
        'error_type': 'parse_error',
        'message': f'Failed to parse CSV: {e}'
    }

if df.empty:
    return {
        'status': 'error',
        'error_type': 'empty_data',
        'message': 'DataFrame is empty'
    }
```

**错误类型**:
- `parse_error`: CSV 格式错误（不重试）
- `empty_data`: CSV 为空（不重试）

### 5.4.1 智能重定向检测（新增）

**适用场景**：当 `official_website_redirect_to_yamato_tracking` 任务返回的数据只有1行时，说明该订单实际使用的是日本邮政配送，需要重定向到 `redirect_to_japan_post_tracking` 进行处理。

**检测条件**：
```python
if (source_name == 'official_website_redirect_to_yamato_tracking'
    and len(df) == 1  # 除表头外只有1行数据
    and tracking_job  # TrackingJob 存在
    and tracking_job.status != 'redirected'):  # 未被重定向过
```

**重定向流程**：

#### 步骤 1: 提取URL
```python
target_url = None
if 'web_start_url' in df.columns and len(df) > 0:
    target_url = df.iloc[0]['web_start_url']
```

#### 步骤 2: 标记原任务
```python
tracking_job.mark_redirected()  # 设置状态为 'redirected'
logger.info(f"Marked TrackingJob {tracking_job.custom_id} as redirected")
```

#### 步骤 3: 记录 SyncLog
```python
SyncLog.objects.create(
    operation_type='official_website_redirect_to_yamato_tracking_completed',
    celery_task_id=task_id,
    message=f"Redirected to redirect_to_japan_post_tracking: {target_url}",
    success=True,
    details={
        'original_custom_id': tracking_job.custom_id,
        'redirected_url': target_url,
        'reason': 'single_row_result'
    }
)
```

#### 步骤 4: 创建新的追踪任务
```python
# 获取 redirect_to_japan_post_tracking 配置
jpt_config = TRACKING_TASK_CONFIGS['redirect_to_japan_post_tracking']
API_TOKEN = jpt_config['api_token']
SITEMAP_ID = jpt_config['sitemap_id']

# 构建新的 custom_id（格式：jpt-from-owryt-{original_custom_id}）
new_custom_id = f"jpt-from-owryt-{tracking_job.custom_id}"

# 调用 WebScraper API
payload = {
    "sitemap_id": SITEMAP_ID,
    "driver": "fulljs",
    "page_load_delay": 2000,
    "request_interval": 2000,
    "start_urls": [target_url],
    "custom_id": new_custom_id
}

api_url = f"https://api.webscraper.io/api/v1/scraping-job?api_token={API_TOKEN}"
api_response = requests.post(api_url, json=payload, timeout=30)
```

#### 步骤 5: 创建新的 TrackingJob
```python
if api_response.status_code in [200, 201, 202]:
    response_data = api_response.json()
    new_job_id = response_data.get('id') or response_data.get('job_id') or None

    # 创建新的 TrackingJob，关联到同一个 TrackingBatch
    new_tracking_job = TrackingJob.objects.create(
        batch=tracking_job.batch,  # 关联到原批次
        job_id=new_job_id,
        custom_id=new_custom_id,
        target_url=target_url,
        index=tracking_job.index,
        status='pending'
    )
```

#### 步骤 6: 记录成功日志
```python
SyncLog.objects.create(
    operation_type='redirect_to_japan_post_tracking_triggered',
    celery_task_id=task_id,
    message=f"Japan Post tracking triggered for redirected job: {new_custom_id}",
    success=True,
    details={
        'original_custom_id': tracking_job.custom_id,
        'new_custom_id': new_custom_id,
        'new_job_id': new_job_id,
        'target_url': target_url
    }
)
```

**重定向完成度计算**：
- 原 `official_website_redirect_to_yamato_tracking` 任务标记为 `redirected`，不计入完成数
- 只有对应的 `redirect_to_japan_post_tracking` 任务完成后，才算真正完成
- TrackingBatch 的完成度 = (直接完成数 + redirected中对应japan_post已完成数) / 总任务数

**错误处理**：
- 如果 API 调用失败，原任务仍保持 `redirected` 状态
- 记录详细的错误日志到 SyncLog
- 返回 `redirected_failed` 状态供监控

**防重复机制**：
- 检查 `tracking_job.status != 'redirected'`，避免重复投递
- 一个 URL 最多只创建一个 redirect_to_japan_post_tracking 任务

### 5.5 Tracker 执行

**注册表**: `apps/data_acquisition/trackers/registry_tracker.py`

**注册的 Trackers**:
```python
TRACKERS = {
    "official_website_redirect_to_yamato_tracking": official_website_redirect_to_yamato_tracking,
    "redirect_to_japan_post_tracking": redirect_to_japan_post_tracking,
    "official_website_tracking": official_website_tracking,
    "yamato_tracking_only": yamato_tracking_only,
    "japan_post_tracking_only": japan_post_tracking_only,
    "japan_post_tracking_10": japan_post_tracking_10,
}
```

**调用**:
```python
from .trackers.registry_tracker import run_tracker
result = run_tracker(source_name, df)
```

### 5.6 Tracker 实现详解

**文件**: `apps/data_acquisition/trackers/official_website_redirect_to_yamato_tracking.py`

**函数**: `official_website_redirect_to_yamato_tracking(df: pd.DataFrame) -> bool`

**事务保护**:
```python
from django.db import transaction

@transaction.atomic
def official_website_redirect_to_yamato_tracking(df):
    # ... 所有数据库操作都在事务中
    # 任何异常都会触发回滚
```

**处理流程**:

#### 5.6.1 读取数据
```python
# 读取 DataFrame 最后一行
last_row = df.iloc[-1]

# 提取字段
order_number = last_row.get('order_number', '').strip()
email = last_row.get('email', '').strip()
tracking_number = last_row.get('tracking_number', '').strip()
delivery_date = last_row.get('delivery_date', '').strip()
delivery_status = last_row.get('delivery_status', '').strip()
confirmed_at = last_row.get('confirmed_at', None)
last_updated_at = last_row.get('last_updated_at', None)
```

#### 5.6.2 查询 Purchasing
```python
from apps.resale.models import Purchasing

purchasing = Purchasing.objects.filter(order_number=order_number).first()
```

**情况一**: Purchasing 存在
- 检查是否有 `official_account`
- 检查 `email` 是否匹配
- 如果不匹配，记录警告日志

**情况二**: Purchasing 不存在
- 创建 `OfficialAccount`
- 创建 `Purchasing`（包含关联的 `Inventory`）

#### 5.6.3 OfficialAccount 处理

**并发安全的创建**:
```python
from apps.resale.models import OfficialAccount

account, created = OfficialAccount.objects.get_or_create(
    email=email,
    defaults={
        'account_name': email.split('@')[0],
        'status': 'active'
    }
)

if created:
    logger.info(f"Created OfficialAccount: {email}")
```

**关联到 Purchasing**:
```python
if not purchasing.official_account:
    purchasing.official_account = account
    logger.info(f"Associated OfficialAccount {email} to Purchasing {order_number}")
```

#### 5.6.4 更新字段

```python
from django.utils import timezone
from datetime import datetime

# 更新订单号
purchasing.order_number = order_number

# 更新快递单号
if tracking_number:
    purchasing.tracking_number = tracking_number

# 更新预计送达日期
if delivery_date:
    try:
        purchasing.estimated_delivery_date = datetime.strptime(
            delivery_date, '%Y-%m-%d'
        ).date()
    except ValueError:
        logger.warning(f"Invalid delivery_date format: {delivery_date}")

# 更新配送状态（限制长度）
if delivery_status:
    purchasing.latest_delivery_status = delivery_status[:10]

# 更新订单确认时间
if confirmed_at:
    try:
        purchasing.confirmed_at = datetime.fromisoformat(confirmed_at)
    except ValueError:
        pass

# 更新最后信息更新时间
purchasing.last_info_updated_at = timezone.now()
```

#### 5.6.5 保存并提交

```python
purchasing.save()
logger.info(
    f"Updated and saved Purchasing {order_number}: "
    f"tracking={tracking_number}"
)

return True  # 返回 True 表示成功
```

**失败处理**:
```python
except Exception as e:
    logger.exception(f"Failed to process tracking data: {e}")
    return False  # 返回 False 表示失败
```

### 5.7 结果验证

```python
if result is False:
    return {
        'status': 'error',
        'error_type': 'tracker_failed',
        'message': 'Tracker returned False indicating failure'
    }

if isinstance(result, dict) and result.get('status') == 'error':
    return {
        'status': 'error',
        'error_type': 'tracker_error',
        'message': result.get('message', 'Unknown error')
    }
```

### 5.8 成功日志

```python
SyncLog.objects.create(
    operation_type='webscraper_tracking',
    celery_task_id=task_id,
    message=f"Tracking completed for job {job_id}",
    success=True,
    details={
        'job_id': job_id,
        'source': source_name,
        'batch_uuid': batch_uuid,
        'result': result
    }
)

return {
    'status': 'success',
    'task_id': task_id,
    'source': source_name,
    'job_id': job_id,
    'batch_uuid': str(batch_uuid),
    'result': result
}
```

---

## 配置说明

### 1. Django Settings

```python
# WebScraper API 配置（阶段五使用）
WEB_SCRAPER_API_TOKEN = "YOUR_WEBSCRAPER_API_TOKEN"
WEB_SCRAPER_EXPORT_URL_TEMPLATE = "https://api.webscraper.io/api/v1/scraping-job/{job_id}/export?format=csv"

# Webhook Token 配置
WEBSCRAPER_WEBHOOK_TOKEN = "your-webhook-token"
# 或使用通用的 token
BATCH_STATS_API_TOKEN = "your-batch-stats-token"

# Source 映射配置（可选）
WEB_SCRAPER_SOURCE_MAP = {
    "official-website-sitemap": "official_website_redirect_to_yamato_tracking",
    "japan-post-sitemap": "redirect_to_japan_post_tracking",
    "official-website-tracking-sitemap": "official_website_tracking",
    "yamato-sitemap": "yamato_tracking_only",
    "japan-post-only-sitemap": "japan_post_tracking_only",
}
```

### 2. WebScraper 配置

**Sitemap 设置**:
1. 创建 Sitemap，配置目标网站的数据提取规则
2. 获取 `sitemap_id`
3. 配置 Webhook URL: `https://your-domain.com/api/acquisition/webscraper/webscraper-tracking/?token=YOUR_TOKEN`

**Webhook 触发条件**: 爬虫任务完成时自动触发

### 3. Celery Worker

确保 Phase 2 Worker 正在运行:
```bash
# Docker Compose 方式（推荐）
docker-compose up -d celery_worker_tracking_phase2

# 或直接启动
celery -A apps.data_acquisition.celery worker \
    --loglevel=info \
    --concurrency=2 \
    --queues=tracking_webhook_queue \
    --hostname=tracking_phase2@%h \
    --time-limit=300 \
    --soft-time-limit=290
```

---

## 监控与日志

### SyncLog 记录类型

| operation_type | 阶段 | 说明 |
|---------------|------|------|
| `webscraper_tracking` | 阶段五 | 数据库更新完成 |
| `redirect_to_japan_post_tracking_triggered` | 阶段五 | 智能重定向：创建新任务 |

### 追踪批次（TrackingBatch）

系统通过 `TrackingBatch` 和 `TrackingJob` 模型追踪每个 Excel 文件中所有 URL 的爬取完成状态。

**模型关系**：
- `TrackingBatch`: 代表一个Excel文件的批次处理
- `TrackingJob`: 代表批次中的单个 URL 爬取任务

**使用示例**：

```python
from apps.data_acquisition.batch_tracker import (
    get_batch_by_uuid,
    get_batch_by_file_path,
    list_batches,
    get_pending_batches,
    get_batch_summary,
    print_batch_status,
)

# 1. 通过批次 UUID 查询（支持短格式）
batch = get_batch_by_uuid('a1b2c3d4')  # 前8位
if batch:
    print(f"完成度: {batch.completion_percentage}%")
    print(f"已完成: {batch.completed_jobs}/{batch.total_jobs}")
    print(f"状态: {batch.get_status_display()}")

# 2. 通过文件路径查询
batch = get_batch_by_file_path('/official_website_redirect_to_yamato_tracking/OWRYT-20260108-001.xlsx')

# 3. 查看详细统计
summary = get_batch_summary(batch)
print(f"总任务数: {summary['total_jobs']}")
print(f"已完成: {summary['completed_jobs']}")
print(f"失败: {summary['failed_jobs']}")
print(f"待处理: {summary['pending_jobs']}")
print(f"失败任务详情: {summary['failed_job_errors']}")

# 4. 打印批次状态（包含所有任务详情）
print_batch_status(batch, show_jobs=True)

# 5. 列出所有批次
batches = list_batches(task_name='official_website_redirect_to_yamato_tracking', days=7)
for b in batches:
    print(f"{b.file_path}: {b.completion_percentage}%")

# 6. 查询未完成的批次
pending = get_pending_batches()
for b in pending:
    print(f"未完成: {b.file_path} - {b.pending_jobs} jobs 待处理")

# 7. 直接使用模型查询
from apps.data_acquisition.models import TrackingBatch, TrackingJob

# 查询特定批次的所有任务
batch = TrackingBatch.objects.get(batch_uuid='your-uuid-here')
jobs = batch.jobs.all()

# 查询失败的任务
failed_jobs = batch.jobs.filter(status='failed')
for job in failed_jobs:
    print(f"失败: {job.custom_id} - {job.error_message}")

# 查询待处理的任务
pending_jobs = batch.jobs.filter(status='pending')
print(f"还有 {pending_jobs.count()} 个任务待处理")
```

**批次状态说明**：

| 状态 | 说明 |
|-----|------|
| `pending` | 刚创建，爬虫任务正在创建中 |
| `processing` | 至少有一个 job 已完成 |
| `completed` | 所有 job 都已完成（全部成功） |
| `partial` | 所有 job 都已完成，但有失败的 |

**任务状态说明（TrackingJob）**：

| 状态 | 说明 |
|-----|------|
| `pending` | 等待 WebScraper 完成 |
| `completed` | 已完成并成功处理 |
| `failed` | 处理失败 |
| `redirected` | 已重定向到其他追踪任务（不计入完成数） |

**重定向任务的完成度计算**：

当一个任务被标记为 `redirected` 时，系统会自动创建新的 redirect_to_japan_post_tracking 任务。完成度计算逻辑会特殊处理这种情况：

```python
# 计算有效完成数
direct_completed = batch.jobs.filter(status='completed').count()

# 查找 redirected 任务中对应的 japan_post 任务已完成的数量
redirected_completed = 0
for redirected_job in batch.jobs.filter(status='redirected'):
    jpt_custom_id = f"jpt-from-owryt-{redirected_job.custom_id}"
    if batch.jobs.filter(custom_id=jpt_custom_id, status='completed').exists():
        redirected_completed += 1

# 有效完成数 = 直接完成 + redirected中对应japan_post已完成
effective_completed = direct_completed + redirected_completed
```

**示例场景**：
- 批次总共 100 个任务
- 其中 30 个被重定向到 redirect_to_japan_post_tracking
- 20 个 japan_post 任务已完成
- 其他 70 个直接完成
- **完成度 = (70 + 20) / 100 = 90%**

**实时监控**：

```python
# 监控特定批次的完成进度
import time
from apps.data_acquisition.batch_tracker import get_batch_by_uuid, get_batch_summary

batch = get_batch_by_uuid('a1b2c3d4')

while not batch.is_completed:
    summary = get_batch_summary(batch)
    print(f"\r进度: {summary['completion_percentage']}% "
          f"({summary['completed_jobs']}/{summary['total_jobs']})", end='')
    time.sleep(5)
    batch.refresh_from_db()

print(f"\n批次已完成！耗时: {summary['duration_seconds']}秒")
```

### SyncLog 查询示例

**查看完整流程的日志**:
```python
from apps.data_acquisition.models import SyncLog
from django.utils import timezone
from datetime import timedelta

# 查看最近 1 小时的所有相关日志
recent = timezone.now() - timedelta(hours=1)

logs = SyncLog.objects.filter(
    operation_type__in=[
        'webscraper_tracking',
        'redirect_to_japan_post_tracking_triggered'
    ],
    created_at__gte=recent
).order_by('created_at')

for log in logs:
    print(f"[{log.created_at}] {log.operation_type}: {log.message}")
```

**查看特定 job_id 的处理结果**:
```python
job_id = "12345"

logs = SyncLog.objects.filter(
    operation_type='webscraper_tracking',
    details__job_id=job_id
)
```

### 日志级别

- **INFO**: 正常流程（任务开始、完成、已处理跳过）
- **WARNING**: 数据问题（空 DataFrame、Email 不匹配）
- **ERROR**: 处理失败（CSV 解析错误、Tracker 失败）
- **EXCEPTION**: 未预期的异常（包含完整堆栈）

### 关键日志示例

```
# 阶段四
[WebScraperTrackingViewSet] Found tracker for source: official_website_redirect_to_yamato_tracking

# 阶段五
[Task def-456] Processing webscraper tracking: source=official_website_redirect_to_yamato_tracking, job_id=78910
[Task def-456] Found existing Purchasing: ORD-20260108-001
[Task def-456] Created OfficialAccount: user@example.com
[Task def-456] Updated and saved Purchasing ORD-20260108-001: tracking=1234567890
[Task def-456] Tracking completed successfully
```

---

## 错误处理

### 阶段四错误

| HTTP 状态码 | 错误场景 | 响应体 |
|-----------|---------|--------|
| 403 | Token 验证失败 | `{"detail": "Webhook token 不匹配"}` |
| 400 | 缺少必需参数 | `{"detail": "Webhook 需要 job_id 与 source"}` |
| 400 | Tracker 不存在 | `{"detail": "未知任务: {source_name}"}` |
| 500 | 其他异常 | `{"detail": "调度任务时出错: {error}"}` |

### 阶段五错误

| 错误类型 | 是否重试 | 说明 |
|---------|---------|------|
| `already_processed` | ❌ 否 | Job 已处理过（幂等性） |
| `empty_data` | ❌ 否 | CSV 为空 |
| `parse_error` | ❌ 否 | CSV 格式错误 |
| `dataframe_error` | ❌ 否 | DataFrame 创建失败 |
| `tracker_failed` | ❌ 否 | Tracker 返回 False |
| `tracker_error` | ❌ 否 | Tracker 返回错误字典 |
| `unknown_tracker` | ❌ 否 | Tracker 不存在 |
| `processing_error` | ✅ 是 | 其他异常（如网络错误），重试最多 3 次 |

### 数据库事务

所有数据库操作都在 `@transaction.atomic` 装饰器保护下：
- 任何异常都会触发事务回滚
- 保证数据一致性
- 不会出现部分更新的情况

---

## 故障排查

### 问题 1: Webhook 返回 403 Forbidden

**可能原因**: Token 验证失败

**解决方案**:
1. 检查 WebScraper Webhook 配置中的 Token
2. 检查 Django settings 中的 `WEBSCRAPER_WEBHOOK_TOKEN`
3. 或检查 `BATCH_STATS_API_TOKEN`

**测试命令**:
```bash
curl -X POST "https://your-domain.com/api/acquisition/webscraper/webscraper-tracking/" \
  -H "Content-Type: application/json" \
  -H "X-Webhook-Token: your-webhook-token" \
  -d '{
    "scrapingjob_id": "12345",
    "source": "official_website_redirect_to_yamato_tracking"
  }'
```

### 问题 2: Webhook 返回 400 "未知任务"

**可能原因**: Source 未注册或映射失败

**解决方案**:
1. 检查 `source` 参数是否正确
2. 检查 `WEB_SCRAPER_SOURCE_MAP` 配置
3. 检查 `apps/data_acquisition/trackers/registry_tracker.py` 中的 `TRACKERS` 注册表

### 问题 3: CSV 解析失败 (parse_error)

**可能原因**: WebScraper CSV 格式错误或编码问题

**解决方案**:
1. 检查 WebScraper job 是否成功完成
2. 手动下载 CSV 检查:
```bash
curl "https://api.webscraper.io/api/v1/scraping-job/{job_id}/export?format=csv" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -o output.csv
```
3. 检查编码是否为 UTF-8
4. 检查 CSV 是否包含必需的列

### 问题 4: Tracker 返回 False

**可能原因**: 业务逻辑验证失败或数据不完整

**解决方案**:
1. 检查日志中的 ERROR 或 EXCEPTION 信息
2. 检查 CSV 数据中是否包含必需字段（如 `order_number`）
3. 检查数据库中是否存在冲突数据
4. 手动运行 tracker 进行调试:
```python
import pandas as pd
from apps.data_acquisition.trackers.official_website_redirect_to_yamato_tracking import official_website_redirect_to_yamato_tracking

# 加载测试数据
df = pd.read_csv('test_data.csv')

# 运行 tracker
result = official_website_redirect_to_yamato_tracking(df)
print(result)
```

### 问题 5: Email 不匹配警告

**现象**: 日志显示 "Email mismatch for Purchasing..."

**原因**: Purchasing 已关联的 OfficialAccount 的 email 与爬取到的 email 不一致

**影响**: 不影响数据更新，只是记录警告

**处理**:
- 如果是正常情况（订单转移等），可以忽略
- 如果是数据错误，需要手动检查并修正

### 问题 6: Celery Worker 未运行

**现象**: 任务一直处于 PENDING 状态

**解决方案**:
```bash
# 检查 worker 状态
celery -A apps.data_acquisition.celery inspect active

# 启动 Phase 2 Worker
docker-compose up -d celery_worker_tracking_phase2

# 或直接启动
celery -A apps.data_acquisition.celery worker \
    --loglevel=info \
    --concurrency=2 \
    --queues=tracking_webhook_queue \
    --hostname=tracking_phase2@%h
```

---

## 数据库模型关系

```
OfficialAccount (官方账号)
    ├── email (唯一)
    ├── account_name
    └── status

Purchasing (采购订单)
    ├── order_number (订单号)
    ├── official_account (外键 -> OfficialAccount)
    ├── tracking_number (快递单号)
    ├── estimated_delivery_date (预计送达日期)
    ├── latest_delivery_status (最新配送状态)
    ├── last_info_updated_at (最后信息更新时间)
    ├── confirmed_at (订单确认时间)
    └── inventory (一对一 -> Inventory)

SyncLog (同步日志)
    ├── operation_type
    ├── celery_task_id
    ├── file_path
    ├── message
    ├── success
    ├── details (JSONField)
    └── created_at

TrackingBatch (追踪批次)
    ├── batch_uuid (批次唯一标识)
    ├── file_path (Excel 文件路径)
    ├── task_name (任务名称)
    ├── total_jobs (总任务数)
    ├── completed_jobs (已完成数)
    ├── failed_jobs (失败数)
    ├── status (批次状态)
    ├── created_at
    └── updated_at

TrackingJob (追踪任务)
    ├── batch (外键 -> TrackingBatch)
    ├── job_id (WebScraper Job ID)
    ├── custom_id (自定义 ID)
    ├── target_url (目标 URL)
    ├── index (序号)
    ├── status (任务状态: pending/completed/failed/redirected)
    ├── error_message (错误信息)
    ├── created_at
    └── updated_at
```

---

## 性能优化建议

### 1. 阶段五优化

**批量处理**: 如果 CSV 包含多行数据，可以批量更新
```python
# 使用 bulk_update 代替逐个 save
from django.db.models import F

purchasings_to_update = []
for index, row in df.iterrows():
    # ... 处理逻辑
    purchasings_to_update.append(purchasing)

Purchasing.objects.bulk_update(
    purchasings_to_update,
    ['tracking_number', 'estimated_delivery_date', 'latest_delivery_status']
)
```

### 2. 数据库索引

确保以下字段有索引:
```python
class Purchasing(models.Model):
    order_number = models.CharField(max_length=100, db_index=True)  # 索引
    tracking_number = models.CharField(max_length=100, db_index=True)  # 索引
    official_account = models.ForeignKey(OfficialAccount, db_index=True)  # 外键自动有索引
```

---

## 相关文档

- [追踪任务流程 Part 1: Excel 处理与任务发布](./TRACKING_FLOW_PART1_PUBLISHING.md)
- [Worker 架构文档](./WORKER_ARCHITECTURE.md)
- [Data Acquisition Workers](./DATA_ACQUISITION_WORKERS.md) - Celery Worker 配置

---

**最后更新**: 2026-01-16
**维护者**: Data Acquisition Team
**流程版本**: v3.3
