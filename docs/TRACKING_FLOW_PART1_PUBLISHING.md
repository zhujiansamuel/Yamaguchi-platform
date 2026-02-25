# 追踪任务流程 - Part 1: Excel 处理到 WebScraper 发布

本文档描述追踪任务的**前半部分流程**：从 Nextcloud 文件监控到 WebScraper API 发布完成。

**另请参阅**: [Part 2: Webhook 接收到数据库更新](./TRACKING_FLOW_PART2_WEBHOOK.md)

---

## 流程概览

```
Nextcloud 文件保存
    ↓
Nextcloud Webhook → Django View
    ↓
[Phase 1] Celery Task: 读取 Excel + 提取 URLs
    ↓
批量投递发布任务（每个间隔 2 秒）
    ↓
[Phase 1.5] Celery Task: 串行发布单个 URL
    ↓
调用 WebScraper API（睡眠 6 秒）
    ↓
WebScraper 开始执行爬虫
    ↓
>>> 流程继续到 Part 2 (Webhook 接收) >>>
```

---

## 支持的任务类型

### Excel 触发的任务（通过 Nextcloud 文件监控）

| 任务名称 | 文件夹关键词 | 文件前缀 | Sitemap ID | Custom ID 前缀 | URL 构造规则 |
|---------|------------|---------|-----------|---------------|------------|
| **official_website_redirect_to_yamato_tracking** | `official_website_redirect_to_yamato_tracking` | `OWRYT-` | 1421177 | `owryt` | 从 Excel 提取 |
| **official_website_tracking** | `official_website_tracking` | `OWT-` | 789 | `owt` | 从 Excel 提取 |
| **yamato_tracking_only** | `yamato_tracking_only` | `YTO-` | 1423671 | `yto` | 模板构造 |
| **japan_post_tracking_only** | `japan_post_tracking_only` | `JPTO-` | 1423655 | `jpto` | 模板构造 |
| **japan_post_tracking_10** ⭐ | `japan_post_tracking_10` | `JPT10-` | 1424233 | `jpt10` | 10 合 1 URL |

### 本地任务（不使用 WebScraper）

| 任务名称 | 文件夹关键词 | 文件前缀 | 处理方式 |
|---------|------------|---------|---------|
| **yamato_tracking_10** ⭐ | `yamato_tracking_10` | `YT10-` | 本地查询，5 小时超时 |

---

## 目录

- [阶段一：文件监控与任务触发](#阶段一文件监控与任务触发)
- [阶段二：Excel 处理与 URL 准备](#阶段二excel-处理与-url-准备)
- [阶段三：串行发布到 WebScraper](#阶段三串行发布到-webscraper)
- [配置说明](#配置说明)
- [监控与日志](#监控与日志)

---

## 阶段一：文件监控与任务触发

### 1.1 Nextcloud Webhook

**触发条件**: 用户在 Nextcloud 特定文件夹保存 Excel 文件

**文件路径匹配规则**:
- 路径必须包含任务关键词（如 `official_website_tracking`）
- 文件名必须以指定前缀开头（如 `OWT-`）

**示例**:
```
/official_website_tracking/OWT-20260116-001.xlsx  ✅ 匹配
/yamato_tracking_only/YTO-test.xlsx               ✅ 匹配
/japan_post_tracking_10/JPT10-batch1.xlsx        ✅ 匹配
/random/file.xlsx                                  ❌ 不匹配
```

### 1.2 Django View 接收

**文件**: `apps/data_acquisition/views.py`

**端点**: `POST /api/acquisition/onlyoffice/callback/`

**处理逻辑**:
```python
# 循环匹配所有追踪任务配置
for task_name, config in TRACKING_TASK_CONFIGS.items():
    if (path_keyword in file_path and 
        filename.startswith(filename_prefix)):
        matched_task = task_name
        break

# 根据任务类型投递到不同的 Celery 任务
if matched_task == 'japan_post_tracking_10':
    process_japan_post_tracking_10_excel.delay(file_path, url)
elif matched_task == 'yamato_tracking_10':
    process_yamato_tracking_10_excel.delay(file_path, url)
else:
    process_tracking_excel.delay(matched_task, file_path, url)
```

---

## 阶段二：Excel 处理与 URL 准备

### 2.1 Worker 配置

**Worker**: `celery_worker_tracking_phase1`

**队列**: `tracking_excel_queue`

**并发数**: 1（避免文件冲突）

**超时**: 2 小时

**任务**:
- `process_tracking_excel` - 通用追踪任务
- `process_japan_post_tracking_10_excel` - Japan Post 10 合 1

### 2.2 process_tracking_excel（通用任务）

**流程**:

1. **下载 Excel 文件**
   ```python
   if document_url:
       content = requests.get(document_url).content
   else:
       content = nextcloud_client.download(file_path)
   ```

2. **解析 Excel，提取 URL**
   
   URL 提取优先级：
   
   | 优先级 | 条件 | 提取方式 | 示例 |
   |--------|------|---------|------|
   | 1 | A 列有超链接 | 提取超链接 | `cell_a.hyperlink.target` |
   | 2 | A 列是 URL 文本 | 直接使用 | `https://example.com` |
   | 3 | A 列+B 列组合 | 构造 Apple Store URL | `order_id` + `email@example.com` |
   | 4 | A 列有追踪号 | 使用模板构造 | `{url_template}.format(tracking_number)` |

3. **创建 TrackingBatch**
   ```python
   batch, created = TrackingBatch.objects.get_or_create(
       file_path=file_path,
       task_name=task_name,
       defaults={
           'batch_uuid': uuid.uuid4(),
           'total_jobs': len(urls),
           'status': 'pending'
       }
   )
   ```

4. **批量投递发布任务**
   ```python
   for idx, url in enumerate(urls):
       custom_id = f"{prefix}-{batch_short}-{idx:04d}"
       
       # 检查是否已投递（断点续传）
       if TrackingJob.objects.filter(batch=batch, custom_id=custom_id).exists():
           continue
       
       # 投递到 publish_tracking_queue，间隔 2 秒
       publish_tracking_batch.apply_async(
           args=[task_name, url, batch_uuid_str, custom_id, idx],
           countdown=dispatched_count * 2
       )
   ```

5. **快速完成**
   - ✅ 不等待 API 调用
   - ✅ 几分钟内完成
   - ✅ Worker 不被长时间占用

### 2.3 process_japan_post_tracking_10_excel（10 合 1）

**特殊逻辑**:

1. **提取追踪号**（A 列，第 2 行开始）
   ```python
   cell_value = str(cell_a.value)
   digits_only = re.sub(r'\D', '', cell_value)  # 只提取数字
   
   if len(digits_only) != 12:
       logger.warning("Invalid tracking number, skipping")
       continue
   ```

2. **每 10 个追踪号构造 1 个 URL**
   ```python
   # 批次内去重
   for i in range(0, len(tracking_data), 10):
       batch_chunk = tracking_data[i:i+10]
       unique_chunk = deduplicate(batch_chunk)
       
       # 构造 URL 参数
       params = {}
       for j in range(1, 11):
           if j <= len(unique_chunk):
               params[f'requestNo{j}'] = unique_chunk[j-1]
           else:
               params[f'requestNo{j}'] = ''  # 留空
       
       # 随机数
       params['search.x'] = random.randint(1, 173)
       params['search.y'] = random.randint(1, 45)
       
       url = f"{base_url}?{urlencode(params)}"
   ```

3. **投递发布任务**
   - 每个 URL 间隔 2 秒
   - custom_id 格式: `jpt10-{batch_short}-{start_row}-{end_row}`

---

## 阶段三：串行发布到 WebScraper

### 3.1 Worker 配置

**Worker**: `celery_worker_publish_tracking_batch` ⭐ **新增**

**队列**: `publish_tracking_queue`

**并发数**: 1（串行处理）

**超时**: 1 分钟（快速失败）

**重试**: 0（不重试）

### 3.2 publish_tracking_batch（单 URL 处理）

**新架构设计**:
- ✅ 只处理单个 URL（而非批量）
- ✅ 串行执行，避免 API 并发冲突
- ✅ 完成后强制睡眠 6 秒
- ✅ 1 分钟超时，快速失败

**流程**:

1. **接收参数**
   ```python
   def publish_tracking_batch(task_name, url, batch_uuid_str, custom_id, index):
   ```

2. **查找 TrackingBatch**
   ```python
   batch = TrackingBatch.objects.get(batch_uuid=batch_uuid_str)
   ```

3. **检查是否已发布**（断点续传）
   ```python
   if TrackingJob.objects.filter(batch=batch, custom_id=custom_id).exists():
       return {'status': 'skipped', 'custom_id': custom_id}
   ```

4. **调用 WebScraper API**
   ```python
   payload = {
       "sitemap_id": config['sitemap_id'],
       "driver": "fulljs",
       "page_load_delay": 2000,
       "request_interval": 2000,
       "start_urls": [url],
       "custom_id": custom_id
   }
   
   response = requests.post(
       "https://api.webscraper.io/api/v1/scraping-job",
       json=payload,
       auth=(api_token, api_token),
       timeout=30
   )
   ```

5. **创建 TrackingJob**
   ```python
   TrackingJob.objects.create(
       batch=batch,
       job_id=response_data['id'],
       custom_id=custom_id,
       target_url=url,
       index=index,
       status='pending'
   )
   ```

6. **强制睡眠 6 秒**
   ```python
   time.sleep(6)  # API 频率限制
   ```

7. **返回结果**
   ```python
   return {
       'status': 'success',
       'custom_id': custom_id,
       'job_id': job_id
   }
   ```

### 3.3 发布速率

| 指标 | 值 | 说明 |
|------|---|------|
| **单个任务耗时** | ~6 秒 | API 调用 + 睡眠 |
| **每小时发布数** | ~600 个 | 3600 / 6 = 600 |
| **100 个 URL 耗时** | ~10 分钟 | 100 * 6 / 60 = 10 |

---

## 配置说明

### Worker 配置（docker/entrypoint.sh）

```bash
# Phase 1: Excel 处理
celery_worker_tracking_phase1)
    exec celery -A apps.data_acquisition.celery worker \
        --loglevel=info \
        --concurrency=1 \
        --queues=tracking_excel_queue \
        --hostname=tracking_phase1@%h \
        --max-tasks-per-child=1 \
        --time-limit=7200 \
        --soft-time-limit=7000
    ;;

# Phase 1.5: 串行发布
celery_worker_publish_tracking_batch)
    exec celery -A apps.data_acquisition.celery worker \
        --loglevel=info \
        --concurrency=1 \
        --queues=publish_tracking_queue \
        --hostname=publish_tracking@%h \
        --max-tasks-per-child=100 \
        --time-limit=60 \
        --soft-time-limit=55
    ;;
```

### 任务路由（apps/data_acquisition/celery.py）

```python
task_routes={
    # Phase 1: Excel 读取和准备
    'apps.data_acquisition.tasks.process_tracking_excel':
        {'queue': 'tracking_excel_queue'},
    'apps.data_acquisition.tasks.process_japan_post_tracking_10_excel':
        {'queue': 'tracking_excel_queue'},
    
    # Phase 1.5: 串行发布
    'apps.data_acquisition.tasks.publish_tracking_batch':
        {'queue': 'publish_tracking_queue'},
}
```

### 任务配置（apps/data_acquisition/tasks.py）

```python
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
    # ... 其他任务配置
}
```

---

## 监控与日志

### 关键日志

**Phase 1（Excel 处理）**:
```bash
# 查看 Excel 处理日志
docker-compose logs -f celery_worker_tracking_phase1

# 成功示例
[INFO] Extracted 150 URLs from /path/to/file.xlsx
[INFO] Dispatched 150 tasks, skipped 0
[INFO] Excel processing complete: total_urls=150, dispatched=150
```

**Phase 1.5（发布任务）**:
```bash
# 查看发布日志
docker-compose logs -f celery_worker_publish_tracking_batch

# 成功示例
[INFO] Publishing single URL: custom_id=jpt10-abc123-0001
[INFO] Successfully published: jpt10-abc123-0001 (job_id=12345)

# 跳过已发布
[INFO] URL already published, skipping: jpt10-abc123-0001

# 失败示例
[ERROR] WebScraper API error: 429 - Rate limit exceeded
[ERROR] Failed to publish jpt10-abc123-0002: timeout
```

### 性能指标

```bash
# 查看 Phase 1 平均处理时间
docker-compose logs celery_worker_tracking_phase1 | grep "Excel processing complete" | tail -20

# 查看 Phase 1.5 发布成功率
docker-compose logs celery_worker_publish_tracking_batch | grep -c "Successfully published"
docker-compose logs celery_worker_publish_tracking_batch | grep -c "Failed to publish"

# 计算成功率
success=$(docker-compose logs celery_worker_publish_tracking_batch | grep -c "Successfully published")
failed=$(docker-compose logs celery_worker_publish_tracking_batch | grep -c "Failed")
echo "Success rate: $(( success * 100 / (success + failed) ))%"
```

---

## 常见问题

### Q1: Phase 1 任务超时

**症状**: Excel 处理任务超过 2 小时

**原因**:
- Excel 文件过大（> 1000 行）
- 网络下载缓慢

**解决方案**:
```bash
# 增加超时时间（修改 docker/entrypoint.sh）
--time-limit=10800  # 改为 3 小时
```

### Q2: Phase 1.5 队列积压

**症状**: `publish_tracking_queue` 积压大量任务

**原因**:
- 发布速率不足（每小时 600 个）
- Worker 实例数不足

**解决方案**:
```bash
# 增加 worker 实例（保持并发=1）
docker-compose up -d --scale celery_worker_publish_tracking_batch=3

# 现在发布速率提升到 1800/小时
```

### Q3: API 调用失败率高

**症状**: 大量 "Failed to publish" 错误

**原因**:
- API Token 无效
- API 频率限制

**解决方案**:
```bash
# 检查 API Token
echo $WEB_SCRAPER_API_TOKEN

# 增加睡眠时间（修改 tasks.py）
time.sleep(10)  # 改为 10 秒
```

---

## 性能优化

### 优化前 vs 优化后

| 指标 | 优化前 | 优化后 | 改进 |
|------|--------|--------|------|
| **Phase 1 耗时** | 数小时 | < 5 分钟 | 🚀 95%+ |
| **Worker 占用时间** | 长时间阻塞 | 快速释放 | ✅ |
| **API 调用方式** | 批量串行 | 独立 worker 串行 | ✅ |
| **失败处理** | 整批失败 | 单个失败 | ✅ |
| **可扩展性** | 困难 | 容易 | ✅ |

---

## 下一步

**任务发布完成后，流程继续到**:
- [Part 2: Webhook 接收到数据库更新](./TRACKING_FLOW_PART2_WEBHOOK.md)

**相关文档**:
- [Worker 架构文档](./WORKER_ARCHITECTURE.md)
- [完整追踪流程（已废弃）](./COMPLETE_TRACKING_FLOW.md)
