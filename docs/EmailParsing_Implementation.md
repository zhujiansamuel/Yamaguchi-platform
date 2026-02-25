# EmailParsing 模块实现总结

## 概述

已成功在 `apps/data_acquisition/EmailParsing/` 目录下创建了完整的邮件解析模块，包含四个独立的 Celery worker 及其配置文件，并在 Docker Compose 和 entrypoint 脚本中添加了相应的启动配置。

---

## 文件结构

```
apps/data_acquisition/EmailParsing/
├── __init__.py
├── email_content_analysis.py
├── celery_email_content_analysis.py
├── tasks_email_content_analysis.py
├── initial_order_confirmation_email.py
├── celery_initial_order_confirmation_email.py
├── tasks_initial_order_confirmation_email.py
├── order_confirmation_notification_email.py
├── celery_order_confirmation_notification_email.py
├── tasks_order_confirmation_notification_email.py
├── send_notification_email.py
├── celery_send_notification_email.py
└── tasks_send_notification_email.py
```

**共 13 个文件**，包含：
- 4 个 Worker 类文件
- 4 个 Celery 配置文件
- 4 个 Celery 任务定义文件
- 1 个模块初始化文件

---

## 四个 Worker 配置

### 1. Email Content Analysis Worker
- **队列名称**: `email_content_analysis_queue`
- **Worker 名称**: `email_content_analysis_worker`
- **Redis DB**: 10 (共享)
- **并发数**: 1 (单线程)
- **超时配置**: 
  - `time_limit`: 120 秒 (2 分钟)
  - `soft_time_limit`: 110 秒
- **功能**: 从数据库读取邮件 → 解析内容 → 根据邮件类型分发到对应的三个 handler

### 2. Initial Order Confirmation Email Worker
- **队列名称**: `initial_order_confirmation_email_queue`
- **Worker 名称**: `initial_order_confirmation_email_worker`
- **Redis DB**: 10 (共享)
- **并发数**: 1 (单线程)
- **超时配置**: 
  - `time_limit`: 60 秒 (1 分钟)
  - `soft_time_limit`: 55 秒
- **功能**: 处理初始订单确认邮件 → 查询并锁定 Purchasing 记录 → 更新数据

### 3. Order Confirmation Notification Email Worker
- **队列名称**: `order_confirmation_notification_email_queue`
- **Worker 名称**: `order_confirmation_notification_email_worker`
- **Redis DB**: 10 (共享)
- **并发数**: 1 (单线程)
- **超时配置**: 
  - `time_limit`: 60 秒 (1 分钟)
  - `soft_time_limit`: 55 秒
- **功能**: 处理订单确认通知邮件 → 查询并锁定 Purchasing 记录 → 更新数据

### 4. Send Notification Email Worker
- **队列名称**: `send_notification_email_queue`
- **Worker 名称**: `send_notification_email_worker`
- **Redis DB**: 10 (共享)
- **并发数**: 1 (单线程)
- **超时配置**: 
  - `time_limit`: 60 秒 (1 分钟)
  - `soft_time_limit`: 55 秒
- **功能**: 处理发送通知邮件 → 查询并锁定 Purchasing 记录 → 更新数据

---

## Redis 配置

所有四个 worker 共享同一个 Redis DB：

```python
REDIS_DB = config('REDIS_DB_EMAIL_PARSING', default='10')
```

**环境变量**: `REDIS_DB_EMAIL_PARSING=10`

这与现有的 worker（使用 DB 0-9）完全隔离。

---

## 锁机制

所有三个邮件处理 worker（除 Email Content Analysis 外）都使用现有的 `apps/data_acquisition/workers/record_selector.py` 提供的锁机制：

- `acquire_record_for_worker()`: 获取并锁定 Purchasing 记录
- `release_record_lock()`: 释放锁
- 与现有 worker 共享同一套锁机制，确保数据一致性

---

## Docker Compose 配置

在 `docker-compose.yml` 中添加了四个新的服务：

1. `celery_worker_email_content_analysis`
   - 容器名称: `data-platform-celery-email-content-analysis`
   
2. `celery_worker_initial_order_confirmation_email`
   - 容器名称: `data-platform-celery-initial-order-confirmation-email`
   
3. `celery_worker_order_confirmation_notification_email`
   - 容器名称: `data-platform-celery-order-confirmation-notification-email`
   
4. `celery_worker_send_notification_email`
   - 容器名称: `data-platform-celery-send-notification-email`

所有服务配置：
- 依赖: `postgres`, `redis`, `django`
- 网络: `data_platform_internal`
- 卷挂载: 代码、静态文件、媒体文件、日志

---

## Entrypoint 脚本配置

在 `docker/entrypoint.sh` 中添加了四个新的启动命令：

```bash
celery_worker_email_content_analysis
celery_worker_initial_order_confirmation_email
celery_worker_order_confirmation_notification_email
celery_worker_send_notification_email
```

每个命令都会启动对应的 Celery worker，并配置正确的队列、并发数和超时参数。

---

## 任务流程

```
┌─────────────────────────────────────┐
│  Email Content Analysis Worker     │
│  - 从数据库读取邮件                   │
│  - 解析邮件内容                       │
│  - 判断邮件类型                       │
└──────────────┬──────────────────────┘
               │
               ├─────────────────────────────────────┐
               │                                     │
               ▼                                     ▼
┌──────────────────────────┐      ┌──────────────────────────┐
│ Initial Order            │      │ Order Confirmation       │
│ Confirmation Email       │      │ Notification Email       │
│ Worker                   │      │ Worker                   │
│ - 查询 Purchasing 记录    │      │ - 查询 Purchasing 记录    │
│ - 获取锁                  │      │ - 获取锁                  │
│ - 更新数据                │      │ - 更新数据                │
│ - 释放锁                  │      │ - 释放锁                  │
└──────────────────────────┘      └──────────────────────────┘
               │
               ▼
┌──────────────────────────┐
│ Send Notification Email  │
│ Worker                   │
│ - 查询 Purchasing 记录    │
│ - 获取锁                  │
│ - 更新数据                │
│ - 释放锁                  │
└──────────────────────────┘
```

---

## 待实现的功能（TODO）

所有代码文件中已使用 `TODO` 标记了以下需要后续实现的部分：

### Email Content Analysis Worker
1. `fetch_email_from_database()`: 从数据库查询未处理的邮件
2. `analyze_email_content()`: 邮件内容解析和分类逻辑
3. `create_handler_task()`: 导入并调用对应的任务函数

### 三个邮件处理 Worker
1. `find_purchasing_record()`: 根据邮件数据查找对应的 Purchasing 记录
2. `update_purchasing_record()`: 更新 Purchasing 记录的具体字段

---

## 启动方式

### 使用 Docker Compose 启动所有服务

```bash
docker-compose up -d
```

### 单独启动某个 worker

```bash
# Email Content Analysis
docker-compose up -d celery_worker_email_content_analysis

# Initial Order Confirmation Email
docker-compose up -d celery_worker_initial_order_confirmation_email

# Order Confirmation Notification Email
docker-compose up -d celery_worker_order_confirmation_notification_email

# Send Notification Email
docker-compose up -d celery_worker_send_notification_email
```

### 手动启动（用于调试）

```bash
# Email Content Analysis
celery -A apps.data_acquisition.EmailParsing.celery_email_content_analysis worker \
    -Q email_content_analysis_queue -c 1 --loglevel=info

# Initial Order Confirmation Email
celery -A apps.data_acquisition.EmailParsing.celery_initial_order_confirmation_email worker \
    -Q initial_order_confirmation_email_queue -c 1 --loglevel=info

# Order Confirmation Notification Email
celery -A apps.data_acquisition.EmailParsing.celery_order_confirmation_notification_email worker \
    -Q order_confirmation_notification_email_queue -c 1 --loglevel=info

# Send Notification Email
celery -A apps.data_acquisition.EmailParsing.celery_send_notification_email worker \
    -Q send_notification_email_queue -c 1 --loglevel=info
```

---

## 环境变量配置

需要在 `.env` 文件中添加以下配置：

```bash
# EmailParsing Workers Redis DB
REDIS_DB_EMAIL_PARSING=10
```

---

## 测试任务

可以使用以下代码测试任务是否正常工作：

```python
# 测试 Email Content Analysis
from apps.data_acquisition.EmailParsing.tasks_email_content_analysis import process_email
result = process_email.delay()
print(f"Task ID: {result.id}")

# 测试 Initial Order Confirmation Email
from apps.data_acquisition.EmailParsing.tasks_initial_order_confirmation_email import process_email
result = process_email.delay(email_data={'id': 1, 'subject': 'Test'})
print(f"Task ID: {result.id}")
```

---

## 注意事项

1. **Redis DB 隔离**: 确保 `REDIS_DB_EMAIL_PARSING=10` 在 `.env` 文件中正确配置
2. **锁机制共享**: 所有 worker 使用同一套锁机制，确保不会与现有 worker 冲突
3. **单线程配置**: 所有 worker 都配置为单线程（`--concurrency=1`），确保任务串行处理
4. **超时配置**: Email Content Analysis 为 2 分钟，其他三个为 1 分钟
5. **重试机制**: 所有任务默认最多重试 3 次，重试间隔 60 秒
6. **TODO 标记**: 所有需要后续实现的逻辑都已用 `TODO` 标记

---

## 下一步工作

1. 实现邮件读取逻辑（从哪个数据库表读取邮件）
2. 实现邮件解析和分类逻辑
3. 实现 Purchasing 记录匹配逻辑（通过 order_number 或其他字段）
4. 实现数据更新逻辑（确定每种邮件类型更新哪些字段）
5. 添加单元测试和集成测试
6. 配置日志监控和告警

---

## 文件修改清单

### 新增文件
- `apps/data_acquisition/EmailParsing/__init__.py`
- `apps/data_acquisition/EmailParsing/email_content_analysis.py`
- `apps/data_acquisition/EmailParsing/celery_email_content_analysis.py`
- `apps/data_acquisition/EmailParsing/tasks_email_content_analysis.py`
- `apps/data_acquisition/EmailParsing/initial_order_confirmation_email.py`
- `apps/data_acquisition/EmailParsing/celery_initial_order_confirmation_email.py`
- `apps/data_acquisition/EmailParsing/tasks_initial_order_confirmation_email.py`
- `apps/data_acquisition/EmailParsing/order_confirmation_notification_email.py`
- `apps/data_acquisition/EmailParsing/celery_order_confirmation_notification_email.py`
- `apps/data_acquisition/EmailParsing/tasks_order_confirmation_notification_email.py`
- `apps/data_acquisition/EmailParsing/send_notification_email.py`
- `apps/data_acquisition/EmailParsing/celery_send_notification_email.py`
- `apps/data_acquisition/EmailParsing/tasks_send_notification_email.py`

### 修改文件
- `docker-compose.yml`: 添加了四个 worker 服务配置
- `docker/entrypoint.sh`: 添加了四个 worker 启动命令

---

**实现完成日期**: 2026-01-16
