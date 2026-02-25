# Data Acquisition Workers 技术文档

本文档说明 `apps/data_acquisition/workers/` 目录下的 Worker 实现现状，并补充与其配套的物流查询任务。

## 目录

1. [概述](#概述)
2. [架构设计](#架构设计)
3. [Worker 详细说明](#worker-详细说明)
4. [记录锁定机制](#记录锁定机制)
5. [代码插入位置指南](#代码插入位置指南)
6. [数据接口](#数据接口)
7. [启动与部署](#启动与部署)
8. [开发指南](#开发指南)

---

## 概述

### 目的

当前 Data Acquisition 的 Worker/任务分为三类：

1. **Playwright 字段补齐 Worker（3 个）**：面向字段补齐流程，使用 `record_selector.py` 的筛选条件与锁机制，从官网提取订单状态信息。
2. **WebScraper 物流/订单查询 Worker（3 个）**：面向物流状态或订单追踪，组装查询 URL 并发布 WebScraper 任务（不使用 Playwright 锁机制）。
3. **Playwright 账号操作任务（1 个）**：独立的 Apple Store 提货人信息更新任务，直接通过 Celery 调度 Playwright 脚本。

### 处理流程

```
┌──────────────────────────────────────────────────────────────────────────┐
│                         Purchasing 记录生命周期（字段补齐）                │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  新订单创建 ──► Worker 1 ──► Worker 2 ──► Worker 3 ──► Worker 4            │
│  (全部为空)    (confirmed)   (shipped)   (arrival)   (tracking_number)    │
│                                                                          │
│  不符合上述流程的记录 ──► Worker 5 (Temporary Flexible Capture)           │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────┐
│                       Purchasing 记录生命周期（物流查询）                  │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  物流查询 (Japan Post) ──► Worker 6                                       │
│  物流查询 (Yamato) ──────► Celery Task                                    │
│  Apple 提货人更新 ───────► Celery Task (Playwright)                       │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

> 说明：原先的 `estimated_delivery_date_empty` Worker 已被移除；`estimated_delivery_date` 目前由追踪流程或外部解析逻辑更新。

---

## 架构设计

### 目录结构

```
apps/data_acquisition/workers/
├── __init__.py
├── base.py
├── record_selector.py
│
├── confirmed_at_empty.py
├── shipped_at_empty.py
├── estimated_website_arrival_date_empty.py
├── tracking_number_empty.py
├── temporary_flexible_capture.py
├── japan_post_tracking_10_tracking_number.py
│
├── celery_confirmed_at_empty.py
├── celery_shipped_at_empty.py
├── celery_estimated_website_arrival_date_empty.py
├── celery_tracking_number_empty.py
├── celery_temporary_flexible_capture.py
├── celery_japan_post_tracking_10_tracking_number.py
├── celery_worker_yamato_tracking_10_tracking_number.py
├── celery_worker_playwright_apple_pickup.py
│
├── tasks_confirmed_at_empty.py
├── tasks_shipped_at_empty.py
├── tasks_estimated_website_arrival_date_empty.py
├── tasks_tracking_number_empty.py
├── tasks_temporary_flexible_capture.py
├── tasks_japan_post_tracking_10_tracking_number.py
├── tasks_playwright_apple_pickup.py
```

### 类继承关系

```
BasePlaywrightWorker (ABC)
    │
    ├── ConfirmedAtEmptyWorker
    ├── ShippedAtEmptyWorker
    └── EstimatedWebsiteArrivalDateEmptyWorker
```

`TrackingNumberEmptyWorker` / `TemporaryFlexibleCaptureWorker` / `JapanPostTracking10TrackingNumberWorker` 为独立 Worker（不继承 Playwright 基类）。
`Yamato Tracking 10 Tracking Number` 与 `Apple Pickup` 为 Celery Task（逻辑分别在 `apps/data_acquisition/tasks.py` 与 `apps/data_acquisition/workers/tasks_playwright_apple_pickup.py` 中实现）。

---

## Worker 详细说明

### Worker 1: ConfirmedAtEmptyWorker

| 属性 | 值 |
|------|-----|
| 文件 | `confirmed_at_empty.py` |
| Queue | `confirmed_at_empty` |
| Redis DB | 2 |
| 目标字段 | `confirmed_at` |

**选取条件:**
```python
confirmed_at IS NULL
AND shipped_at IS NULL
AND estimated_website_arrival_date IS NULL
AND (tracking_number IS NULL OR tracking_number = '' OR tracking_number = 'nan')
AND estimated_delivery_date IS NULL
```

**业务场景:** 新创建的订单，需要查询官网确认订单是否被接受。

---

### Worker 2: ShippedAtEmptyWorker

| 属性 | 值 |
|------|-----|
| 文件 | `shipped_at_empty.py` |
| Queue | `shipped_at_empty` |
| Redis DB | 3 |
| 目标字段 | `shipped_at` |

**选取条件:**
```python
confirmed_at IS NOT NULL
AND shipped_at IS NULL
AND estimated_website_arrival_date IS NULL
AND (tracking_number IS NULL OR tracking_number = '' OR tracking_number = 'nan')
AND estimated_delivery_date IS NULL
```

**业务场景:** 订单已确认，需要查询官网确认是否已发货。

---

### Worker 3: EstimatedWebsiteArrivalDateEmptyWorker

| 属性 | 值 |
|------|-----|
| 文件 | `estimated_website_arrival_date_empty.py` |
| Queue | `estimated_website_arrival_date_empty` |
| Redis DB | 4 |
| 目标字段 | `estimated_website_arrival_date` |

**选取条件:**
```python
confirmed_at IS NOT NULL
AND shipped_at IS NOT NULL
AND estimated_website_arrival_date IS NULL
AND (tracking_number IS NULL OR tracking_number = '' OR tracking_number = 'nan')
AND estimated_delivery_date IS NULL
```

**业务场景:** 订单已发货，需要从官网获取预计到达日期。

---

### Worker 4: TrackingNumberEmptyWorker

| 属性 | 值 |
|------|-----|
| 文件 | `tracking_number_empty.py` |
| Queue | `tracking_number_empty` |
| Redis DB | 5 |
| 目标字段 | `tracking_number` / `latest_delivery_status` 等（通过 WebScraper 回写） |

**选取条件:**
```python
order_number 以 'w' 开头 (不区分大小写)
AND official_account 关联存在
AND official_account.email 非空
AND tracking_number 为空 (NULL / '' / 'nan')
AND latest_delivery_status NOT IN ['配達完了', 'お届け先にお届け済み']
AND (last_info_updated_at IS NULL OR last_info_updated_at < now - N小时)
```

**业务场景:** 需要从 Apple 官方订单页面触发追踪查询，发布 `official_website_redirect_to_yamato_tracking` 任务。

---

### Worker 5: TemporaryFlexibleCaptureWorker

| 属性 | 值 |
|------|-----|
| 文件 | `temporary_flexible_capture.py` |
| Queue | `temporary_flexible_capture` |
| Redis DB | 7 |
| 目标字段 | 动态确定 |

**选取条件:**
```python
官方账号存在且 email 非空
AND (last_info_updated_at IS NULL OR last_info_updated_at < now - N小时)
AND 动态条件 (多个字段条件以 OR 组合)
```

**业务场景:** 通过动态条件触发 Apple 订单追踪抓取，适用于字段组合异常、需要重新抓取的记录等。

---

### Worker 6: JapanPostTracking10TrackingNumberWorker

| 属性 | 值 |
|------|-----|
| 文件 | `japan_post_tracking_10_tracking_number.py` |
| Queue | `japan_post_tracking_10_tracking_number_queue` |
| Redis DB | 6 |
| 目标字段 | `latest_delivery_status` 等物流字段 |

**选取条件:**
```python
order_number 以 'w' 开头 (不区分大小写)
AND shipping_method = 'JP LOGISTICS GROUP CO., LTD.'
AND tracking_number 提取出的数字长度 = 12
AND latest_delivery_status NOT IN ['配達完了', 'お届け先にお届け済み']
AND (last_info_updated_at IS NULL OR last_info_updated_at < now - N小时)
```

**业务场景:** 针对 Japan Post 物流，批量拼接 10 个 tracking number 的查询 URL，调用 WebScraper API 发起抓取任务，并写入 TrackingBatch/TrackingJob。

---

### Worker 7: Yamato Tracking 10 Tracking Number（Celery Task）

| 属性 | 值 |
|------|-----|
| 实现 | `apps/data_acquisition/tasks.py` 中的 `process_yamato_tracking_10_tracking_number` |
| Queue | `yamato_tracking_10_tracking_number_queue` |
| Redis DB | 8 |
| 目标字段 | `latest_delivery_status` 等物流字段 |

**选取条件:**
```python
order_number 以 'w' 开头 (不区分大小写)
AND shipping_method = 'YAMATO TRANSPORT CO.,LTD.'
AND tracking_number 提取出的数字长度 = 12
AND latest_delivery_status NOT IN ['配達完了', 'お届け先にお届け済み']
AND (
    last_info_updated_at IS NULL
    OR last_info_updated_at < now - N小时
    OR latest_delivery_status 为 “＊＊ お問い合わせ番号が見つかりません...”
)
```

**业务场景:** 针对 Yamato 物流，批量查询最多 10 个 tracking number，调用 `query_yamato()` 完成查询并回写状态。

---

### Worker 8: Playwright Apple Pickup Contact Update（Celery Task）

| 属性 | 值 |
|------|-----|
| 实现 | `apps/data_acquisition/workers/tasks_playwright_apple_pickup.py` 中的 `process_apple_pickup_contact_update` |
| Queue | `playwright_apple_pickup_queue` |
| Redis DB | 9 |
| 目标字段 | Apple Store 订单提货人姓名 |

**调用参数:**
```python
apple_id: Apple ID 邮箱
password: Apple ID 密码
newname: 新提货人姓名（"姓 名"）
ordernumber: 可选，订单号（找不到时回退 product_fallback）
product_fallback: 可选，默认 "iPhone"
item_id: 可选，订单条目 ID，默认 "0000101"
```

**业务场景:** 使用 Playwright 登录 Apple Store 并更新订单提货联系人信息。

---

## 记录锁定机制

> 仅 Playwright 字段补齐 Worker（confirmed/shipped/estimated）使用锁机制；TrackingNumber/TemporaryFlexible/Japan Post/Yamato/Apple Pickup 均不使用记录锁。

### 锁定字段 (Purchasing 模型)

```python
is_locked = BooleanField(default=False)
locked_at = DateTimeField(null=True)
locked_by_worker = CharField(max_length=50)
```

### 锁定流程

```
1. Worker 查询符合条件且未锁定的记录
2. 使用 select_for_update(skip_locked=True) 原子锁定
3. 设置 is_locked=True, locked_at=now(), locked_by_worker=worker_name
4. 执行数据提取
5. 更新记录数据
6. 释放锁: is_locked=False, locked_at=None, locked_by_worker=''
```

### 锁定超时

- **超时时间:** 5 分钟 (`LOCK_TIMEOUT_MINUTES = 5`)
- **过期锁处理:** 超过 5 分钟的锁视为过期，可被其他 Worker 获取
- **清理方式:** 调用 `cleanup_expired_locks()`；需要自行在定时任务中触发

### 核心函数

```python
# 获取并锁定记录
record = acquire_record_for_worker(worker_name, filter_condition)

# 释放记录锁
release_record_lock(record, worker_name)

# 清理过期锁
cleanup_expired_locks()
```

---

## 代码插入位置指南

### 1. Playwright 浏览器初始化

**文件:** `base.py`
**方法:** `initialize_browser()`

```python
def initialize_browser(self) -> None:
    # TODO: Implement Playwright initialization
    # from playwright.sync_api import sync_playwright
    # self._playwright = sync_playwright().start()
    # self._browser = self._playwright.chromium.launch(headless=self.headless)
    # self._context = self._browser.new_context()
    # self._page = self._context.new_page()
    # self._page.set_default_timeout(self.timeout)
    logger.info("Browser initialization placeholder")
```

### 2. 浏览器关闭清理

**文件:** `base.py`
**方法:** `close_browser()`

```python
def close_browser(self) -> None:
    # TODO: Implement browser cleanup
    # if self._page:
    #     self._page.close()
    # if self._context:
    #     self._context.close()
    # if self._browser:
    #     self._browser.close()
    # if self._playwright:
    #     self._playwright.stop()
    logger.info("Browser cleanup placeholder")
```

### 3. Playwright Worker 逻辑插入位置

各 Worker 的 `execute()` 方法中均有 TODO 注释，示例：

- `confirmed_at_empty.py`：确认状态提取
- `shipped_at_empty.py`：发货状态提取
- `estimated_website_arrival_date_empty.py`：官网预计到达日期提取

TrackingNumber/TemporaryFlexible/Japan Post/Yamato/Apple Pickup 任务不使用上述 BasePlaywrightWorker。

---

## 数据接口

### Purchasing 模型关键字段

```python
class Purchasing(models.Model):
    uuid = UUIDField()
    order_number = CharField(max_length=100)

    # Playwright Worker 目标字段
    confirmed_at = DateTimeField(null=True)
    shipped_at = DateTimeField(null=True)
    estimated_website_arrival_date = DateField(null=True)
    tracking_number = CharField(max_length=50)
    estimated_delivery_date = DateField(null=True)

    # 物流查询字段
    latest_delivery_status = CharField(max_length=10)
    delivery_status_query_time = DateTimeField(null=True)
    last_info_updated_at = DateTimeField(null=True)
    shipping_method = CharField(max_length=100)

    # 锁定字段
    is_locked = BooleanField(default=False)
    locked_at = DateTimeField(null=True)
    locked_by_worker = CharField(max_length=50)
```

### Playwright Worker 输入/输出接口

每个 Worker 的 `execute()` 方法接收 `task_data` 字典（目前各 Worker 均未强制依赖输入参数）：

```python
task_data = {
    'force_reprocess': False,
    'timeout_override': 60000,
    'debug_mode': False,
}
```

`BasePlaywrightWorker.run()` 会包装返回结构：

```python
{
    'status': 'success' | 'error',
    'result': { ... } | None,
    'error': 'error message' | None
}
```

### Japan Post Worker 输出接口

```python
{
    'status': 'success',
    'batch_uuid': '...',
    'total_records': 10,
    'tracking_numbers': [...],
    'url': 'https://trackings.post.japanpost.jp/...',
    'custom_id': 'jpt10-...'
}
```

### Celery Task 调用接口

```python
# Playwright Worker
from apps.data_acquisition.workers.tasks_confirmed_at_empty import process_record
result = process_record.delay()

# Japan Post Worker
from apps.data_acquisition.workers.tasks_japan_post_tracking_10_tracking_number import process_record
result = process_record.delay()

# Apple Pickup Playwright Task
from apps.data_acquisition.workers.tasks_playwright_apple_pickup import process_apple_pickup_contact_update
result = process_apple_pickup_contact_update.delay(
    apple_id="...",
    password="...",
    newname="山田 太郎",
    ordernumber="..."
)
```

### 记录选择器接口

```python
from apps.data_acquisition.workers.record_selector import (
    acquire_record_for_worker,
    release_record_lock,
    cleanup_expired_locks,
    get_confirmed_at_empty_filter,
    get_shipped_at_empty_filter,
    get_estimated_website_arrival_date_empty_filter,
    get_tracking_number_empty_filter,
    get_temporary_flexible_capture_filter,
)
```

---

## 启动与部署

### 环境变量配置

```bash
REDIS_HOST=localhost
REDIS_PORT=6379

# Playwright Worker Redis DB
REDIS_DB_CONFIRMED_AT_EMPTY=2
REDIS_DB_SHIPPED_AT_EMPTY=3
REDIS_DB_ESTIMATED_WEBSITE_ARRIVAL_DATE_EMPTY=4
REDIS_DB_TRACKING_NUMBER_EMPTY=5
REDIS_DB_JAPAN_POST_TRACKING_10_TRACKING_NUMBER=6
REDIS_DB_TEMPORARY_FLEXIBLE_CAPTURE=7

# Yamato Tracking 10 Tracking Number
REDIS_DB_YAMATO_TRACKING_10_TRACKING_NUMBER=8

# Playwright Apple Pickup
REDIS_DB_PLAYWRIGHT_APPLE_PICKUP=9
```

### 启动命令

```bash
# Worker 1: confirmed_at_empty
celery -A apps.data_acquisition.workers.celery_confirmed_at_empty worker \
    -Q confirmed_at_empty -c 1 --loglevel=info

# Worker 2: shipped_at_empty
celery -A apps.data_acquisition.workers.celery_shipped_at_empty worker \
    -Q shipped_at_empty -c 1 --loglevel=info

# Worker 3: estimated_website_arrival_date_empty
celery -A apps.data_acquisition.workers.celery_estimated_website_arrival_date_empty worker \
    -Q estimated_website_arrival_date_empty -c 1 --loglevel=info

# Worker 4: tracking_number_empty
celery -A apps.data_acquisition.workers.celery_tracking_number_empty worker \
    -Q tracking_number_empty -c 1 --loglevel=info

# Worker 5: temporary_flexible_capture
celery -A apps.data_acquisition.workers.celery_temporary_flexible_capture worker \
    -Q temporary_flexible_capture -c 1 --loglevel=info

# Worker 6: japan_post_tracking_10_tracking_number
celery -A apps.data_acquisition.workers.celery_japan_post_tracking_10_tracking_number worker \
    -Q japan_post_tracking_10_tracking_number_queue -c 1 --loglevel=info

# Worker 7: yamato_tracking_10_tracking_number
celery -A apps.data_acquisition.workers.celery_worker_yamato_tracking_10_tracking_number worker \
    -Q yamato_tracking_10_tracking_number_queue -c 1 --loglevel=info

# Worker 8: playwright_apple_pickup
celery -A apps.data_acquisition.workers.celery_worker_playwright_apple_pickup worker \
    -Q playwright_apple_pickup_queue -c 1 --loglevel=info
```

### 数据库迁移

```bash
python manage.py migrate data_aggregation 0004_add_worker_lock_fields
```

---

## 开发指南

### 添加新的 Playwright Worker

1. 在 `record_selector.py` 中添加新的过滤函数
2. 创建新的 Worker 类文件 (继承 `BasePlaywrightWorker`)
3. 创建对应的 Celery 配置文件
4. 创建对应的 Tasks 文件
5. 更新 `__init__.py` 导出
6. 更新 `.env.example` 添加新的 Redis DB

### 实现 Playwright 逻辑的最佳实践

```python
def execute(self, task_data: dict) -> dict:
    record = self.acquire_record()
    if record is None:
        return {'status': 'no_record', 'message': '...'}

    try:
        self._page.goto('https://example.com/orders')
        self._page.wait_for_selector('#order-search')
        self._page.fill('#order-search', record.order_number)
        self._page.click('#search-button')
        self._page.wait_for_selector('.order-result')
        date_text = self._page.text_content('.confirmed-date')
        confirmed_at = parse_date(date_text)
        record.confirmed_at = confirmed_at
        record.save(update_fields=['confirmed_at', 'updated_at'])
        return {
            'status': 'success',
            'record_id': record.id,
            'extracted_data': {'confirmed_at': str(confirmed_at)},
        }
    finally:
        self.release_record(record)
```

### 错误处理策略

| 错误类型 | 处理方式 |
|---------|---------|
| 无匹配记录 | 返回 `status: no_record`，不重试 |
| 页面超时 | 截图保存，重试（最多3次） |
| 元素未找到 | 记录日志，重试 |
| 数据解析失败 | 记录原始数据，标记需人工处理 |
| 网络错误 | 重试（最多3次，间隔60秒） |

---

## 附录

### Redis DB 分配表

| DB | 用途 |
|----|------|
| 0 | data_aggregation (主应用) |
| 1 | data_acquisition (同步任务) |
| 2 | confirmed_at_empty Worker |
| 3 | shipped_at_empty Worker |
| 4 | estimated_website_arrival_date_empty Worker |
| 5 | tracking_number_empty Worker |
| 6 | japan_post_tracking_10_tracking_number Worker |
| 7 | temporary_flexible_capture Worker |
| 8 | yamato_tracking_10_tracking_number Worker |
| 9 | playwright_apple_pickup Worker |

### 相关文档

- [Purchasing API 文档](./API_PURCHASING.md)
- [系统架构文档](../ARCHITECTURE.md)
- [Docker 部署指南](../DOCKER_DEPLOYMENT.md)
