# Excel 回写功能说明

## 概述

WebScraper 追踪数据在落库的同时，会自动回写到原始 Excel 文件中，让用户可以直接在 Excel 中查看追踪结果。

## 回写策略

系统提供两种回写策略：

### 1. 批量回写（推荐）

**默认启用**，整个 TrackingBatch 完成后一次性写入所有数据。

**优点：**
- ✅ 避免并发写入冲突
- ✅ 性能更好（只需下载/上传一次 Excel）
- ✅ 不会出现文件锁定错误

**缺点：**
- ⏰ 需要等待整个 batch 完成才能看到结果

**工作流程：**
1. WebScraper 任务逐个完成，数据落库
2. 当最后一个任务完成时，自动触发批量回写任务
3. 批量回写任务下载 Excel，写入所有数据，上传回 Nextcloud

### 2. 即时回写

每个任务完成后立即回写，实时性好。

**优点：**
- ⚡ 实时性好，用户可以立即看到结果

**缺点：**
- ⚠️ 可能出现并发写入冲突（文件锁定错误）
- ⚠️ 性能较差（每个任务都要下载/上传 Excel）

**启用方法：**

在 `config/settings/base.py` 中添加：

```python
# Excel 回写配置
TRACKING_IMMEDIATE_WRITEBACK = True  # 启用即时回写
```

**重试机制：**

即时回写内置了重试机制（默认 3 次，指数退避），遇到文件锁定时会自动重试。

## 回写数据格式

系统自动识别数据类型，提取相应字段：

### Japan Post Tracking 数据

提取"配送履歴"不为空的**最后一行**的以下字段：
- 状態発生日
- 配送履歴
- 詳細1
- 取扱局
- 県名等

### Yamato Tracking 数据

提取"data2"不为空的**最后一行**的以下字段：
- data2
- data3
- name

所有字段使用 `｜｜｜` 分隔，写入 Excel 的 **C 列**（同一行）。

**示例：**
```
配送済み｜｜｜2026年1月11日｜｜｜ご不在のため持ち戻り｜｜｜千代田局｜｜｜東京都
```

## 回写位置

- **列**：C 列（第 3 列）
- **行**：根据 TrackingJob 的 `index` 字段定位（`index + 2`，因为第 1 行是表头）
- **写入方式**：覆盖写入，忽略 C 列已有内容

## 监控和日志

### SyncLog 记录

所有回写操作都会记录到 `SyncLog` 表：

```python
operation_type='excel_writeback'
success=True/False
details={
    'batch_uuid': '...',
    'total_jobs': 100,
    'written': 98,
    'row_indices': [0, 1, 2, ...]
}
```

### TrackingBatch 状态

TrackingBatch 模型新增字段：

```python
writeback_triggered = models.BooleanField()       # 是否已触发回写
writeback_completed_at = models.DateTimeField()   # 回写完成时间
```

## 故障排查

### 文件锁定错误

**错误信息：**
```
"/path/to/file.xlsx" is locked, existing lock on file: 3 shared locks
```

**原因：**
- 用户正在 OnlyOffice 中编辑文件
- 多个任务并发写入同一文件
- 文件被其他进程锁定

**解决方案：**

1. **使用批量回写（推荐）**
   ```python
   # 在 settings 中确保未设置或设置为 False
   TRACKING_IMMEDIATE_WRITEBACK = False
   ```

2. **如果使用即时回写，增加重试次数**

   修改 `apps/data_acquisition/tasks.py`：
   ```python
   writeback_success = writeback_to_excel(
       file_path=file_path,
       row_index=row_index,
       writeback_data=writeback_data,
       task_id=task_id,
       max_retries=5,        # 增加到 5 次
       retry_delay=3.0       # 增加延迟到 3 秒
   )
   ```

3. **手动触发批量回写**

   如果批量回写失败，可以手动触发：
   ```python
   from apps.data_acquisition.tasks import batch_writeback_tracking_data

   batch_writeback_tracking_data.apply_async(
       args=['batch-uuid-here']
   )
   ```

### 回写失败但数据已落库

回写失败**不影响**数据落库，数据仍然会正确保存到数据库。

可以通过以下方式查看数据：
1. Django Admin 查看 Purchasing 记录
2. 数据库直接查询
3. 手动触发批量回写补救

## 数据库迁移

添加新字段后，需要运行迁移：

```bash
python manage.py migrate data_acquisition
```

迁移文件：`0009_add_writeback_fields_to_trackingbatch.py`

## 测试

### 测试批量回写

```python
from apps.data_acquisition.excel_writeback import batch_writeback_to_excel

result = batch_writeback_to_excel(
    batch_uuid='your-batch-uuid',
    task_id='test-task'
)

print(result)
# {'status': 'success', 'total_jobs': 10, 'written': 10}
```

### 测试即时回写

```python
from apps.data_acquisition.excel_writeback import writeback_to_excel

success = writeback_to_excel(
    file_path='/official_website_redirect_to_yamato_tracking/OWRYT-20260112-1135.xlsx',
    row_index=0,
    writeback_data='配送済み｜｜｜2026年1月11日｜｜｜...',
    task_id='test-task'
)
```

## 配置建议

### 生产环境（推荐）

```python
# config/settings/production.py
TRACKING_IMMEDIATE_WRITEBACK = False  # 使用批量回写
```

### 开发/测试环境

```python
# config/settings/local.py
TRACKING_IMMEDIATE_WRITEBACK = True   # 使用即时回写，便于测试
```

## API 参考

### `extract_writeback_data(df)`

从 DataFrame 提取回写数据。

**参数：**
- `df` (DataFrame): WebScraper 返回的数据

**返回：**
- `str`: 用 `｜｜｜` 分隔的字符串，如果无法提取则返回空字符串

### `writeback_to_excel(file_path, row_index, writeback_data, task_id, max_retries, retry_delay)`

单个任务回写。

**参数：**
- `file_path` (str): Nextcloud 文件路径
- `row_index` (int): Excel 行索引（从 0 开始）
- `writeback_data` (str): 要写入的数据
- `task_id` (str): Celery 任务 ID
- `max_retries` (int): 最大重试次数，默认 3
- `retry_delay` (float): 重试延迟（秒），默认 2.0

**返回：**
- `bool`: 是否成功

### `batch_writeback_to_excel(batch_uuid, task_id)`

批量回写。

**参数：**
- `batch_uuid` (str): TrackingBatch 的 UUID
- `task_id` (str): Celery 任务 ID

**返回：**
- `dict`: 回写结果统计
