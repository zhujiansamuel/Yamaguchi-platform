# LegalPersonOffline 模型时区处理修改说明

## 修改目标

确保 `LegalPersonOffline` 模型的 `create_with_inventory` 方法中，所有传入的日期在不显式指定时区的情况下，都作为东京时间（JST/UTC+9）处理。

## 修改内容

### 修改 `create_with_inventory` 方法

**修改位置：** 第 576-587 行

在创建 LegalPersonOffline 实例前，添加时区转换逻辑：

```python
# Apply Tokyo timezone to datetime fields in fields
datetime_fields = ['appointment_time', 'visit_time']
for field in datetime_fields:
    if field in fields and fields[field] is not None:
        fields[field] = ensure_tokyo_timezone(fields[field])

# Apply Tokyo timezone to inventory_times
inventory_time_fields = ['transaction_confirmed_at', 'scheduled_arrival_at', 
                       'checked_arrival_at_1', 'checked_arrival_at_2', 'actual_arrival_at']
for field in inventory_time_fields:
    if field in inventory_times and inventory_times[field] is not None:
        inventory_times[field] = ensure_tokyo_timezone(inventory_times[field])
```

**影响的字段：**

**LegalPersonOffline 实例字段：**
- `appointment_time` - 预约时间
- `visit_time` - 实际到店时间

**Inventory 实例字段（通过 inventory_times 参数传递）：**
- `transaction_confirmed_at` - 交易确认时间
- `scheduled_arrival_at` - 计划到达时间
- `checked_arrival_at_1` - 第一次检查到达时间
- `checked_arrival_at_2` - 第二次检查到达时间
- `actual_arrival_at` - 实际到达时间

## 使用示例

### 示例 1: 使用字符串日期时间

```python
from django.utils import timezone

legal_person, inventories, skipped = LegalPersonOffline.create_with_inventory(
    inventory_data=[
        ('4547597992388', '123456789012345'),
        ('4547597992395', '987654321098765'),
    ],
    username='customer123',
    appointment_time='2025-01-20 14:00:00',  # 将被解释为 2025-01-20 14:00:00+09:00
    visit_time='2025-01-20 15:30:00',        # 将被解释为 2025-01-20 15:30:00+09:00
    inventory_times={
        'transaction_confirmed_at': '2025-01-20 15:45:00',  # 将被解释为东京时间
        'scheduled_arrival_at': '2025-01-27 10:00:00'       # 将被解释为东京时间
    },
    skip_on_error=True
)
```

### 示例 2: 使用 date 对象

```python
from datetime import date, datetime

legal_person, inventories, skipped = LegalPersonOffline.create_with_inventory(
    inventory_data=[
        ('4547597992388', '123456789012345'),
    ],
    username='customer123',
    appointment_time=datetime(2025, 1, 20, 14, 0),  # 将被解释为 2025-01-20 14:00:00+09:00
    visit_time=datetime(2025, 1, 20, 15, 30),       # 将被解释为 2025-01-20 15:30:00+09:00
    inventory_times={
        'transaction_confirmed_at': datetime(2025, 1, 20, 15, 45),
        'scheduled_arrival_at': date(2025, 1, 27)  # 将被转换为 2025-01-27 00:00:00+09:00
    }
)
```

### 示例 3: 已有时区的日期不受影响

```python
import pytz
from datetime import datetime

utc_time = pytz.UTC.localize(datetime(2025, 1, 20, 5, 0))  # UTC 时间

legal_person, inventories, skipped = LegalPersonOffline.create_with_inventory(
    inventory_data=[
        ('4547597992388', '123456789012345'),
    ],
    username='customer123',
    appointment_time=utc_time,  # 保持为 UTC 时间，不会被转换
    visit_time=utc_time
)
```

## 工具函数

此修改复用了 `ensure_tokyo_timezone()` 函数（已在 Purchasing 模型修改中添加），该函数支持：
- ✅ 无时区的 datetime 对象 → 解释为东京时间
- ✅ date 对象 → 转换为当天午夜的东京时间
- ✅ 字符串格式的日期/时间 → 解析并解释为东京时间
- ✅ 已有时区的 datetime → 保持不变（向后兼容）
- ✅ None 值 → 保持不变

## 与 Purchasing 模型的一致性

此修改与 Purchasing 模型的时区处理保持一致：
- 使用相同的 `ensure_tokyo_timezone()` 工具函数
- 采用相同的处理逻辑
- 保持相同的向后兼容性

## 测试建议

建议测试以下场景：
1. 传入字符串格式的日期时间
2. 传入 datetime 对象（无时区）
3. 传入 date 对象
4. 传入已有时区的 datetime 对象
5. 传入 None 值
6. 通过 inventory_times 参数传递各种格式的时间

## 兼容性说明

1. **向后兼容：** 已有时区信息的日期不会被修改，保持原有行为
2. **数据库兼容：** Django 的 DateTimeField 支持时区感知的 datetime 对象
3. **依赖要求：** 需要 `pytz` 包（已在环境中安装）

## 注意事项

1. 此修改仅影响 `LegalPersonOffline` 模型的 `create_with_inventory` 方法
2. `actual_arrival_at` 字段在方法内部使用 `timezone.now()` 自动设置，已经是时区感知的
3. 如果从 Excel 导入日期数据，建议在读取时就应用此转换
4. 数据库中存储的是带时区的 datetime，查询时需注意时区转换

## 相关文件

- 修改文件：`apps/data_aggregation/models.py`
- 修改说明：`LEGALPERSONOFFLINE_TIMEZONE_CHANGES.md`（本文件）
- 相关修改：`TIMEZONE_CHANGES.md`（Purchasing 模型的时区处理修改）
