# Purchasing 模型时区处理修改说明

## 修改目标

确保 `Purchasing` 模型的 `update_fields` 和 `create_with_inventory` 方法中，所有传入的日期在不显式指定时区的情况下，都作为东京时间（JST/UTC+9）处理。

## 修改内容

### 1. 添加时区处理工具函数

在 `apps/data_aggregation/models.py` 文件开头添加了 `ensure_tokyo_timezone()` 函数：

**功能：**
- 将无时区信息的日期/时间值解释为东京时间
- 支持多种输入格式：
  - `datetime` 对象（有/无时区）
  - `date` 对象
  - 字符串格式的日期/时间
  - `None` 值
  - 列表（通过列表推导式处理）

**处理逻辑：**
- 如果输入已有时区信息，保持不变
- 如果输入无时区信息，添加东京时区（Asia/Tokyo）
- `date` 对象会被转换为当天午夜 00:00 的东京时间

### 2. 修改 `update_fields` 方法

**修改位置：** 第 1475-1481 行

在处理日期参数前，添加时区转换：

```python
# Apply Tokyo timezone to date fields
if estimated_website_arrival_date is not None:
    estimated_website_arrival_date = ensure_tokyo_timezone(estimated_website_arrival_date)
if estimated_website_arrival_date_2 is not None:
    estimated_website_arrival_date_2 = ensure_tokyo_timezone(estimated_website_arrival_date_2)
if estimated_delivery_date is not None:
    estimated_delivery_date = ensure_tokyo_timezone(estimated_delivery_date)
```

**修改位置：** 第 1512-1520 行

在通用字段更新循环中，为日期时间字段添加时区转换：

```python
# Update remaining fields directly
# Apply Tokyo timezone to datetime/date fields
datetime_fields = ['confirmed_at', 'shipped_at', 'delivery_status_query_time', 'last_info_updated_at']
for field, value in kwargs.items():
    if hasattr(self, field):
        # Apply timezone conversion for datetime/date fields
        if field in datetime_fields and value is not None:
            value = ensure_tokyo_timezone(value)
        setattr(self, field, value)
```

**影响的字段：**
- `estimated_website_arrival_date`
- `estimated_website_arrival_date_2`
- `estimated_delivery_date`
- `confirmed_at`
- `shipped_at`
- `delivery_status_query_time`
- `last_info_updated_at`

### 3. 修改 `create_with_inventory` 方法

**修改位置：** 第 1761-1768 行

在解析参数后立即处理 `estimated_website_arrival_date`：

```python
# Apply Tokyo timezone to estimated_website_arrival_date
if estimated_website_arrival_date is not None:
    if isinstance(estimated_website_arrival_date, list):
        # Process each date in the list
        estimated_website_arrival_date = [ensure_tokyo_timezone(d) for d in estimated_website_arrival_date]
    else:
        # Process single date
        estimated_website_arrival_date = ensure_tokyo_timezone(estimated_website_arrival_date)
```

**修改位置：** 第 1837-1843 行

在创建 Purchasing 实例前，为 `purchasing_data` 中的所有日期字段添加时区转换：

```python
# Apply Tokyo timezone to datetime/date fields in purchasing_data
datetime_fields = ['confirmed_at', 'shipped_at', 'estimated_website_arrival_date', 
                 'estimated_website_arrival_date_2', 'estimated_delivery_date',
                 'delivery_status_query_time', 'last_info_updated_at']
for field in datetime_fields:
    if field in purchasing_data and purchasing_data[field] is not None:
        purchasing_data[field] = ensure_tokyo_timezone(purchasing_data[field])
```

**影响的字段：**
- `estimated_website_arrival_date`（支持单个值或列表）
- `estimated_website_arrival_date_2`
- `estimated_delivery_date`
- `confirmed_at`
- `shipped_at`
- `delivery_status_query_time`
- `last_info_updated_at`

## 使用示例

### 示例 1: update_fields 使用字符串日期

```python
purchasing.update_fields(
    estimated_website_arrival_date='2025-01-20',  # 将被解释为 2025-01-20 00:00:00+09:00
    estimated_delivery_date='2025-01-25'          # 将被解释为 2025-01-25 00:00:00+09:00
)
```

### 示例 2: update_fields 使用 date 对象

```python
from datetime import date

purchasing.update_fields(
    estimated_website_arrival_date=date(2025, 1, 20),  # 将被转换为 2025-01-20 00:00:00+09:00
    shipped_at=date(2025, 1, 15)                       # 将被转换为 2025-01-15 00:00:00+09:00
)
```

### 示例 3: create_with_inventory 使用日期列表

```python
purchasing, inventories = Purchasing.create_with_inventory(
    email='user@example.com',
    iphone_type_names=['iPhone 15 Pro 256GB ブラック', 'iPhone 15 Pro Max 512GB ホワイト'],
    estimated_website_arrival_date=['2025-01-20', '2025-01-25']  # 每个日期都将被解释为东京时间
)
```

### 示例 4: 已有时区的日期不受影响

```python
from datetime import datetime
import pytz

utc_time = pytz.UTC.localize(datetime(2025, 1, 20, 1, 30))
purchasing.update_fields(
    confirmed_at=utc_time  # 保持为 UTC 时间，不会被转换
)
```

## 测试验证

已创建测试脚本 `test_timezone_conversion.py` 验证时区转换功能，测试覆盖：
- ✅ 无时区的 datetime 对象
- ✅ date 对象
- ✅ 字符串格式的日期
- ✅ 字符串格式的日期时间
- ✅ 已有时区的 datetime 对象（保持不变）
- ✅ None 值处理
- ✅ 日期列表处理

所有测试均通过。

## 兼容性说明

1. **向后兼容：** 已有时区信息的日期不会被修改，保持原有行为
2. **数据库兼容：** Django 的 DateTimeField 支持时区感知的 datetime 对象
3. **依赖要求：** 需要 `pytz` 包（已在环境中安装）

## 注意事项

1. 此修改仅影响 `Purchasing` 模型的两个方法
2. 其他模型如需类似功能，可复用 `ensure_tokyo_timezone()` 函数
3. 如果从 Excel 导入日期数据，建议在读取时就应用此转换
4. 数据库中存储的是带时区的 datetime，查询时需注意时区转换

## 相关文件

- 修改文件：`apps/data_aggregation/models.py`
- 测试脚本：`test_timezone_conversion.py`
- 修改说明：`TIMEZONE_CHANGES.md`（本文件）
