# Inventory 模型说明文档

## 概述

Inventory（库存）模型用于跟踪产品库存，包括iPhone和iPad等电子产品。每个库存项目都有唯一的UUID标识，并关联到具体的产品和采购来源。

**文件位置**: `apps/data_aggregation/models.py:504-704`

## 数据库表

- **表名**: `inventory`
- **历史记录**: 支持（使用 `HistoricalRecordsWithSource`）
- **软删除**: 支持（`is_deleted` 字段）

## 主要字段

### 标识字段
- **uuid** (CharField, 最大长度59, 唯一)
  - 48字符的全局唯一标识符
  - 由 `generate_uuid()` 函数自动生成
  - 格式: 12组4位十六进制字符，用连字符分隔
  - 示例: `1a2b-3c4d-5e6f-7a8b-9c0d-1e2f-3a4b-5c6d-7e8f-9a0b-1c2d-3e4f`

- **flag** (CharField, 最大长度100, 可选)
  - 人类可读的标识符
  - 用于业务场景的快速识别

### 产品关联字段
- **iphone** (ForeignKey to iPhone, 可选)
  - 关联到 iPhone 产品
  - 反向关系名: `iphone_inventories`
  - 删除策略: SET_NULL

- **ipad** (ForeignKey to iPad, 可选)
  - 关联到 iPad 产品
  - 反向关系名: `ipad_inventories`
  - 删除策略: SET_NULL

- **imei** (CharField, 最大长度17, 唯一, 可选)
  - 国际移动设备识别码
  - 用于唯一标识移动设备

### 采购来源字段
- **source1** (ForeignKey to EcSite, 可选)
  - 来源1: 电商网站订单
  - 反向关系名: `ecsite_inventories`
  - 删除策略: PROTECT

- **source2** (ForeignKey to Purchasing, 可选)
  - 来源2: 采购订单
  - 反向关系名: `purchasing_inventories`
  - 删除策略: PROTECT

- **source3** (ForeignKey to LegalPersonOffline, 可选)
  - 来源3: 法人线下采购
  - 反向关系名: `legal_person_inventories`
  - 删除策略: PROTECT

- **source4** (ForeignKey to TemporaryChannel, 可选)
  - 来源4: 临时渠道
  - 反向关系名: `temporary_channel_inventories`
  - 删除策略: PROTECT

### 时间跟踪字段
- **transaction_confirmed_at** (DateTimeField, 可选)
  - 交易确认时间

- **scheduled_arrival_at** (DateTimeField, 可选)
  - 预计到达时间

- **checked_arrival_at_1** (DateTimeField, 可选)
  - 第一次检查到达时间

- **checked_arrival_at_2** (DateTimeField, 可选)
  - 第二次检查到达时间

- **actual_arrival_at** (DateTimeField, 可选)
  - 实际到达时间

### 状态字段
- **status** (CharField, 最大长度20)
  - 可选值:
    - `planned`: 计划中
    - `in_transit`: 到达中
    - `arrived`: 到达
    - `out_of_stock`: 出库
    - `abnormal`: 异常
  - 默认值: `planned`

### 元数据字段
- **created_at** (DateTimeField, 自动)
  - 记录创建时间

- **updated_at** (DateTimeField, 自动)
  - 最后更新时间

- **is_deleted** (BooleanField)
  - 软删除标记
  - 默认值: False

## 属性方法

### product
```python
@property
def product(self):
    """获取关联的产品（iPhone或iPad）"""
```
- **返回**: iPhone 或 iPad 实例，或 None
- **用途**: 方便获取关联的产品，无需判断是 iPhone 还是 iPad

### product_type
```python
@property
def product_type(self):
    """获取产品类型"""
```
- **返回**: 'iPhone' 或 'iPad' 字符串，或 None
- **用途**: 快速识别库存项目关联的产品类型

## 数据库索引

模型包含以下索引以优化查询性能：
- `uuid` 字段索引
- `status` 字段索引
- `created_at` 字段索引
- `actual_arrival_at` 字段降序索引

## 使用示例

### 创建库存项目
```python
from apps.data_aggregation.models import Inventory, iPhone
from django.utils import timezone

# 查找产品
iphone = iPhone.objects.get(jan='4547597992388')

# 创建库存
inventory = Inventory.objects.create(
    iphone=iphone,
    imei='123456789012345',
    status='planned',
    scheduled_arrival_at=timezone.now() + timezone.timedelta(days=7)
)
```

### 查询库存
```python
# 查询所有已到达的iPhone库存
arrived_iphones = Inventory.objects.filter(
    status='arrived',
    iphone__isnull=False
)

# 查询特定来源的库存
purchasing_inventory = Inventory.objects.filter(
    source2__isnull=False
)
```

### 使用属性方法
```python
inventory = Inventory.objects.first()

# 获取关联产品
product = inventory.product  # 返回 iPhone 或 iPad 实例

# 获取产品类型
product_type = inventory.product_type  # 返回 'iPhone' 或 'iPad'
```

## 与其他模型的关系

### 一对多关系
- **iPhone** → Inventory (一个iPhone型号可以有多个库存项目)
- **iPad** → Inventory (一个iPad型号可以有多个库存项目)
- **EcSite** → Inventory (一个电商订单可以有多个库存项目)
- **Purchasing** → Inventory (一个采购订单可以有多个库存项目)
- **LegalPersonOffline** → Inventory (一个法人线下订单可以有多个库存项目)
- **TemporaryChannel** → Inventory (一个临时渠道可以有多个库存项目)

## 业务逻辑说明

1. **唯一性约束**: 每个库存项目必须有唯一的 UUID 和 IMEI（如果提供）

2. **产品关联**: 库存项目可以关联到 iPhone 或 iPad，但同一时间只能关联一个产品

3. **多来源支持**: 支持四种不同的采购来源，灵活适应不同的业务场景

4. **状态流转**: 库存状态从 `planned` → `in_transit` → `arrived` → `out_of_stock`

5. **时间跟踪**: 详细记录库存的各个时间节点，用于物流追踪和分析

## 相关 API 端点

详见 `docs/API_INVENTORY.md`

## 注意事项

1. **IMEI 唯一性**: 如果提供 IMEI，必须确保在系统中唯一
2. **产品关联**: 只能关联 iPhone 或 iPad 中的一个，不能同时关联两者
3. **来源保护**: 采购来源使用 PROTECT 删除策略，防止误删关联数据
4. **软删除**: 使用 `is_deleted` 字段进行软删除，保留历史数据
