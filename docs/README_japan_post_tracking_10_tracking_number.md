# Japan Post Tracking 10 Tracking Number Worker

## 概述

该Worker从Purchasing模型查询符合条件的记录，构造Japan Post追踪URL，并发布爬取任务到WebScraper API。

## 配置信息

- **Worker名称**: `japan_post_tracking_10_tracking_number_worker`
- **队列名称**: `japan_post_tracking_10_tracking_number_queue`
- **Redis DB**: 6
- **并发数**: 1（单线程）
- **超时时间**: 2分钟（硬超时120秒，软超时110秒）
- **Celery App**: `celery_japan_post_tracking_10_tracking_number`

## 选取条件

从Purchasing模型查询符合以下条件的记录（最多10条）：

1. `order_number` 以 'w' 开头（不区分大小写）
2. `tracking_number` 正则提取全部数字后，以 '1' 开头（位数不定）
3. `latest_delivery_status` 不等于 '配達完了'

## 工作流程

### 1. 查询记录
```python
# 查询符合条件的Purchasing记录
records = Purchasing.objects.filter(
    Q(order_number__istartswith='w'),
    ~Q(latest_delivery_status='配達完了')
).exclude(tracking_number__isnull=True).exclude(tracking_number='')
```

### 2. 提取追踪号
```python
# 从tracking_number中提取数字
digits = re.sub(r'\D', '', record.tracking_number)

# 筛选以'1'开头的追踪号
if digits and digits.startswith('1'):
    valid_records.append(record)
```

### 3. 构造URL
```python
# 每10个追踪号构造一个URL
base_url = 'https://trackings.post.japanpost.jp/services/srv/search'
params = {
    'requestNo1': tracking_number_1,
    'requestNo2': tracking_number_2,
    # ... up to requestNo10
    'search.x': random.randint(1, 173),
    'search.y': random.randint(1, 45),
    'startingUrlPatten': '',
    'locale': 'ja'
}
```

### 4. 创建批次记录
```python
# 创建TrackingBatch
batch = TrackingBatch.objects.create(
    file_path=f'purchasing_query_{batch_short}',
    task_name='japan_post_tracking_10',
    batch_uuid=uuid.uuid4(),
    total_jobs=1,
    status='pending'
)
```

### 5. 发布任务
```python
# 调用publish_tracking_batch发布到WebScraper API
publish_tracking_batch.apply_async(
    args=[task_name, url, batch_uuid_str, custom_id, index],
    countdown=0
)
```

## 启动Worker

### 方式1：直接启动
```bash
celery -A apps.data_acquisition.workers.celery_japan_post_tracking_10_tracking_number worker \
    -Q japan_post_tracking_10_tracking_number_queue -c 1 --loglevel=info
```

### 方式2：Docker Compose
```bash
docker-compose up -d celery_worker_japan_post_tracking_10_tracking_number
```

## 手动触发任务

### 使用Django管理命令
```bash
# 触发1个任务
python manage.py run_japan_post_tracking_10_tracking_number

# 触发多个任务
python manage.py run_japan_post_tracking_10_tracking_number --count 3
```

### 使用Python代码
```python
from apps.data_acquisition.workers.tasks_japan_post_tracking_10_tracking_number import process_record

# 触发任务
result = process_record.delay()
print(f"Task ID: {result.id}")
```

## 环境变量

在 `.env` 文件中添加：

```env
# Redis配置
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB_JAPAN_POST_TRACKING_10_TRACKING_NUMBER=6

# WebScraper API配置
WEB_SCRAPER_API_TOKEN=your_api_token
WEB_SCRAPER_SITEMAP_IDS={"japan_post_tracking_10": 1424233}
```

## 日志记录

### SyncLog记录
任务执行完成后会创建SyncLog记录：

```python
SyncLog.objects.create(
    operation_type='japan_post_tracking_10_tracking_number_completed',
    message='Published 1 tracking task with N tracking numbers',
    success=True,
    details={
        'batch_uuid': batch_uuid_str,
        'total_records': len(records),
        'tracking_numbers': tracking_numbers,
        'url': url,
        'custom_id': custom_id,
        'task_id': result['task_id']
    }
)
```

### 查看日志
```bash
# Worker日志
tail -f /var/log/celery/japan_post_tracking_10_tracking_number.log

# 或Docker日志
docker logs -f data-platform-celery-japan-post-tracking-10-tracking-number
```

## 监控

### 通过Flower监控
访问 Flower Web界面：
- URL: `http://your-server:5555`
- 查找Worker: `japan_post_tracking_10_tracking_number_worker`

### 通过Redis监控
```bash
# 连接到Redis DB 6
redis-cli -n 6

# 查看队列长度
LLEN japan_post_tracking_10_tracking_number_queue

# 查看所有键
KEYS *
```

### 通过Django Admin监控
1. 访问Django Admin
2. 查看SyncLog模型
3. 筛选 `operation_type = 'japan_post_tracking_10_tracking_number_completed'`

## 与原Worker 5的区别

| 特性 | 原Worker 5 (EstimatedDeliveryDateEmptyWorker) | 新Worker (JapanPostTracking10TrackingNumberWorker) |
|------|-----------------------------------------------|---------------------------------------------------|
| 数据来源 | 基于记录锁定机制逐个处理 | 批量查询Purchasing模型 |
| 选取条件 | 复杂的字段组合条件 | 简单的3个条件 |
| 处理方式 | Playwright浏览器自动化 | 发布WebScraper API任务 |
| 批次管理 | 无 | 创建TrackingBatch和TrackingJob |
| 超时时间 | 10分钟 | 2分钟 |
| 重试策略 | 最多3次 | 不重试 |

## 故障排查

### 问题1：找不到符合条件的记录
**原因**: Purchasing表中没有符合条件的记录

**解决方案**:
```python
# 手动查询验证
from apps.data_aggregation.models import Purchasing
from django.db.models import Q
import re

records = Purchasing.objects.filter(
    Q(order_number__istartswith='w'),
    ~Q(latest_delivery_status='配達完了')
).exclude(tracking_number__isnull=True).exclude(tracking_number='')

for record in records:
    digits = re.sub(r'\D', '', record.tracking_number)
    if digits and digits.startswith('1'):
        print(f"Found: {record.order_number} - {digits}")
```

### 问题2：任务发布失败
**原因**: WebScraper API配置错误或网络问题

**解决方案**:
1. 检查 `.env` 文件中的 `WEB_SCRAPER_API_TOKEN`
2. 检查 `WEB_SCRAPER_SITEMAP_IDS` 配置
3. 查看Worker日志获取详细错误信息

### 问题3：Worker无法启动
**原因**: Redis连接失败或配置错误

**解决方案**:
```bash
# 测试Redis连接
redis-cli -h $REDIS_HOST -p $REDIS_PORT -n 6 ping

# 检查环境变量
echo $REDIS_DB_JAPAN_POST_TRACKING_10_TRACKING_NUMBER
```

## 性能优化

### 调整最大记录数
修改 `japan_post_tracking_10_tracking_number.py`:
```python
MAX_RECORDS = 20  # 从10改为20
```

### 调整超时时间
修改 `celery_japan_post_tracking_10_tracking_number.py`:
```python
task_time_limit=5 * 60,  # 5分钟
task_soft_time_limit=4 * 60 + 50,  # 4分50秒
```

## 相关文件

- Worker主文件: `apps/data_acquisition/workers/japan_post_tracking_10_tracking_number.py`
- Celery配置: `apps/data_acquisition/workers/celery_japan_post_tracking_10_tracking_number.py`
- 任务定义: `apps/data_acquisition/workers/tasks_japan_post_tracking_10_tracking_number.py`
- 管理命令: `apps/data_acquisition/management/commands/run_japan_post_tracking_10_tracking_number.py`
- Docker配置: `docker-compose.yml`
- 启动脚本: `docker/entrypoint.sh`

## 注意事项

1. **不重试**: 任务失败后不会自动重试，仅记录日志
2. **单线程**: Worker以单线程运行，确保任务顺序执行
3. **批次隔离**: 每次执行创建独立的TrackingBatch，便于追踪
4. **URL限制**: 每个URL最多包含10个追踪号
5. **API频率**: 发布任务时会自动延迟2秒，避免API限流
