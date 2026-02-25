# Yamato Tracking 10 任务实现文档

## 概述

`yamato_tracking_10` 是一个新的追踪任务，用于批量查询大和运输（Yamato）的追踪信息。与其他追踪任务不同，此任务不使用 WebScraper API，而是直接调用 `query_yamato()` 函数进行批量查询。

## 任务特性

### 1. 文件监控
- **监控文件夹**: `/japan_post_tracking_10/`
- **文件名前缀**: `YT10-`
- **示例文件名**: `YT10-20260116-001.xlsx`

### 2. 数据提取
- **数据源**: Excel 文件 A 列
- **起始行**: 第 2 行（跳过表头）
- **数据类型**: 追踪号（字符串）

### 3. 批量查询
- **批次大小**: 每 10 个追踪号为一组
- **查询函数**: `query_yamato(tracking_numbers)`
- **随机延迟**: 每次查询后随机睡眠 1-50 秒

### 4. 状态追踪
- **TrackingBatch**: 记录整个批次的进度
- **TrackingJob**: 为每个追踪号创建一个 Job（方案 A）
- **断点续传**: 支持任务中断后从断点继续

### 5. 结果记录
- **保存内容**: HTTP 状态码（保存到 `writeback_data` 字段）
- **日志输出**: 完整的 response 内容输出到日志
- **错误处理**: 整组（10个）标记为 failed

## 实现细节

### 配置文件

#### 1. tasks.py - TRACKING_TASK_CONFIGS

```python
'yamato_tracking_10': {
    'path_keyword': 'japan_post_tracking_10',
    'filename_prefix': 'YT10-',
    'custom_id_prefix': 'yt10',
    'sync_log_triggered': 'yamato_tracking_10_triggered',
    'sync_log_completed': 'yamato_tracking_10_completed',
    'display_name': 'Yamato Tracking 10',
    # 注意：此任务不使用 WebScraper API，直接调用 query_yamato() 函数
},
```

### 核心函数

#### 1. query_yamato(tracking_numbers)

**位置**: `apps/data_acquisition/tasks.py`

**功能**: 查询大和运输追踪信息

**参数**:
- `tracking_numbers`: 追踪号列表，最多 10 个

**返回**: `requests.Response` 对象

**特性**:
- 使用 RobustHTTPAdapter 处理 SSL 连接
- 支持最多 10 个追踪号的批量查询
- 自动填充空位（不足 10 个时）

#### 2. process_yamato_tracking_10_excel(file_path, document_url=None)

**位置**: `apps/data_acquisition/tasks.py`

**功能**: 处理 Yamato Tracking 10 任务的主函数

**流程**:

1. **下载 Excel 文件**
   - 优先使用 OnlyOffice 提供的 `document_url`
   - 备用方案：通过 WebDAV 下载

2. **解析 Excel**
   - 读取 A 列数据（从第 2 行开始）
   - 提取所有非空的追踪号

3. **创建 TrackingBatch**
   - 查找现有批次（支持断点续传）
   - 如果不存在，创建新批次

4. **创建 TrackingJob**
   - 为每个追踪号创建一个 TrackingJob
   - 跳过已存在的 Job（断点续传）
   - 使用 `bulk_create` 批量创建

5. **批量查询**
   - 每 10 个追踪号为一组
   - 调用 `query_yamato()` 函数
   - 保存状态码到 `writeback_data`
   - 输出完整响应到日志

6. **错误处理**
   - 整组标记为 failed
   - 记录错误信息到 `error_message`

7. **随机延迟**
   - 每次查询后随机睡眠 1-50 秒
   - 最后一批不睡眠

8. **更新进度**
   - 每批完成后更新 TrackingBatch 进度
   - 自动触发 Excel 回写（每 10 个任务）

### 触发机制

#### views.py - onlyoffice_callback

**修改内容**:

```python
# 自动识别 yamato_tracking_10 任务
if matched_task == 'yamato_tracking_10':
    process_yamato_tracking_10_excel.delay(
        file_path=file_path,
        document_url=url
    )
else:
    process_tracking_excel.delay(
        task_name=matched_task,
        file_path=file_path,
        document_url=url
    )
```

**工作原理**:
1. OnlyOffice 保存文件时触发回调
2. 系统检查文件路径和文件名
3. 匹配到 `yamato_tracking_10` 配置
4. 调用专用的 `process_yamato_tracking_10_excel` 任务

## 数据库模型

### TrackingBatch

| 字段 | 类型 | 说明 |
|------|------|------|
| batch_uuid | UUID | 批次唯一标识 |
| task_name | String | 任务名称（`yamato_tracking_10`） |
| file_path | String | Excel 文件路径 |
| total_jobs | Integer | 总任务数 |
| completed_jobs | Integer | 已完成任务数 |
| failed_jobs | Integer | 失败任务数 |
| status | String | 批次状态（pending/processing/completed/partial） |

### TrackingJob

| 字段 | 类型 | 说明 |
|------|------|------|
| batch | ForeignKey | 关联的 TrackingBatch |
| custom_id | String | 自定义 ID（格式：`yt10-{batch_short}-{序号}`） |
| target_url | String | 追踪号（复用此字段存储） |
| index | Integer | 在 Excel 中的序号 |
| status | String | 任务状态（pending/completed/failed） |
| writeback_data | String | HTTP 状态码 |
| error_message | String | 错误信息（如果失败） |

## 日志记录

### SyncLog 记录

#### 1. 触发日志
```python
operation_type='yamato_tracking_10_triggered'
message='Yamato Tracking 10 task triggered'
details={
    'batch_uuid': batch_uuid_str,
    'total_numbers': len(tracking_numbers)
}
```

#### 2. 完成日志
```python
operation_type='yamato_tracking_10_completed'
message='Processed {count} tracking numbers'
details={
    'batch_uuid': batch_uuid_str,
    'total': total_jobs,
    'success': success_count,
    'failed': failed_count,
    'tracking_batch_id': tracking_batch.id
}
```

### 应用日志

#### 查询成功
```
[Task {task_id}] Query successful, status code: 200
[Task {task_id}] Response preview: <html>...
```

#### 查询失败
```
[Task {task_id}] Query failed for batch {batch_num}: {error}
```

#### 随机延迟
```
[Task {task_id}] Sleeping for {sleep_time} seconds...
```

## 断点续传机制

### 工作原理

1. **查找现有批次**
   ```python
   tracking_batch = TrackingBatch.objects.filter(
       file_path=file_path,
       task_name='yamato_tracking_10',
       status__in=['pending', 'processing']
   ).order_by('-created_at').first()
   ```

2. **查询已创建的 Job**
   ```python
   existing_indices = set(TrackingJob.objects.filter(
       batch=tracking_batch
   ).values_list('index', flat=True))
   ```

3. **跳过已存在的 Job**
   ```python
   for item in tracking_numbers:
       row_index = item['row_index']
       if row_index not in existing_indices:
           # 创建新 Job
   ```

4. **只处理 pending 状态的 Job**
   ```python
   all_jobs = TrackingJob.objects.filter(
       batch=tracking_batch,
       status='pending'
   ).order_by('index')
   ```

### 使用场景

- Excel 文件包含 100 个追踪号
- 第 50 个任务查询时失败（网络中断）
- 重新执行时，系统自动跳过前 50 个，从第 51 个继续

## 使用示例

### 1. 准备 Excel 文件

**文件名**: `YT10-20260116-001.xlsx`

**内容**:
| A 列（追踪号） |
|---------------|
| 123456789012  |
| 234567890123  |
| 345678901234  |
| ...           |

### 2. 上传到 Nextcloud

**路径**: `/japan_post_tracking_10/YT10-20260116-001.xlsx`

### 3. 系统自动处理

1. OnlyOffice 保存文件时触发回调
2. 系统识别为 `yamato_tracking_10` 任务
3. 自动触发 `process_yamato_tracking_10_excel` 任务
4. 任务开始处理：
   - 下载 Excel
   - 提取追踪号
   - 创建 TrackingBatch 和 TrackingJob
   - 批量查询（每 10 个一组）
   - 保存结果

### 4. 查看进度

#### 通过 Django Admin
- 访问 `/admin/data_acquisition/trackingbatch/`
- 查看批次进度和完成状态

#### 通过代码
```python
from apps.data_acquisition.batch_tracker import get_batch_by_file_path

batch = get_batch_by_file_path('/japan_post_tracking_10/YT10-20260116-001.xlsx')
print(f"进度: {batch.completed_jobs}/{batch.total_jobs} ({batch.completion_percentage}%)")
```

### 5. 查看日志

#### Celery 日志
```bash
tail -f /path/to/celery.log | grep yamato_tracking_10
```

#### SyncLog
```python
from apps.data_acquisition.models import SyncLog

logs = SyncLog.objects.filter(
    operation_type__in=[
        'yamato_tracking_10_triggered',
        'yamato_tracking_10_completed'
    ]
).order_by('-created_at')
```

## 监控与调试

### 1. 查看批次状态

```python
from apps.data_acquisition.batch_tracker import get_batch_summary

batch = get_batch_by_file_path('/japan_post_tracking_10/YT10-20260116-001.xlsx')
summary = get_batch_summary(batch)
print(summary)
```

### 2. 查看失败的任务

```python
from apps.data_acquisition.batch_tracker import get_batch_jobs

failed_jobs = get_batch_jobs(batch, status='failed')
for job in failed_jobs:
    print(f"Job {job.custom_id}: {job.error_message}")
```

### 3. 重试失败的任务

由于使用了断点续传机制，只需重新触发任务即可：

```python
from apps.data_acquisition.tasks import process_yamato_tracking_10_excel

process_yamato_tracking_10_excel.delay(
    file_path='/japan_post_tracking_10/YT10-20260116-001.xlsx'
)
```

系统会自动跳过已完成的任务，只处理失败和未处理的任务。

## 注意事项

### 1. 随机延迟
- 每次查询后随机睡眠 1-50 秒
- 避免频繁请求被服务器封禁
- 最后一批不睡眠，加快完成速度

### 2. 错误处理
- 整组（10个）标记为 failed
- 不会因为单个追踪号失败而影响其他组
- 可以通过重新执行任务来重试失败的组

### 3. 数据保存
- 仅保存 HTTP 状态码到 `writeback_data`
- 完整的响应内容输出到日志
- 预留了 `writeback_data` 字段供将来扩展

### 4. 性能优化
- 使用 `bulk_create` 批量创建 TrackingJob
- 每 10 个任务完成后自动触发 Excel 回写
- 批次完成时触发最后一次回写

## 配置要求

### 环境变量
无特殊要求，使用现有的 Nextcloud 和 Celery 配置。

### 依赖包
- `requests`: HTTP 请求
- `certifi`: SSL 证书验证
- `openpyxl`: Excel 文件解析
- `celery`: 异步任务队列

### Celery 队列
- 队列名称: `tracking_excel_queue`
- 最大重试次数: 2
- 重试间隔: 300 秒（5 分钟）

## 扩展建议

### 1. 解析响应内容
如果将来需要解析响应内容，可以在查询成功后添加解析逻辑：

```python
response = query_yamato(batch_numbers)
status_code = response.status_code

# 解析 HTML 内容
from bs4 import BeautifulSoup
soup = BeautifulSoup(response.text, 'html.parser')
# 提取所需字段...

# 保存到 writeback_data
job.writeback_data = f"{status_code}|{parsed_data}"
```

### 2. 单独重试失败的追踪号
可以修改错误处理逻辑，单独标记失败的追踪号：

```python
# 逐个查询（而不是批量）
for job in batch_jobs:
    try:
        response = query_yamato([job.target_url])
        job.writeback_data = str(response.status_code)
        job.status = 'completed'
    except Exception as e:
        job.status = 'failed'
        job.error_message = str(e)
    job.save()
```

### 3. 自定义延迟策略
可以根据时间段调整延迟时间：

```python
from datetime import datetime

hour = datetime.now().hour
if 9 <= hour <= 17:  # 工作时间
    sleep_time = random.randint(10, 60)
else:  # 非工作时间
    sleep_time = random.randint(1, 10)
```

## 文件清单

### 修改的文件
1. `apps/data_acquisition/tasks.py`
   - 添加 `query_yamato()` 函数
   - 添加 `process_yamato_tracking_10_excel()` 任务
   - 在 `TRACKING_TASK_CONFIGS` 中添加配置

2. `apps/data_acquisition/views.py`
   - 导入 `process_yamato_tracking_10_excel`
   - 修改 `onlyoffice_callback` 以支持新任务

### 新增的文件
1. `docs/YAMATO_TRACKING_10_IMPLEMENTATION.md`（本文档）

## 总结

`yamato_tracking_10` 任务已成功实现，具备以下特性：

✅ 自动文件监控和任务触发  
✅ Excel 数据提取（A 列追踪号）  
✅ 批量查询（每 10 个一组）  
✅ 状态追踪（TrackingBatch + TrackingJob）  
✅ 断点续传支持  
✅ 随机延迟（1-50 秒）  
✅ 完整的日志记录  
✅ 错误处理（整组标记为 failed）  
✅ 预留 Excel 回写功能  

任务已集成到现有的追踪任务系统中，可以通过 Nextcloud 文件上传自动触发。
