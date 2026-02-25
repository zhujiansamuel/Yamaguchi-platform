# Celery Worker 架构文档

本文档描述了数据采集系统的 Celery Worker 架构，包括所有 worker 的职责、配置和任务路由规则。

---

## 架构概览

系统采用**多阶段分离架构**，将追踪任务流程拆分为 3 个独立阶段，每个阶段由专用 worker 处理：

```
┌─────────────────────────────────────────────────────────────────┐
│                    追踪任务完整流程                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Phase 1: Excel 处理 (快速，分钟级)                             │
│  ┌──────────────────────────────────────────────────┐          │
│  │ Worker: celery_worker_tracking_phase1            │          │
│  │ Queue:  tracking_excel_queue                     │          │
│  │ 任务:   - process_tracking_excel                 │          │
│  │        - process_japan_post_tracking_10_excel    │          │
│  │ 职责:   读取 Excel → 提取 URL → 投递发布任务     │          │
│  └──────────────────────────────────────────────────┘          │
│                          ↓ (2秒间隔投递)                         │
│                                                                 │
│  Phase 1.5: 串行发布 (单 URL，1分钟/任务)                       │
│  ┌──────────────────────────────────────────────────┐          │
│  │ Worker: celery_worker_publish_tracking_batch     │          │
│  │ Queue:  publish_tracking_queue                   │          │
│  │ 任务:   - publish_tracking_batch                 │          │
│  │ 职责:   单 URL 发布 → WebScraper API → 睡眠 6秒  │          │
│  └──────────────────────────────────────────────────┘          │
│                          ↓                                      │
│                   WebScraper 执行爬虫                            │
│                          ↓                                      │
│                                                                 │
│  Phase 2: Webhook 处理 (数据解析，5分钟/任务)                   │
│  ┌──────────────────────────────────────────────────┐          │
│  │ Worker: celery_worker_tracking_phase2            │          │
│  │ Queue:  tracking_webhook_queue                   │          │
│  │ 任务:   - process_webscraper_tracking            │          │
│  │        - batch_writeback_tracking_data           │          │
│  │ 职责:   接收 Webhook → 下载 CSV → 解析数据       │          │
│  └──────────────────────────────────────────────────┘          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    Yamato 本地任务流程                           │
├─────────────────────────────────────────────────────────────────┤
│  Worker: celery_worker_yamato_tracking_10                       │
│  Queue:  yamato_tracking_10_queue                               │
│  任务:   - process_yamato_tracking_10_excel                     │
│  职责:   读取 Excel → 本地查询 → 保存结果 (5小时超时)           │
└─────────────────────────────────────────────────────────────────┘
```

---

## Worker 详细配置

### 1. celery_worker_tracking_phase1

**职责**: Excel 文件处理和 URL 准备（Phase 1）

| 配置项 | 值 | 说明 |
|--------|---|------|
| **队列** | `tracking_excel_queue` | Excel 处理专用队列 |
| **并发数** | 1 | 单线程处理，避免文件冲突 |
| **超时时间** | 2 小时 | 支持大型 Excel 文件 |
| **max-tasks-per-child** | 1 | 每个任务后重启，释放内存 |
| **内存限制** | 1G | Docker 资源限制 |
| **处理任务** | `process_tracking_excel`<br/>`process_japan_post_tracking_10_excel` | 所有 Excel 触发的追踪任务 |

**启动命令**:
```bash
celery -A apps.data_acquisition.celery worker \
    --loglevel=info \
    --concurrency=1 \
    --queues=tracking_excel_queue \
    --hostname=tracking_phase1@%h \
    --max-tasks-per-child=1 \
    --time-limit=7200 \
    --soft-time-limit=7000
```

**任务流程**:
1. 下载 Excel 文件（从 OnlyOffice 或 WebDAV）
2. 解析 Excel，提取所有 URL
3. 创建 TrackingBatch
4. 批量投递任务到 `publish_tracking_queue`，每个任务间隔 2 秒
5. 快速完成（几分钟内）

---

### 2. celery_worker_publish_tracking_batch ⭐ (新增)

**职责**: 串行发布单个 URL 到 WebScraper API（Phase 1.5）

| 配置项 | 值 | 说明 |
|--------|---|------|
| **队列** | `publish_tracking_queue` | 发布任务专用队列 |
| **并发数** | 1 | **串行处理，确保 API 频率限制** |
| **超时时间** | 1 分钟 | 快速失败，不阻塞后续任务 |
| **max-tasks-per-child** | 100 | 每 100 个任务重启一次 |
| **重试次数** | 0 | 不重试，超时即抛弃 |
| **处理任务** | `publish_tracking_batch` | 单 URL 发布任务 |

**启动命令**:
```bash
celery -A apps.data_acquisition.celery worker \
    --loglevel=info \
    --concurrency=1 \
    --queues=publish_tracking_queue \
    --hostname=publish_tracking@%h \
    --max-tasks-per-child=100 \
    --time-limit=60 \
    --soft-time-limit=55
```

**任务流程**:
1. 接收单个 URL 和 custom_id
2. 检查是否已发布（断点续传）
3. 调用 WebScraper API 创建爬虫任务
4. **强制睡眠 6 秒**（API 频率限制）
5. 返回发布结果（成功/失败/跳过）

**关键特性**:
- ✅ 串行处理，避免 API 并发冲突
- ✅ 1 分钟超时，快速失败
- ✅ 6 秒睡眠，符合 API 频率限制
- ✅ 失败不重试，继续下一个任务

---

### 3. celery_worker_yamato_tracking_10 ⭐ (新增)

**职责**: 处理 Yamato 10 合 1 本地查询任务

| 配置项 | 值 | 说明 |
|--------|---|------|
| **队列** | `yamato_tracking_10_queue` | Yamato 10 专用队列 |
| **并发数** | 1 | 单线程处理 |
| **超时时间** | 5 小时 | 支持大批量查询 |
| **max-tasks-per-child** | 1 | 每个任务后重启 |
| **内存限制** | 1G | Docker 资源限制 |
| **处理任务** | `process_yamato_tracking_10_excel` | Yamato 本地查询任务 |

**启动命令**:
```bash
celery -A apps.data_acquisition.celery worker \
    --loglevel=info \
    --concurrency=1 \
    --queues=yamato_tracking_10_queue \
    --hostname=yamato_tracking_10@%h \
    --max-tasks-per-child=1 \
    --time-limit=18000 \
    --soft-time-limit=17900
```

**任务流程**:
1. 下载 Excel 文件
2. 提取 A 列追踪号
3. 每 10 个追踪号调用 `query_yamato()` 本地查询
4. 保存查询结果到 TrackingJob
5. 标记任务状态（completed/failed）

**关键特性**:
- ✅ 不调用 WebScraper API，本地直接查询
- ✅ 5 小时超时，支持大批量处理
- ✅ 独立队列，不影响其他任务

---

### 4. celery_worker_tracking_phase2

**职责**: WebScraper Webhook 回调处理和数据解析（Phase 2）

| 配置项 | 值 | 说明 |
|--------|---|------|
| **队列** | `tracking_webhook_queue` | Webhook 回调专用队列 |
| **并发数** | 2 | 支持并发处理 |
| **超时时间** | 5 分钟 | 数据解析和数据库操作 |
| **max-tasks-per-child** | 100 | 定期重启 |
| **处理任务** | `process_webscraper_tracking`<br/>`batch_writeback_tracking_data` | Webhook 处理和数据回写 |

**启动命令**:
```bash
celery -A apps.data_acquisition.celery worker \
    --loglevel=info \
    --concurrency=2 \
    --queues=tracking_webhook_queue \
    --hostname=tracking_phase2@%h \
    --max-tasks-per-child=100 \
    --time-limit=300 \
    --soft-time-limit=270
```

**任务流程**:
1. 接收 WebScraper Webhook 回调
2. 下载 CSV 导出文件
3. 解析数据并验证
4. 调用对应的 Tracker 更新数据库
5. 更新 TrackingJob 状态
6. 触发 Excel 回写任务（每 10 个完成一次）

---

### 5. celery_worker_acquisition

**职责**: 通用数据采集任务

| 配置项 | 值 | 说明 |
|--------|---|------|
| **队列** | `acquisition_queue` | 默认队列 |
| **并发数** | 4 | 支持并发 |
| **超时时间** | 30 分钟 | 通用超时 |
| **处理任务** | 所有其他 acquisition 任务 | 不包括追踪任务 |

**启动命令**:
```bash
celery -A apps.data_acquisition.celery worker \
    --loglevel=info \
    --concurrency=4 \
    --queues=acquisition_queue \
    --hostname=acquisition@%h \
    --max-tasks-per-child=100 \
    --time-limit=1800 \
    --soft-time-limit=1620
```

---

### 6. celery_worker_aggregation

**职责**: 数据聚合任务

| 配置项 | 值 | 说明 |
|--------|---|------|
| **队列** | 聚合队列 | 数据聚合专用 |
| **并发数** | 2 | 支持并发 |
| **超时时间** | 5 分钟 | 快速聚合 |

---

## 任务路由规则

任务路由配置位于 `apps/data_acquisition/celery.py`：

```python
task_routes={
    # Phase 1: Excel 读取和准备（快速完成）
    'apps.data_acquisition.tasks.process_tracking_excel':
        {'queue': 'tracking_excel_queue'},
    'apps.data_acquisition.tasks.process_japan_post_tracking_10_excel':
        {'queue': 'tracking_excel_queue'},

    # Phase 1.5: 串行发布任务（独立 worker，单并发，6s 间隔）
    'apps.data_acquisition.tasks.publish_tracking_batch':
        {'queue': 'publish_tracking_queue'},

    # Yamato 10 本地任务（独立 worker，长超时）
    'apps.data_acquisition.tasks.process_yamato_tracking_10_excel':
        {'queue': 'yamato_tracking_10_queue'},

    # Phase 2: Webhook 回调和数据解析
    'apps.data_acquisition.tasks.process_webscraper_tracking':
        {'queue': 'tracking_webhook_queue'},
    'apps.data_acquisition.tasks.batch_writeback_tracking_data':
        {'queue': 'tracking_webhook_queue'},

    # Default queue for other acquisition tasks
    'apps.data_acquisition.tasks.*':
        {'queue': 'acquisition_queue'},
}
```

---

## Docker Compose 配置

所有 worker 在 `docker-compose.yml` 中定义：

```yaml
services:
  # Phase 1: Excel 处理
  celery_worker_tracking_phase1:
    container_name: data-platform-celery-tracking-phase1
    command: celery_worker_tracking_phase1
    deploy:
      resources:
        limits:
          memory: 1G

  # Phase 1.5: 串行发布
  celery_worker_publish_tracking_batch:
    container_name: data-platform-celery-publish-tracking
    command: celery_worker_publish_tracking_batch

  # Yamato 10 本地任务
  celery_worker_yamato_tracking_10:
    container_name: data-platform-celery-yamato-tracking-10
    command: celery_worker_yamato_tracking_10
    deploy:
      resources:
        limits:
          memory: 1G

  # Phase 2: Webhook 处理
  celery_worker_tracking_phase2:
    container_name: data-platform-celery-tracking-phase2
    command: celery_worker_tracking_phase2

  # 通用任务
  celery_worker_acquisition:
    container_name: data-platform-celery-acquisition
    command: celery_worker_acquisition

  celery_worker_aggregation:
    container_name: data-platform-celery-aggregation
    command: celery_worker_aggregation
```

---

## 启动和管理

### 启动所有 Worker

```bash
# 启动所有追踪相关 worker
docker-compose up -d celery_worker_tracking_phase1
docker-compose up -d celery_worker_publish_tracking_batch
docker-compose up -d celery_worker_yamato_tracking_10
docker-compose up -d celery_worker_tracking_phase2
```

### 重启 Worker

```bash
# 重新构建并启动
docker-compose up -d --build celery_worker_tracking_phase1
docker-compose up -d --build celery_worker_publish_tracking_batch
docker-compose up -d --build celery_worker_yamato_tracking_10
docker-compose up -d --build celery_worker_tracking_phase2
```

### 查看 Worker 状态

```bash
# 查看所有容器
docker-compose ps

# 查看特定 worker 日志
docker-compose logs -f celery_worker_publish_tracking_batch
docker-compose logs -f celery_worker_yamato_tracking_10
```

### 查看队列状态

```bash
# 使用 Flower 监控（推荐）
# 访问 http://localhost:5555

# 或使用 Celery 命令
docker-compose exec celery_worker_tracking_phase1 \
    celery -A apps.data_acquisition.celery inspect active_queues
```

---

## 性能优化要点

### 1. Phase 1 快速完成
- ✅ Excel 处理从数小时缩短到几分钟
- ✅ 不等待 API 调用完成即返回
- ✅ Worker 不会被长时间占用

### 2. Phase 1.5 串行发布
- ✅ 单并发确保 API 调用串行化
- ✅ 6 秒睡眠避免频率限制
- ✅ 1 分钟超时快速失败
- ✅ 可横向扩展（增加 worker 实例）

### 3. 内存管理
- ✅ Phase 1: max-tasks-per-child=1，每个任务后重启
- ✅ Phase 1.5: max-tasks-per-child=100，定期重启
- ✅ Yamato 10: max-tasks-per-child=1，处理完即重启

### 4. 断点续传
- ✅ Phase 1: 检查已投递的任务，只投递未投递的
- ✅ Phase 1.5: 检查已发布的 URL，跳过重复发布
- ✅ Yamato 10: 支持批次恢复

---

## 监控指标

### 关键指标

| 指标 | 说明 | 目标值 |
|------|------|--------|
| **Phase 1 完成时间** | Excel 处理到投递完成 | < 5 分钟 |
| **Phase 1.5 发布速率** | URL/小时 | ~600 (每 6 秒 1 个) |
| **Phase 1.5 成功率** | 发布成功 / 总数 | > 95% |
| **Phase 2 处理延迟** | Webhook 到数据库更新 | < 1 分钟 |
| **Worker 内存使用** | Phase 1 / Yamato 10 | < 1G |
| **队列积压** | 待处理任务数 | < 100 |

### 日志监控

```bash
# 查看发布成功率
docker-compose logs celery_worker_publish_tracking_batch | grep "Successfully published"

# 查看失败任务
docker-compose logs celery_worker_publish_tracking_batch | grep "Failed to publish"

# 查看 Phase 1 处理时间
docker-compose logs celery_worker_tracking_phase1 | grep "Excel processing complete"
```

---

## 故障排查

### 问题 1: Phase 1.5 队列积压严重

**症状**: `publish_tracking_queue` 积压大量任务

**原因**:
- Worker 实例不足
- API 调用超时频繁

**解决方案**:
```bash
# 增加 worker 实例（保持并发=1）
docker-compose up -d --scale celery_worker_publish_tracking_batch=3

# 检查 API 响应时间
docker-compose logs celery_worker_publish_tracking_batch | grep "timeout"
```

### 问题 2: Phase 1 任务超时

**症状**: Excel 处理任务超过 2 小时

**原因**:
- Excel 文件过大
- 网络下载缓慢

**解决方案**:
```bash
# 增加超时时间（修改 docker/entrypoint.sh）
--time-limit=10800  # 3 小时

# 检查文件大小
docker-compose logs celery_worker_tracking_phase1 | grep "Extracted"
```

### 问题 3: Yamato 10 查询失败

**症状**: `process_yamato_tracking_10_excel` 返回错误

**原因**:
- SSL 证书验证失败
- 目标网站限流

**解决方案**:
```bash
# 查看详细错误
docker-compose logs celery_worker_yamato_tracking_10 | grep "Query yamato error"

# 检查 SSL 配置
docker-compose exec celery_worker_yamato_tracking_10 python -c \
    "import certifi; print(certifi.where())"
```

---

## 版本历史

### v4.0 (2026-01-16)
- ✅ 重构追踪工作流：分离 Excel 处理和 API 发布
- ✅ 新增 `celery_worker_publish_tracking_batch`（Phase 1.5）
- ✅ 新增 `celery_worker_yamato_tracking_10`（本地任务）
- ✅ `publish_tracking_batch` 改为单 URL 处理模式
- ✅ `process_tracking_excel` 改为投递模式
- ✅ `process_japan_post_tracking_10_excel` 改为投递模式
- ✅ Phase 1 任务从数小时缩短到几分钟

### v3.2 (2026-01-11)
- ✅ 添加智能重定向功能
- ✅ 实现 TrackingBatch 追踪功能

### v3.0 (2026-01-08)
- ✅ 重构为配置驱动架构
- ✅ 支持多种追踪任务类型

---

## 相关文档

- [TRACKING_FLOW_PART1_PUBLISHING.md](./TRACKING_FLOW_PART1_PUBLISHING.md) - Excel 处理到 WebScraper 发布流程
- [TRACKING_FLOW_PART2_WEBHOOK.md](./TRACKING_FLOW_PART2_WEBHOOK.md) - Webhook 接收到数据库更新流程
- [COMPLETE_TRACKING_FLOW.md](./COMPLETE_TRACKING_FLOW.md) - 完整追踪流程（已废弃，拆分为 Part 1 和 Part 2）
