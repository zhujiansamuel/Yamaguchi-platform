# Japan Post Tracking 10 完整工作流程

本文档详细描述 Japan Post Tracking 10 (合10追踪) 的完整数据处理链路，从数据库查询到最终数据落库。

---

## 目录

1. [概述](#概述)
2. [Phase 1: 数据查询与任务发布](#phase-1-数据查询与任务发布)
3. [Phase 1.5: 任务发布控制](#phase-15-任务发布控制)
4. [Phase 2: WebScraper 抓取](#phase-2-webscraper-抓取)
5. [Phase 3: Webhook 处理与数据落库](#phase-3-webhook-处理与数据落库)
6. [配置说明](#配置说明)
7. [监控与故障排查](#监控与故障排查)

---

## 概述

### 业务场景

Japan Post Tracking 10 是针对日本邮政物流的批量追踪解决方案，特点是：
- 一次可查询 10 个追踪号（合并查询，提高效率）
- 针对 JP LOGISTICS GROUP CO., LTD. 承运的订单
- 自动过滤已完成/已送达的订单
- 智能控制查询频率（默认 6 小时间隔）

### 技术架构

```
┌─────────────────────────────────────────────────────────────────┐
│ Phase 1: Worker Query & Publish                                │
│ ┌──────────────────────────────────────────────────────────┐   │
│ │ JapanPostTracking10TrackingNumberWorker                  │   │
│ │ - Query Purchasing (10 records)                          │   │
│ │ - Construct URL (10 tracking numbers)                    │   │
│ │ - Create TrackingBatch                                   │   │
│ │ - Dispatch to publish queue                              │   │
│ └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ Phase 1.5: Publish Control                                     │
│ ┌──────────────────────────────────────────────────────────┐   │
│ │ publish_tracking_batch (Celery Task)                     │   │
│ │ - Call WebScraper API                                    │   │
│ │ - Create TrackingJob                                     │   │
│ │ - Rate limit: 6s sleep (150/15min)                       │   │
│ └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ Phase 2: WebScraper Execution                                  │
│ ┌──────────────────────────────────────────────────────────┐   │
│ │ WebScraper.io                                            │   │
│ │ - Scrape Japan Post website                              │   │
│ │ - Extract tracking data                                  │   │
│ │ - Send webhook on completion                             │   │
│ └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ Phase 3: Webhook Processing & Database Update                  │
│ ┌──────────────────────────────────────────────────────────┐   │
│ │ process_webscraper_tracking (Celery Task)                │   │
│ │ - Download CSV from WebScraper                           │   │
│ │ - Call japan_post_tracking_10(df) tracker               │   │
│ │   - Parse Japanese datetime                              │   │
│ │   - Match Purchasing records                             │   │
│ │   - Update database fields                               │   │
│ │ - Mark TrackingJob as completed/failed                   │   │
│ └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Phase 1: 数据查询与任务发布

### 1.1 Worker 配置

**文件**: `apps/data_acquisition/workers/japan_post_tracking_10_tracking_number.py`

**Celery 配置**:
- **队列**: `japan_post_tracking_10_tracking_number_queue`
- **Redis DB**: 6
- **容器**: `data-platform-celery-japan-post-tracking-10-tracking-number`
- **并发度**: 1
- **超时**: 120 秒

**触发方式**:
```bash
# 手动触发
python manage.py run_japan_post_tracking_10_tracking_number

# 或通过 Celery Beat 定时任务
```

### 1.2 选取条件

```python
# 数据库查询条件
Purchasing.objects.filter(
    # 1. order_number 以 'w' 开头（不区分大小写）
    Q(order_number__istartswith='w'),

    # 2. 排除已完成状态
    ~Q(latest_delivery_status__in=['配達完了', 'お届け先にお届け済み']),

    # 3. 时间条件（满足任一即可）:
    #    - 从未查询过 (delivery_status_query_time IS NULL)
    #    - 超过查询间隔 (< now - 6 hours)
    #    - 快递单未登录 (latest_delivery_status = "伝票番号未登録")
    Q(delivery_status_query_time__isnull=True) |
    Q(delivery_status_query_time__lt=timezone.now() - timedelta(hours=6)) |
    Q(latest_delivery_status='伝票番号未登録'),

    # 4. 承运商过滤
    Q(shipping_method='JP LOGISTICS GROUP CO., LTD.')
).exclude(
    # 5. 排除空追踪号
    tracking_number__isnull=True
).exclude(
    tracking_number=''
)

# 额外过滤：tracking_number 提取出的数字长度必须 = 12
# 例如: "1837-9316-7924" -> "183793167924" (12位)
```

**每次查询数量**: 最多 10 条记录（`MAX_RECORDS = 10`）

### 1.3 URL 构造

**Japan Post 追踪 URL 格式**:
```
https://trackings.post.japanpost.jp/services/srv/search?
  requestNo1=183792779166
  &requestNo2=183792777895
  &requestNo3=183792778142
  ...
  &requestNo10=183792779240
  &search.x=13
  &search.y=4
  &startingUrlPatten=
  &locale=ja
```

**特点**:
- 一次最多 10 个追踪号
- 使用随机 x/y 坐标（反爬虫）
- 空位补空字符串

### 1.4 TrackingBatch 创建

```python
batch = TrackingBatch.objects.create(
    file_path=f'purchasing_query_{batch_short}',  # 虚拟路径
    task_name='japan_post_tracking_10',
    batch_uuid=uuid.uuid4(),
    total_jobs=1,  # 只有 1 个 URL
    status='pending'
)
```

### 1.5 任务发布

```python
# 调用统一的发布任务
publish_tracking_batch.apply_async(
    args=[
        'japan_post_tracking_10',  # task_name
        url,                        # 构造的 URL
        batch_uuid_str,            # TrackingBatch UUID
        custom_id,                 # jpt10-{batch_short}-purchasing
        0                          # index
    ],
    countdown=0  # 立即执行
)
```

### 1.6 防重复查询

Worker 会立即更新所有查询记录的 `delivery_status_query_time`：
```python
Purchasing.objects.filter(
    uuid__in=record_uuids
).update(
    delivery_status_query_time=timezone.now()
)
```

**目的**: 防止在 WebScraper 返回结果前，Worker 重复查询相同记录。

---

## Phase 1.5: 任务发布控制

### 1.5.1 发布任务配置

**文件**: `apps/data_acquisition/tasks.py:945-1085`

**Celery 配置**:
- **队列**: `publish_tracking_queue`
- **容器**: `data-platform-celery-tracking-phase1`
- **并发度**: 取决于配置
- **超时**: 60 秒
- **重试**: 0 次（失败即抛弃）

### 1.5.2 发布流程

```python
def publish_tracking_batch(task_name, url, batch_uuid_str, custom_id, index):
    try:
        # 1. 查找 TrackingBatch
        tracking_batch = TrackingBatch.objects.get(batch_uuid=batch_uuid_str)

        # 2. 断点续传检查
        if TrackingJob.objects.filter(batch=tracking_batch, custom_id=custom_id).exists():
            return {'status': 'skipped'}  # 已发布，跳过

        # 3. 调用 WebScraper API
        config = TRACKING_TASK_CONFIGS['japan_post_tracking_10']
        payload = {
            "sitemap_id": config['sitemap_id'],  # 1424233
            "driver": "fulljs",
            "page_load_delay": 2000,
            "request_interval": 2000,
            "start_urls": [url],
            "custom_id": custom_id
        }

        api_url = f"https://api.webscraper.io/api/v1/scraping-job?api_token={API_TOKEN}"
        response = requests.post(api_url, json=payload, timeout=30)

        # 4. 创建 TrackingJob
        if response.status_code in [200, 201, 202]:
            job_id = response.json().get('id')
            TrackingJob.objects.create(
                batch=tracking_batch,
                job_id=job_id,
                custom_id=custom_id,
                target_url=url,
                index=index,
                status='pending'
            )
            return {'status': 'success', 'job_id': job_id}
        else:
            return {'status': 'failed', 'reason': f"API error: {response.status_code}"}

    finally:
        # 5. 强制睡眠 6 秒（频率限制）
        time.sleep(6)
```

### 1.5.3 频率限制保证

**策略**: 无论成功、失败还是跳过，都睡眠 6 秒

**计算**:
```
15 分钟 = 900 秒
900 秒 ÷ 6 秒/任务 = 150 任务/15分钟
150 < 200 (API 限制) ✅
```

**受保护场景**:
- 大批量断点续传（大量跳过）
- API 临时故障（大量失败）
- 网络超时（异常情况）
- 任意混合场景

---

## Phase 2: WebScraper 抓取

### 2.1 WebScraper 配置

**Sitemap ID**: `1424233`

**Sitemap 选择器配置** (参考):
```json
{
  "selectors": [
    {
      "id": "お問い合わせ番号",
      "type": "Text",
      "selector": "table.tableType01 td:nth-child(1)"
    },
    {
      "id": "最新年月日",
      "type": "Text",
      "selector": "table.tableType01 td:nth-child(2)"
    },
    {
      "id": "最新状態",
      "type": "Text",
      "selector": "table.tableType01 td:nth-child(3)"
    }
  ]
}
```

### 2.2 抓取结果格式

**CSV 输出示例**:
```csv
web-scraper-order,web-scraper-start-url,お問い合わせ番号,最新年月日,最新状態,time-scraped
1,https://trackings.post.japanpost.jp/...,1837-9277-9166,2026/01/09 10:37,配達中,2026-01-21 15:30:00
2,https://trackings.post.japanpost.jp/...,1837-9277-7895,2026/01/08 14:22,お届け先にお届け済み,2026-01-21 15:30:00
```

**关键列说明**:
- `お問い合わせ番号`: 追踪号（格式: XXXX-XXXX-XXXX）
- `最新年月日`: 最新状态时间（格式: YYYY/MM/DD HH:MM）
- `最新状態`: 最新配送状态
- `time-scraped`: 抓取时间戳

### 2.3 Webhook 配置

WebScraper 完成后会调用：
```
POST /api/acquisition/webscraper/webscraper-tracking/?t=<token>

Body:
{
  "scrapingjob_id": "123456",
  "custom_id": "jpt10-a7f3646b-purchasing",
  "status": "completed"
}
```

---

## Phase 3: Webhook 处理与数据落库

### 3.1 Webhook 接收

**文件**: `apps/data_acquisition/views.py:703-804`

**端点**: `POST /api/acquisition/webscraper/webscraper-tracking/`

**验证**:
1. Token 验证（`WEBSCRAPER_WEBHOOK_TOKEN` 或 `BATCH_STATS_API_TOKEN`）
2. Source 解析（通过 `custom_id` 前缀 `jpt10-` 识别）
3. Tracker 存在性检查

**任务调度**:
```python
process_webscraper_tracking.delay(
    source_name='japan_post_tracking_10',
    job_id=job_id,
    batch_uuid=batch_uuid,
    request_data=request.data,
    dry_run=False
)
```

### 3.2 Webhook 处理任务

**文件**: `apps/data_acquisition/tasks.py:435-864`

**Celery 配置**:
- **队列**: `tracking_webhook_queue`
- **容器**: `data-platform-celery-tracking-phase2`
- **并发度**: 2
- **超时**: 300 秒

**处理流程**:
```python
def process_webscraper_tracking(source_name, job_id, batch_uuid, request_data):
    # 1. 查找 TrackingJob
    custom_id = request_data.get('custom_id')
    tracking_job = TrackingJob.objects.get(custom_id=custom_id)

    # 2. 下载 CSV 数据
    content = fetch_webscraper_export_sync(job_id, format="csv")
    df = pd.read_csv(io.BytesIO(content), encoding="utf-8-sig")

    # 3. 调用 tracker
    result = run_tracker('japan_post_tracking_10', df)

    # 4. 检查 tracker 执行结果
    tracker_failed = False
    error_keywords = [
        'Failed to process',
        'Missing required columns',
        'Empty DataFrame',
        'No valid tracking data found',
        'Error updating record',
    ]
    for keyword in error_keywords:
        if keyword in result:
            tracker_failed = True
            break

    # 5. 更新 TrackingJob 状态
    if tracker_failed:
        tracking_job.mark_failed(error_message=result)
    else:
        tracking_job.mark_completed()  # 触发 TrackingBatch 进度更新

    return {'status': 'success' if not tracker_failed else 'error'}
```

### 3.3 Tracker 数据解析

**文件**: `apps/data_acquisition/trackers/japan_post_tracking_10.py`

#### 3.3.1 数据提取

```python
def extract_tracking_data(df: pd.DataFrame) -> List[Dict]:
    # 1. 过滤有效追踪号（格式: XXXX-XXXX-XXXX）
    pattern = r'^\d{4}-\d{4}-\d{4}$'
    mask = df['お問い合わせ番号'].astype(str).str.match(pattern)
    df_filtered = df[mask].copy()

    # 2. 列名映射
    column_mapping = {
        'お問い合わせ番号': 'tracking_number',
        '最新年月日': 'delivery_status_query_time',
        '最新状態': 'latest_delivery_status',
        'time-scraped': 'last_info_updated_at'
    }

    # 3. 清理文本（去除多余空白和换行）
    df_result['delivery_status_query_time'] = df_result['delivery_status_query_time'].apply(clean_text)

    return df_result.to_dict(orient='records')
```

#### 3.3.2 日期时间解析

```python
def parse_japanese_datetime(datetime_str: str) -> Optional[datetime]:
    """
    解析日本日期时间格式

    支持格式:
    - "2026/01/09 10:37"
    - "2026/01/09 10:37:25"
    - "2026-01-09 10:37"
    - "2026-01-09 10:37:25"
    """
    formats = [
        '%Y/%m/%d %H:%M:%S',
        '%Y/%m/%d %H:%M',
        '%Y-%m-%d %H:%M:%S',
        '%Y-%m-%d %H:%M',
    ]

    for fmt in formats:
        try:
            dt = datetime.strptime(datetime_str, fmt)
            # 本地化到东京时区
            tokyo_tz = pytz.timezone('Asia/Tokyo')
            if dt.tzinfo is None:
                dt = tokyo_tz.localize(dt)
            return dt
        except ValueError:
            continue

    return None
```

#### 3.3.3 数据库更新

```python
def update_purchasing_records(tracking_data: List[Dict]) -> Dict[str, int]:
    updated_count = 0
    not_found_count = 0
    error_count = 0

    for item in tracking_data:
        # 1. 提取 12 位数字追踪号
        tracking_number = item.get('tracking_number')  # "1837-9316-7924"
        digits_only = re.sub(r'\D', '', tracking_number)  # "183793167924"

        if len(digits_only) != 12:
            error_count += 1
            continue

        # 2. 查询匹配的 Purchasing 记录
        purchasing_records = Purchasing.objects.filter(
            tracking_number__icontains=digits_only
        )

        # 3. 精确匹配（提取数据库中的数字部分）
        matched_records = []
        for record in purchasing_records:
            record_digits = re.sub(r'\D', '', record.tracking_number or '')
            if record_digits == digits_only:
                matched_records.append(record)

        if not matched_records:
            not_found_count += 1
            continue

        # 4. 更新每条匹配的记录
        for record in matched_records:
            # 解析日期时间
            delivery_status_query_time = parse_japanese_datetime(
                item.get('delivery_status_query_time')
            )

            # 更新字段
            record.delivery_status_query_time = delivery_status_query_time
            record.latest_delivery_status = item.get('latest_delivery_status')
            record.last_info_updated_at = timezone.now()
            record.delivery_status_query_source = 'japan_post_tracking_10'

            # 保存（使用 update_fields 优化性能）
            record.save(update_fields=[
                'delivery_status_query_time',
                'latest_delivery_status',
                'last_info_updated_at',
                'delivery_status_query_source'
            ])

            updated_count += 1

    return {
        'updated': updated_count,
        'not_found': not_found_count,
        'errors': error_count,
        'total_processed': len(tracking_data)
    }
```

### 3.4 TrackingBatch 状态更新

**触发机制**: `TrackingJob.mark_completed()` → `TrackingBatch.update_progress()`

```python
# TrackingJob 模型方法
def mark_completed(self):
    self.status = 'completed'
    self.completed_at = timezone.now()
    self.save()

    # 触发批次进度更新
    self.batch.update_progress()

# TrackingBatch 模型方法
def update_progress(self):
    completed = self.jobs.filter(status='completed').count()
    self.completed_jobs = completed

    if completed >= self.total_jobs:
        self.status = 'completed'
    elif self.jobs.filter(status='failed').exists():
        self.status = 'partially_completed'

    self.save()
```

---

## 配置说明

### 4.1 环境变量

**WebScraper API**:
```python
# config/settings/base.py
WEB_SCRAPER_API_TOKEN = "your-api-token"
WEB_SCRAPER_EXPORT_URL_TEMPLATE = "https://api.webscraper.io/api/v1/scraping-job/{job_id}/csv"
WEBSCRAPER_WEBHOOK_TOKEN = "your-webhook-token"
```

**Sitemap ID**:
```python
# apps/data_acquisition/tasks.py
SITEMAP_IDS = {
    'japan_post_tracking_10': 1424233,
}
```

**Source 映射**:
```python
# config/settings/base.py
WEB_SCRAPER_SOURCE_MAP = {
    "japan_post_tracking_10": "japan_post_tracking_10",
}
```

### 4.2 查询间隔配置

```python
# config/settings/base.py
DELIVERY_STATUS_QUERY_INTERVAL_HOURS = 6  # 默认 6 小时
```

**作用**: 控制同一追踪号的最小查询间隔，避免频繁查询。

### 4.3 任务配置

```python
# apps/data_acquisition/tasks.py
TRACKING_TASK_CONFIGS = {
    'japan_post_tracking_10': {
        'path_keyword': 'japan_post_tracking_10',
        'filename_prefix': 'JPT10-',
        'api_token': WEBSCRAPER_API_TOKEN,
        'sitemap_id': 1424233,
        'custom_id_prefix': 'jpt10',
        'sync_log_triggered': 'japan_post_tracking_10_triggered',
        'sync_log_completed': 'japan_post_tracking_10_completed',
        'display_name': 'Japan Post Tracking 10',
    },
}
```

---

## 监控与故障排查

### 5.1 日志关键字

**Phase 1 - Worker 查询**:
```bash
# 查询记录
docker logs data-platform-celery-japan-post-tracking-10-tracking-number 2>&1 | grep "\[japan_post_tracking_10_tracking_number_worker\]"

# 关键日志
[japan_post_tracking_10_tracking_number_worker] Found 100 candidate records
[japan_post_tracking_10_tracking_number_worker] Filtered 10 valid records with tracking numbers of length 12
[japan_post_tracking_10_tracking_number_worker] Constructed URL with 10 tracking numbers
[japan_post_tracking_10_tracking_number_worker] Created TrackingBatch a7f3646b
[japan_post_tracking_10_tracking_number_worker] Published task: jpt10-a7f3646b-purchasing
```

**Phase 1.5 - 任务发布**:
```bash
# 发布日志
docker logs data-platform-celery-tracking-phase1 2>&1 | grep "jpt10-"

# 关键日志
[Task xxx] Publishing single URL: task=japan_post_tracking_10, custom_id=jpt10-a7f3646b-purchasing
[Task xxx] Successfully published: jpt10-a7f3646b-purchasing (job_id=123456)
[Task xxx] Rate limit sleep (6s) completed
```

**Phase 3 - Webhook 处理**:
```bash
# Webhook 日志
docker logs data-platform-celery-tracking-phase2 2>&1 | grep "\[japan_post_tracking_10\]"

# 关键日志
[japan_post_tracking_10] Processing DataFrame with 10 rows
[japan_post_tracking_10] DataFrame columns: ['お問い合わせ番号', '最新年月日', '最新状態', ...]
[japan_post_tracking_10] Extracted 10 tracking records
[japan_post_tracking_10] Japan Post Tracking 10 processing completed: 10 updated, 0 not found, 0 errors
```

### 5.2 数据库查询

**查看最近的批次**:
```python
from apps.data_acquisition.models import TrackingBatch, TrackingJob

# 最近的批次
latest_batch = TrackingBatch.objects.filter(
    task_name='japan_post_tracking_10'
).order_by('-created_at').first()

print(f"Batch: {latest_batch.batch_uuid}")
print(f"Status: {latest_batch.status}")
print(f"Progress: {latest_batch.completed_jobs}/{latest_batch.total_jobs}")

# 批次的任务
jobs = latest_batch.jobs.all()
for job in jobs:
    print(f"  Job: {job.custom_id}, Status: {job.status}")
```

**查看更新的记录**:
```python
from apps.data_aggregation.models import Purchasing

# 最近更新的记录
recent = Purchasing.objects.filter(
    delivery_status_query_source='japan_post_tracking_10'
).order_by('-last_info_updated_at')[:10]

for p in recent:
    print(f"{p.order_number}: {p.tracking_number}")
    print(f"  Status: {p.latest_delivery_status}")
    print(f"  Query Time: {p.delivery_status_query_time}")
    print(f"  Updated: {p.last_info_updated_at}")
```

### 5.3 常见问题

#### 问题 1: TrackingBatch 显示 completed 但数据库未更新

**排查步骤**:
1. 检查 `tracking_phase2` 容器日志，搜索 `[japan_post_tracking_10]`
2. 查看是否有错误信息（列名不匹配、日期格式错误等）
3. 检查 TrackingJob 状态是否为 `failed`

**解决方案**:
- 如果是列名问题：检查 WebScraper sitemap 配置
- 如果是日期格式：`parse_japanese_datetime` 函数会记录警告
- 如果是匹配失败：检查追踪号格式是否正确

#### 问题 2: Worker 未查询到记录

**排查步骤**:
1. 检查选取条件是否过于严格
2. 验证数据库中是否有符合条件的记录
3. 检查 `DELIVERY_STATUS_QUERY_INTERVAL_HOURS` 配置

**测试查询**:
```python
from apps.data_aggregation.models import Purchasing
from django.db.models import Q
from django.utils import timezone
from datetime import timedelta

time_threshold = timezone.now() - timedelta(hours=6)

candidates = Purchasing.objects.filter(
    Q(order_number__istartswith='w'),
    ~Q(latest_delivery_status__in=['配達完了', 'お届け先にお届け済み']),
    Q(delivery_status_query_time__isnull=True) |
    Q(delivery_status_query_time__lt=time_threshold) |
    Q(latest_delivery_status='伝票番号未登録'),
    Q(shipping_method='JP LOGISTICS GROUP CO., LTD.')
).exclude(
    tracking_number__isnull=True
).exclude(
    tracking_number=''
)

print(f"Found {candidates.count()} candidates")
```

#### 问题 3: API 频率限制

**症状**: WebScraper API 返回 429 Too Many Requests

**排查**:
- 检查 `publish_tracking_batch` 是否正确睡眠 6 秒
- 查看 15 分钟内的发布数量

**验证**:
```bash
# 统计最近 15 分钟的发布数
docker logs data-platform-celery-tracking-phase1 --since 15m 2>&1 | grep "Successfully published" | wc -l
```

**理论最大值**: 150 个/15分钟（900秒 ÷ 6秒）

#### 问题 4: Webhook 未收到

**排查步骤**:
1. 检查 WebScraper 任务状态（访问 WebScraper.io 后台）
2. 验证 webhook URL 配置
3. 检查 Django 日志是否有 webhook 请求记录

**手动触发 webhook 处理**:
```python
from apps.data_acquisition.tasks import process_webscraper_tracking

# 手动触发（用于测试）
process_webscraper_tracking.delay(
    source_name='japan_post_tracking_10',
    job_id='<从 WebScraper 后台获取>',
    batch_uuid='<TrackingBatch UUID>',
    request_data={'custom_id': 'jpt10-xxxxx-purchasing'},
    dry_run=False
)
```

### 5.4 监控指标

**推荐监控项**:
1. Worker 执行频率（每 X 分钟触发一次）
2. 每次查询到的记录数
3. TrackingBatch 完成率
4. TrackingJob 失败率
5. Purchasing 记录更新数量
6. API 调用频率（确保 < 200/15分钟）

**SyncLog 记录**:
```python
from apps.data_acquisition.models import SyncLog

# 查看最近的同步日志
logs = SyncLog.objects.filter(
    operation_type__in=[
        'japan_post_tracking_10_tracking_number_completed',
        'japan_post_tracking_10_triggered',
        'japan_post_tracking_10_completed'
    ]
).order_by('-timestamp')[:10]

for log in logs:
    print(f"{log.timestamp}: {log.operation_type}")
    print(f"  Success: {log.success}")
    print(f"  Message: {log.message}")
    print(f"  Details: {log.details}")
```

---

## 附录

### A. 相关文件清单

**Worker**:
- `apps/data_acquisition/workers/japan_post_tracking_10_tracking_number.py`
- `apps/data_acquisition/workers/celery_japan_post_tracking_10_tracking_number.py`
- `apps/data_acquisition/workers/tasks_japan_post_tracking_10_tracking_number.py`
- `apps/data_acquisition/management/commands/run_japan_post_tracking_10_tracking_number.py`

**Tracker**:
- `apps/data_acquisition/trackers/japan_post_tracking_10.py`
- `apps/data_acquisition/trackers/registry_tracker.py`

**任务**:
- `apps/data_acquisition/tasks.py` (publish_tracking_batch, process_webscraper_tracking)

**视图**:
- `apps/data_acquisition/views.py` (WebScraperTrackingViewSet)

**配置**:
- `config/settings/base.py`
- `apps/data_acquisition/celery.py`
- `docker/entrypoint.sh`

**模型**:
- `apps/data_acquisition/models.py` (TrackingBatch, TrackingJob, SyncLog)
- `apps/data_aggregation/models.py` (Purchasing)

### B. 数据流图

```
Purchasing DB
    ↓ (query with filters)
JapanPostTracking10TrackingNumberWorker
    ↓ (10 records)
Construct URL (10 tracking numbers)
    ↓
Create TrackingBatch (total_jobs=1)
    ↓
publish_tracking_batch.apply_async
    ↓ (dispatch to queue)
publish_tracking_queue
    ↓ (process by phase1 worker)
Call WebScraper API
    ↓
Create TrackingJob (status=pending)
    ↓ (sleep 6s)
WebScraper.io (scraping)
    ↓ (completed)
Send Webhook
    ↓
Django /api/acquisition/webscraper/webscraper-tracking/
    ↓ (verify token, resolve source)
process_webscraper_tracking.delay
    ↓ (dispatch to tracking_webhook_queue)
tracking_phase2 worker
    ↓
Download CSV from WebScraper
    ↓
Parse CSV to DataFrame
    ↓
Call japan_post_tracking_10(df)
    ↓
extract_tracking_data
    ↓
parse_japanese_datetime
    ↓
update_purchasing_records
    ↓ (match by tracking number)
Update Purchasing DB
    ↓
TrackingJob.mark_completed()
    ↓
TrackingBatch.update_progress()
    ↓
TrackingBatch.status = completed
```

### C. 版本历史

- **2026-01-21**: 初始版本，完整链路文档
  - 添加 Phase 1-3 详细说明
  - 添加日期时间解析逻辑
  - 添加 tracker 执行结果验证
  - 添加统一的 6 秒睡眠策略

---

## 参考文档

- [追踪任务流程 Part 1: Excel 处理与任务发布](./TRACKING_FLOW_PART1_PUBLISHING.md)
- [追踪任务流程 Part 2: Webhook 处理与数据落库](./TRACKING_FLOW_PART2_WEBHOOK.md)
- [Worker 架构文档](./WORKER_ARCHITECTURE.md)
- [Data Acquisition Workers](./DATA_ACQUISITION_WORKERS.md)
