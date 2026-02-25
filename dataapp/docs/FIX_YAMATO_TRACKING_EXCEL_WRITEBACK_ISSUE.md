# 修复：Yamato Tracking Number 任务的 Excel Writeback 问题

## 问题描述

`run_yamato_tracking_10_tracking_number` 任务在完成时会错误地触发 Excel writeback，导致以下错误：

```
[ERROR] excel_writeback [Task ...] Batch writeback failed for ...: File is not a zip file
```

## 根本原因

### 1. 两个不同的 Yamato Tracking 系统

系统中有两个不同的 Yamato tracking 任务：

#### yamato_tracking_10（原有系统）
- **数据来源**：Excel 文件（从 Nextcloud 上传）
- **触发方式**：文件上传自动触发
- **Worker**：`celery_worker_yamato_tracking_10`
- **队列**：`yamato_tracking_10_queue`
- **file_path**：有实际文件路径（如：`/path/to/file.xlsx`）
- **结果处理**：查询完成后，将状态码写回原 Excel 文件的 C 列
- **需要 excel_writeback**：✅ 是

#### yamato_tracking_10_tracking_number（新系统）
- **数据来源**：Purchasing 数据库模型
- **触发方式**：手动命令触发（`python manage.py run_yamato_tracking_10_tracking_number`）
- **Worker**：`celery_worker_yamato_tracking_10_tracking_number`
- **队列**：`yamato_tracking_10_tracking_number_queue`
- **Redis DB**：DB 8（完全隔离）
- **file_path**：空字符串 `''`（任务不基于文件）
- **结果处理**：查询完成后，直接更新 Purchasing 模型字段：
  - `latest_delivery_status`
  - `delivery_status_query_time`
  - `delivery_status_query_source`
  - `last_info_updated_at`
- **需要 excel_writeback**：❌ 否

### 2. 问题触发流程

1. `process_yamato_tracking_10_tracking_number` 创建 `TrackingBatch`，设置 `file_path=''`
   ```python
   # apps/data_acquisition/tasks.py:2158
   tracking_batch = TrackingBatch.objects.create(
       batch_uuid=batch_uuid,
       task_name='yamato_tracking_10_tracking_number',
       file_path='',  # 该任务不基于文件
       ...
   )
   ```

2. 任务完成后调用 `tracking_batch.update_progress()`

3. `update_progress()` 检测到批次完成，**无条件触发** `batch_writeback_tracking_data`
   ```python
   # apps/data_acquisition/models.py:622-634（修复前）
   if crossed_milestone or batch_just_completed:
       # 没有检查 file_path 是否为空！
       batch_writeback_tracking_data.apply_async(...)
   ```

4. `batch_writeback_to_excel` 尝试用空 `file_path` 构建 WebDAV URL
   ```python
   # apps/data_acquisition/excel_writeback.py:254-290
   file_path = batch.file_path  # ''
   webdav_url = base_url + '/' + file_path.lstrip('/')  # 结果：base_url + '/'
   ```

5. 下载到错误内容（不是 Excel 文件），导致 `BadZipFile: File is not a zip file`

## 解决方案

### 修改位置

`apps/data_acquisition/models.py` 的 `TrackingBatch.update_progress()` 方法

### 修改内容

在触发 Excel writeback 之前，检查 `file_path` 是否为空：

```python
if crossed_milestone or batch_just_completed:
    trigger_reason = "milestone_10" if crossed_milestone else "batch_completed"

    # 只有当 file_path 不为空时才触发 Excel 回写
    # yamato_tracking_10_tracking_number 等直接更新数据库的任务不需要 Excel 回写
    if self.file_path and self.file_path.strip():
        logger.info(
            f"Batch {self.batch_uuid}: triggering writeback at {new_completed} completed "
            f"(reason: {trigger_reason}, old: {old_completed}, file: {self.file_path})"
        )

        # 异步触发批量回写任务
        from .tasks import batch_writeback_tracking_data
        batch_writeback_tracking_data.apply_async(
            args=[str(self.batch_uuid)],
            countdown=5
        )

        if batch_just_completed:
            self.writeback_triggered = True
            self.save(update_fields=['writeback_triggered'])
    else:
        logger.info(
            f"Batch {self.batch_uuid}: skipping writeback at {new_completed} completed "
            f"(reason: {trigger_reason}, no file_path, task handles data directly)"
        )
```

### 修改原理

- **条件检查**：`if self.file_path and self.file_path.strip()`
  - 只有当 `file_path` 不为空且不是纯空白字符时，才触发 Excel writeback
  - 对于 `file_path=''` 的任务，跳过 writeback 并记录日志

- **向后兼容**：
  - ✅ 不影响现有基于 Excel 的任务（如 `yamato_tracking_10`）
  - ✅ 修复直接更新数据库的任务（如 `yamato_tracking_10_tracking_number`）

## 验证方法

### 1. 运行 tracking_number 任务

```bash
python manage.py run_yamato_tracking_10_tracking_number
```

### 2. 查看日志

应该看到：
```
[INFO] Batch {uuid}: skipping writeback at 1 completed (reason: batch_completed, no file_path, task handles data directly)
```

而不是：
```
[ERROR] excel_writeback Batch writeback failed: File is not a zip file
```

### 3. 验证数据更新

检查 Purchasing 模型的记录是否正确更新：
- `latest_delivery_status`
- `delivery_status_query_time`
- `delivery_status_query_source = 'process_yamato_tracking_10_tracking_number'`

## 相关文件

- `apps/data_acquisition/models.py` - TrackingBatch 模型（修复位置）
- `apps/data_acquisition/tasks.py` - 任务实现
- `apps/data_acquisition/excel_writeback.py` - Excel 回写逻辑
- `apps/data_acquisition/workers/celery_worker_yamato_tracking_10_tracking_number.py` - Worker 配置
- `apps/data_acquisition/workers/README_yamato_tracking_10_tracking_number.md` - 文档

## 设计建议

### 未来可以考虑的改进

1. **显式标志**：在 `TrackingBatch` 模型中添加 `needs_excel_writeback` 布尔字段
   ```python
   needs_excel_writeback = models.BooleanField(
       default=True,
       help_text='Whether this batch needs to write back to Excel file'
   )
   ```

2. **任务类型枚举**：明确区分不同类型的任务
   ```python
   TASK_TYPE_CHOICES = [
       ('excel_based', 'Excel-based tracking'),
       ('database_based', 'Database-based tracking'),
   ]
   ```

3. **抽象基类**：为不同类型的 tracking 任务创建不同的基类

但目前的修复已经足够解决问题，且不会影响现有功能。

## 总结

| 任务类型 | file_path | Excel Writeback | 结果处理 |
|---------|-----------|----------------|---------|
| yamato_tracking_10 | 有实际路径 | ✅ 触发 | 写回 Excel |
| yamato_tracking_10_tracking_number | 空字符串 | ❌ 跳过 | 更新数据库 |

**修复核心**：在触发 Excel writeback 前检查 `file_path` 是否有效，避免对不需要 Excel 回写的任务进行错误操作。
