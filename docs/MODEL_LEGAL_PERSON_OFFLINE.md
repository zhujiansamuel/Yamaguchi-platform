# LegalPersonOffline 模型说明文档

## 概述

LegalPersonOffline（法人线下）模型用于表示客户到线下店铺进行产品采购的记录。每个记录代表一次线下访问和购买行为，可以关联多个库存项目。

**文件位置**: `apps/data_aggregation/models.py:286-460`

## 数据库表

- **表名**: `legal_person_offline`
- **历史记录**: 支持（使用 `HistoricalRecordsWithSource`）
- **软删除**: 支持（`is_deleted` 字段）

## 主要字段

### 标识字段
- **uuid** (CharField, 最大长度59, 唯一)
  - 48字符的全局唯一标识符
  - 由 `generate_uuid()` 函数自动生成
  - 格式: 12组4位十六进制字符，用连字符分隔
  - 示例: `1a2b-3c4d-5e6f-7a8b-9c0d-1e2f-3a4b-5c6d-7e8f-9a0b-1c2d-3e4f`

### 客户信息字段
- **username** (CharField, 最大长度50)
  - 客户用户名
  - 必填字段

### 时间跟踪字段
- **appointment_time** (DateTimeField, 可选)
  - 预约时间
  - 客户预约到店的时间

- **visit_time** (DateTimeField, 可选)
  - 实际访问时间
  - 客户实际到店的时间

- **order_created_at** (DateTimeField, 自动)
  - 订单创建时间
  - 记录创建时自动设置

- **updated_at** (DateTimeField, 自动)
  - 最后更新时间
  - 每次更新时自动更新

### 元数据字段
- **is_deleted** (BooleanField)
  - 软删除标记
  - 默认值: False

## 类方法

### create_with_inventory
```python
@classmethod
def create_with_inventory(cls, inventory_data, **fields):
    """
    创建 LegalPersonOffline 实例并自动创建关联的库存项目。

    Args:
        inventory_data (List[Tuple[str, str]]): (jan, imei) 元组列表
            - jan (str): JAN码，用于在iPhone或iPad模型中查找产品
            - imei (str): 设备的IMEI号码
        **fields: LegalPersonOffline 字段的关键字参数
            特殊键：
            - inventory_times (dict): 库存项目的可选时间字段
                示例: {
                    'transaction_confirmed_at': datetime,
                    'scheduled_arrival_at': datetime
                }
                这些字段将应用于所有创建的库存项目

    Returns:
        tuple: (legal_person_instance, inventory_list)
            - legal_person_instance: 创建的 LegalPersonOffline 实例
            - inventory_list: 创建的 Inventory 实例列表

    Raises:
        Exception: 如果任何数据库操作失败（事务将回滚）
    """
```

#### 功能说明
1. **事务处理**: 使用数据库事务确保数据一致性
2. **自动产品关联**: 通过 JAN 码自动查找并关联 iPhone 或 iPad 产品
3. **批量创建库存**: 一次性创建多个关联的库存项目
4. **自动生成标识**: 为每个库存项目生成唯一的 flag 标识
5. **状态设置**: 新创建的库存默认状态为 `arrived`

#### Flag 生成规则
- 格式: `LPO-{uuid_prefix}-{index:03d}`
- `uuid_prefix`: LegalPersonOffline UUID 的第一段（连字符前的部分）
- `index`: 库存项目的序号（从1开始，3位数字）
- 示例: `LPO-1a2b-001`, `LPO-1a2b-002`

#### 使用示例
```python
from django.utils import timezone
from apps.data_aggregation.models import LegalPersonOffline

# 创建法人线下订单并关联库存
legal_person, inventories = LegalPersonOffline.create_with_inventory(
    inventory_data=[
        ('4547597992388', '123456789012345'),  # iPhone JAN + IMEI
        ('4547597992395', '987654321098765'),  # iPhone JAN + IMEI
    ],
    username='customer123',
    appointment_time=timezone.now(),
    visit_time=timezone.now(),
    inventory_times={
        'transaction_confirmed_at': timezone.now(),
        'scheduled_arrival_at': timezone.now() + timezone.timedelta(days=7)
    }
)

print(f"创建了 {legal_person} 及 {len(inventories)} 个库存项目")
# 输出: 创建了 customer123 - 1a2b3c4d... (2024-01-15) 及 2 个库存项目
```

## 数据库索引

模型包含以下索引以优化查询性能：
- `uuid` 字段索引
- `username` 字段索引
- `order_created_at` 字段降序索引
- `visit_time` 字段索引

## 与其他模型的关系

### 一对多关系
- **LegalPersonOffline** → Inventory (一个法人线下订单可以有多个库存项目)
  - 反向关系名: `legal_person_inventories`
  - 通过 Inventory 模型的 `source3` 字段关联

## 业务逻辑说明

1. **唯一性约束**: 每个记录都有唯一的 UUID

2. **时间跟踪**:
   - `appointment_time`: 客户预约时间
   - `visit_time`: 实际到店时间
   - `order_created_at`: 订单记录创建时间

3. **库存关联**:
   - 作为库存的 `source3`（来源3）
   - 可以通过 `legal_person_inventories` 反向关系访问所有关联库存

4. **产品匹配逻辑**:
   - 优先在 iPhone 模型中查找（`is_deleted=False`）
   - 如果未找到，在 iPad 模型中查找（`is_deleted=False`）
   - 如果都未找到，创建不关联产品的库存项目

## 使用示例

### 基本创建
```python
from django.utils import timezone
from apps.data_aggregation.models import LegalPersonOffline

# 创建简单的法人线下记录（不关联库存）
legal_person = LegalPersonOffline.objects.create(
    username='customer456',
    appointment_time=timezone.now(),
    visit_time=timezone.now()
)
```

### 查询相关库存
```python
# 获取某个法人线下订单的所有库存
legal_person = LegalPersonOffline.objects.get(uuid='...')
inventories = legal_person.legal_person_inventories.all()

# 查询今天的所有法人线下订单
from datetime import date
today_orders = LegalPersonOffline.objects.filter(
    order_created_at__date=date.today()
)
```

### 使用 create_with_inventory
```python
# 场景：客户到店购买了3台iPhone
legal_person, inventories = LegalPersonOffline.create_with_inventory(
    inventory_data=[
        ('4547597992388', '111111111111111'),
        ('4547597992388', '222222222222222'),
        ('4547597992395', '333333333333333'),
    ],
    username='vip_customer',
    visit_time=timezone.now()
)

# 查看创建的库存
for inv in inventories:
    print(f"库存 {inv.flag}: {inv.product} - IMEI: {inv.imei}")
# 输出:
# 库存 LPO-1a2b-001: iPhone 15 Pro 256GB 钛金属 - IMEI: 111111111111111
# 库存 LPO-1a2b-002: iPhone 15 Pro 256GB 钛金属 - IMEI: 222222222222222
# 库存 LPO-1a2b-003: iPhone 15 Pro Max 512GB 黑色 - IMEI: 333333333333333
```

## 相关 API 端点

详见 `docs/API_LEGAL_PERSON_OFFLINE.md`

## 相关文档

- [Inventory 模型说明](MODEL_INVENTORY.md)
- [create_with_inventory 使用指南](CREATE_WITH_INVENTORY_GUIDE.md)

## 注意事项

1. **事务安全**: `create_with_inventory` 方法使用事务，确保要么全部成功，要么全部回滚

2. **JAN 码匹配**: 如果提供的 JAN 码在系统中不存在，库存将被创建但不会关联产品

3. **IMEI 唯一性**: 确保提供的 IMEI 在系统中唯一，否则会引发数据库错误

4. **软删除**: 删除记录时应设置 `is_deleted=True`，而不是物理删除

5. **UUID 自动生成**: UUID 在创建时自动生成，无需手动指定
