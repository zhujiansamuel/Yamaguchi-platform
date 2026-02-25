# Yamato Tracking 10 Tracking Number Worker

## 概述

这是第7个独立worker，专门用于处理从Purchasing模型查询符合条件的记录并进行Yamato物流查询的任务。

## 功能

- 从Purchasing模型查询符合以下条件的记录：
  - `order_number` 以 'w' 开头（不区分大小写）
  - `latest_delivery_status` 不在 "配達完了"、"お届け先にお届け済み" 中
  - 满足以下任一条件：
    - `delivery_status_query_time` 为空
    - `delivery_status_query_time` 距离现在超过配置的间隔（默认6小时）
    - `latest_delivery_status` 为 "＊＊ お問い合わせ番号が見つかりません。お問い合わせ番号をご確認の上、お近くの取扱店にお問い合わせください。"
  - `tracking_number` 不为空，提取到的数字是12位
- 先取最多100条候选记录，再筛选10条有效记录
- 使用 `query_yamato()` 函数进行批量查询，并解析HTML落库
- 使用 TrackingBatch/TrackingJob 记录批次与任务状态
- 记录详细日志，查询失败不重试

## 配置

- **Worker名称**: `yamato_tracking_10_tracking_number_worker`
- **队列名称**: `yamato_tracking_10_tracking_number_queue`
- **Redis DB**: 8
- **并发数**: 1（单线程）
- **超时时间**: 30分钟（硬超时），25分钟（软超时）

## 启动命令

```bash
celery -A apps.data_acquisition.workers.celery_worker_yamato_tracking_10_tracking_number worker \
    -Q yamato_tracking_10_tracking_number_queue -c 1 --loglevel=info
```

## 触发任务

使用Django管理命令手动触发：

```bash
python manage.py run_yamato_tracking_10_tracking_number
```

## 环境变量

需要在 `.env` 文件中配置：

```env
REDIS_DB_YAMATO_TRACKING_10_TRACKING_NUMBER=8
```

## 任务流程

1. 查询Purchasing模型，筛选符合条件的记录（含时间阈值与特殊状态）
2. 使用正则表达式提取tracking_number中的数字
3. 验证数字为12位
4. 最多选取10条记录
5. 创建 TrackingBatch 与 TrackingJob
6. 调用 `query_yamato()` 进行批量查询
7. 解析HTML并更新Purchasing字段（含状态与时间）
8. 记录查询结果到SyncLog
9. 如果查询失败，仅记录日志，不重试

## 日志

所有操作都会记录到：
- Celery worker日志
- Django SyncLog模型（operation_type: `yamato_tracking_10_tracking_number_triggered`、`yamato_tracking_10_tracking_number_completed`）

## 与原有yamato_tracking_10的区别

| 特性 | yamato_tracking_10 | yamato_tracking_10_tracking_number |
|------|-------------------|-----------------------------------|
| 数据来源 | Excel文件 | Purchasing模型 |
| 触发方式 | 文件上传自动触发 | 手动命令触发 |
| Worker | yamato_tracking_10_queue | yamato_tracking_10_tracking_number_queue |
| Redis DB | 原有DB | DB 8 |
| 重试策略 | 最多2次重试 | 不重试 |
| 批次管理 | 使用TrackingBatch/TrackingJob | 使用TrackingBatch/TrackingJob |
