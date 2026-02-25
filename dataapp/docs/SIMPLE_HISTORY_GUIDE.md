# Django Simple History 集成指南

本文档介绍项目中 `django-simple-history` 的集成方式和使用方法。

## 目录

1. [概述](#概述)
2. [架构设计](#架构设计)
3. [change_source 字段](#change_source-字段)
4. [在代码中设置来源](#在代码中设置来源)
5. [Admin 集成](#admin-集成)
6. [查询历史记录](#查询历史记录)
7. [添加新的来源类型](#添加新的来源类型)
8. [最佳实践](#最佳实践)

---

## 概述

项目使用 `django-simple-history` 库为所有模型提供历史追踪功能。每当模型实例被创建、更新或删除时，系统会自动记录一条历史记录。

### 特殊功能

- **change_source 字段**：记录每次修改的来源（Admin、API、Celery 等）
- **自动填充**：通过信号机制自动填充 change_source
- **上下文传递**：使用 `contextvars` 在调用栈中传递来源信息

---

## 架构设计

### 核心模块

```
apps/core/
├── __init__.py
├── apps.py           # App 配置，注册信号
├── history.py        # ChangeSource 枚举、contextvars、信号处理
└── admin.py          # BaseHistoryAdmin 基类
```

### 关键组件

| 组件 | 文件 | 说明 |
|------|------|------|
| `ChangeSource` | `apps/core/history.py` | 来源枚举定义 |
| `HistoricalRecordsWithSource` | `apps/core/history.py` | 包含 change_source 的历史记录类 |
| `set_change_source()` | `apps/core/history.py` | 设置当前来源 |
| `get_change_source()` | `apps/core/history.py` | 获取当前来源 |
| `ChangeSourceContext` | `apps/core/history.py` | 上下文管理器 |
| `BaseHistoryAdmin` | `apps/core/admin.py` | Admin 基类 |

---

## change_source 字段

### 可用的来源类型

```python
from apps.core.history import ChangeSource

class ChangeSource(models.TextChoices):
    ADMIN = 'admin', 'Admin 管理后台'
    API = 'api', 'REST API'
    CELERY = 'celery', 'Celery 异步任务'
    SYNC = 'sync', 'Nextcloud 同步'
    SHELL = 'shell', 'Django Shell/脚本'
    UNKNOWN = 'unknown', '未知来源'
```

### 历史表结构

每个模型的历史表（如 `historical_purchasing`）包含以下额外字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| `change_source` | CharField(20) | 修改来源 |
| `history_id` | BigAutoField | 历史记录主键 |
| `history_date` | DateTimeField | 修改时间 |
| `history_change_reason` | CharField(100) | 修改原因（可选） |
| `history_type` | CharField(1) | 操作类型：+创建/-删除/~更新 |
| `history_user` | ForeignKey(User) | 修改用户（如有） |

---

## 在代码中设置来源

### 方法 1：使用上下文管理器（推荐）

```python
from apps.core.history import ChangeSourceContext, ChangeSource

# 在 API 视图中
def create_order(request):
    with ChangeSourceContext(ChangeSource.API):
        order = Purchasing.objects.create(
            order_number='ORD-001',
            delivery_status='pending_confirmation'
        )
    return order
```

### 方法 2：手动设置和重置

```python
from apps.core.history import set_change_source, reset_change_source, ChangeSource

def process_in_celery_task():
    token = set_change_source(ChangeSource.CELERY)
    try:
        # 执行数据库操作
        purchasing.delivery_status = 'shipped'
        purchasing.save()
    finally:
        reset_change_source(token)
```

### 方法 3：在 Celery 任务中

```python
from celery import shared_task
from apps.core.history import ChangeSourceContext, ChangeSource

@shared_task
def sync_purchasing_data():
    with ChangeSourceContext(ChangeSource.CELERY):
        # 所有在此上下文中的数据库操作都会记录为 CELERY 来源
        for item in data:
            Purchasing.objects.update_or_create(...)
```

### 方法 4：在 Nextcloud 同步中

```python
from apps.core.history import ChangeSourceContext, ChangeSource

def handle_nextcloud_webhook(file_path, data):
    with ChangeSourceContext(ChangeSource.SYNC):
        # 处理同步数据
        process_excel_data(data)
```

---

## Admin 集成

### 自动设置来源

所有继承 `BaseHistoryAdmin` 的 Admin 类会自动将 `change_source` 设置为 `ADMIN`：

```python
from apps.core.admin import BaseHistoryAdmin

@admin.register(Purchasing)
class PurchasingAdmin(BaseHistoryAdmin):
    list_display = ['order_number', 'delivery_status', 'created_at']
    # ... 其他配置
```

### 查看历史记录

在 Admin 详情页面中，点击 "History" 按钮可查看该记录的所有历史变更。

### 已集成的模型

**data_aggregation 应用**:
- AggregationSource, AggregatedData, AggregationTask
- iPhone, iPad, Inventory, TemporaryChannel
- LegalPersonOffline, EcSite, OfficialAccount, Purchasing
- GiftCard, GiftCardPayment
- DebitCard, DebitCardPayment
- CreditCard, CreditCardPayment
- OtherPayment, HistoricalData

**data_acquisition 应用**:
- DataSource, AcquiredData, AcquisitionTask
- NextcloudSyncState, SyncConflict, SyncLog

---

## 查询历史记录

### 获取对象的历史

```python
purchasing = Purchasing.objects.get(order_number='ORD-001')

# 获取所有历史记录
for record in purchasing.history.all():
    print(f"{record.history_date}: {record.history_type} by {record.change_source}")

# 获取最新的历史记录
latest = purchasing.history.most_recent()
print(f"Last modified from: {latest.change_source}")
```

### 按来源筛选历史

```python
from apps.core.history import ChangeSource

# 获取所有来自 Admin 的修改
admin_changes = Purchasing.history.filter(change_source=ChangeSource.ADMIN)

# 获取所有来自 API 的修改
api_changes = Purchasing.history.filter(change_source=ChangeSource.API)

# 获取特定时间范围内的修改
from django.utils import timezone
from datetime import timedelta

yesterday = timezone.now() - timedelta(days=1)
recent_changes = Purchasing.history.filter(history_date__gte=yesterday)
```

### 比较版本差异

```python
purchasing = Purchasing.objects.get(order_number='ORD-001')
history = purchasing.history.all()

if history.count() >= 2:
    new_record = history[0]
    old_record = history[1]

    delta = new_record.diff_against(old_record)
    for change in delta.changes:
        print(f"{change.field}: {change.old} -> {change.new}")
```

### 恢复到历史版本

```python
# 获取特定时间点的版本
historical_purchasing = purchasing.history.as_of(some_datetime)

# 恢复到该版本
historical_purchasing.instance.save()
```

---

## 添加新的来源类型

### 步骤 1：更新枚举

编辑 `apps/core/history.py`：

```python
class ChangeSource(models.TextChoices):
    ADMIN = 'admin', 'Admin 管理后台'
    API = 'api', 'REST API'
    CELERY = 'celery', 'Celery 异步任务'
    SYNC = 'sync', 'Nextcloud 同步'
    SHELL = 'shell', 'Django Shell/脚本'
    UNKNOWN = 'unknown', '未知来源'
    # 新增来源
    IMPORT = 'import', '批量导入'
    WEBHOOK = 'webhook', 'Webhook 回调'
```

### 步骤 2：生成迁移

```bash
python manage.py makemigrations
python manage.py migrate
```

### 步骤 3：在代码中使用

```python
from apps.core.history import ChangeSourceContext, ChangeSource

def handle_bulk_import(file):
    with ChangeSourceContext(ChangeSource.IMPORT):
        # 批量导入操作
        pass
```

---

## 最佳实践

### 1. 始终使用上下文管理器

使用 `ChangeSourceContext` 确保来源正确设置和清理：

```python
# 推荐
with ChangeSourceContext(ChangeSource.API):
    obj.save()

# 不推荐（可能忘记重置）
set_change_source(ChangeSource.API)
obj.save()
# 忘记调用 reset_change_source()
```

### 2. 在入口点设置来源

在请求处理的入口点设置来源，而不是在每个函数中：

```python
# API View
class PurchasingViewSet(viewsets.ModelViewSet):
    def perform_create(self, serializer):
        with ChangeSourceContext(ChangeSource.API):
            serializer.save()
```

### 3. Celery 任务装饰器

创建装饰器简化 Celery 任务中的来源设置：

```python
from functools import wraps
from apps.core.history import ChangeSourceContext, ChangeSource

def celery_history_source(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        with ChangeSourceContext(ChangeSource.CELERY):
            return func(*args, **kwargs)
    return wrapper

@shared_task
@celery_history_source
def my_celery_task():
    # 自动设置为 CELERY 来源
    pass
```

### 4. 定期清理历史

对于高频更新的模型，考虑定期清理旧历史记录：

```python
from datetime import timedelta
from django.utils import timezone

# 删除超过 90 天的历史记录
cutoff = timezone.now() - timedelta(days=90)
Purchasing.history.filter(history_date__lt=cutoff).delete()
```

### 5. 排除不重要的字段

如果某些字段变化不需要记录，可以排除：

```python
class MyModel(models.Model):
    name = models.CharField(max_length=100)
    last_accessed = models.DateTimeField()  # 不需要追踪

    history = HistoricalRecordsWithSource(
        excluded_fields=['last_accessed']
    )
```

---

## 故障排除

### change_source 显示为 unknown

确保在执行数据库操作前设置了来源：

```python
# 错误：没有设置来源
obj.save()  # change_source 将为 unknown

# 正确
with ChangeSourceContext(ChangeSource.API):
    obj.save()
```

### Admin 中的 change_source 不是 admin

确保 Admin 类继承了 `BaseHistoryAdmin`：

```python
# 错误
class MyModelAdmin(admin.ModelAdmin):
    pass

# 正确
class MyModelAdmin(BaseHistoryAdmin):
    pass
```

### 历史记录没有用户信息

确保已添加 `HistoryRequestMiddleware`：

```python
# config/settings/base.py
MIDDLEWARE = [
    # ...
    'simple_history.middleware.HistoryRequestMiddleware',
]
```

---

## 相关链接

- [django-simple-history 官方文档](https://django-simple-history.readthedocs.io/)
- [源码位置](../apps/core/history.py)
