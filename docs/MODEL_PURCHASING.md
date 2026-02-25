# Purchasing 模型说明文档

## 概述

Purchasing（采购）模型用于跟踪采购订单和配送信息。支持与官方账号关联、多种支付方式、库存管理等功能。该模型是系统中最复杂的模型之一，提供了丰富的类方法和实例方法。

**文件位置**: `apps/data_aggregation/models.py:898-1786`

## 数据库表

- **表名**: `purchasing`
- **历史记录**: 支持（使用 `HistoricalRecordsWithSource`）
- **软删除**: 支持（`is_deleted` 字段）

## 主要字段

### 标识字段
- **uuid** (CharField, 最大长度59, 唯一)
  - 48字符的全局唯一标识符
  - 由 `generate_uuid()` 函数自动生成

- **order_number** (CharField, 最大长度50, 可选)
  - 订单号（允许为空或重复）
  - 如果不提供，`create_with_inventory` 会自动生成（基于 `_generate_order_number()`）
  - 通过常规 API 创建时不会自动生成（可为空）

### 账号关联字段
- **official_account** (ForeignKey to OfficialAccount, 可选)
  - 关联的官方账号
  - 反向关系名: `purchasing_orders`
  - 删除策略: PROTECT

- **batch_encoding** (CharField, 最大长度50, 可选)
  - 批次编码
  - 用于采购订单分组

- **batch_level_1** (CharField, 最大长度50, 可选)
  - 批次层级1标识

- **batch_level_2** (CharField, 最大长度50, 可选)
  - 批次层级2标识

- **batch_level_3** (CharField, 最大长度50, 可选)
  - 批次层级3标识

- **account_used** (CharField, 最大长度50, 可选)
  - 使用的账号（通常是 email）

- **payment_method** (TextField, 可选)
  - 支付方式
  - 用于存储未匹配的支付卡信息

- **creation_source** (CharField, 最大长度200, 可选)
  - 创建来源
  - 用于记录创建订单的调用来源（如 API、手工导入、自动同步）
  - `create_with_inventory` 未传入时会自动填充调用方信息

### 时间跟踪字段
- **created_at** (DateTimeField, 自动)
  - 创建时间

- **confirmed_at** (DateTimeField, 可选)
  - 订单确认时间

- **shipped_at** (DateTimeField, 可选)
  - 发货时间

- **last_info_updated_at** (DateTimeField, 可选)
  - 最后信息更新时间

- **updated_at** (DateTimeField, 自动)
  - 最后更新时间

### 配送信息字段
- **estimated_website_arrival_date** (DateField, 可选)
  - 官网预计到达日期

- **estimated_website_arrival_date_2** (DateField, 可选)
  - 官网预计到达日期2

- **tracking_number** (CharField, 最大长度50, 可选)
  - 邮寄单号

- **estimated_delivery_date** (DateField, 可选)
  - 邮寄预计送达日期

- **shipping_method** (CharField, 最大长度100, 可选)
  - 快递方式
  - 用于记录快递配送方式（例如：Standard, Express, DHL, EMS, SF Express）

- **official_query_url** (URLField, 最大长度500, 可选)
  - 官方查询URL
  - 用于存储官方订单追踪或查询的链接地址

- **delivery_status** (CharField, 最大长度30)
  - 配送状态
  - 可选值:
    - `pending_confirmation`: 等待确认
    - `shipped`: 已发送
    - `in_delivery`: 配送中
    - `delivered`: 已送达
  - 默认值: `pending_confirmation`

- **latest_delivery_status** (CharField, 最大长度10, 可选)
  - 最新配送状态（日文，最多10字符）

- **delivery_status_query_time** (DateTimeField, 可选)
  - 配送状态查询时间

- **delivery_status_query_source** (CharField, 最大长度100, 可选)
  - 配送状态查询来源

### Worker 锁定字段
用于数据采集worker的并发控制：

- **is_locked** (BooleanField)
  - 是否被 worker 锁定
  - 默认值: False

- **locked_at** (DateTimeField, 可选)
  - 锁定时间戳

- **locked_by_worker** (CharField, 最大长度50, 可选)
  - 锁定该记录的 worker 名称

- **is_deleted** (BooleanField)
  - 软删除标记
  - 默认值: False

**锁定机制说明**:
- 锁定超时: 5分钟（可在 worker 设置中配置）
- 过期锁定会被每日定时任务清理
- 用于防止基于 Playwright 的数据提取过程中的并发修改

## 属性方法

### inventory_count
```python
@property
def inventory_count(self):
    """获取关联的库存数量"""
```
- **返回**: 整数，关联的库存项目数量
- **用途**: 快速获取订单包含的库存数量

## 实例方法

### get_inventory_items
```python
def get_inventory_items(self):
    """获取所有关联的库存项目"""
```
- **返回**: QuerySet，所有关联的 Inventory 实例
- **用途**: 获取订单的所有库存项目

### update_fields
```python
def update_fields(self, **kwargs):
    """
    更新 Purchasing 实例字段，并同步更新相关库存信息。

    Args:
        **kwargs: 要更新的字段
            特殊键：
            - email (str): 用于查找或创建 OfficialAccount
            - name (str): 账号持有人姓名（仅在提供email时生效）
            - postal_code (str): 邮编（仅在提供email时生效）
            - address_line_1 (str): 地址1（仅在提供email时生效）
            - address_line_2 (str): 地址2（仅在提供email时生效）
            - payment_cards (list): 支付卡列表
            - iphone_type_names (list): 1-2个iPhone型号名称字符串列表
            - estimated_website_arrival_date (date | list[date]): 更新库存的 checked_arrival_at_1
                - 单个日期：应用到所有库存
                - 日期列表：按索引对应到每个库存（与 iphone_type_names 对应）
            - estimated_website_arrival_date_2: 仅更新Purchasing字段，不同步库存
            - estimated_delivery_date: 更新库存的 checked_arrival_at_2
            - last_info_updated_at: 被忽略（由系统自动更新）

    Returns:
        bool: 成功返回 True
    """
```

#### 特殊字段处理
1. **email**: 自动查找或创建对应的 OfficialAccount 并更新关联（详见下文）
2. **name, postal_code, address_line_1, address_line_2**: OfficialAccount 相关字段，仅在提供 email 时生效
3. **payment_cards**: 处理支付卡信息并创建支付记录
4. **iphone_type_names**: 匹配并更新关联的库存iPhone信息（详见下文）
5. **estimated_website_arrival_date**: 同步更新关联库存的 `checked_arrival_at_1`
   - 单个日期值：应用到所有匹配的库存
   - 日期列表：每个日期对应一个库存（与 `iphone_type_names` 索引一一对应）
6. **estimated_website_arrival_date_2**: 仅更新Purchasing字段，不同步更新库存
7. **estimated_delivery_date**: 同步更新所有关联库存的 `checked_arrival_at_2`
8. **tracking_number / shipping_method / email 冲突**: 若已有值且新值不同，会记录冲突并跳过更新

#### email 参数详解

`email` 参数用于查找或创建 OfficialAccount 并建立关联。当提供 `email` 时，可以同时提供以下字段来更新或创建 OfficialAccount：

**关联字段**:
- `name`: 账号持有人姓名
- `postal_code`: 邮编
- `address_line_1`: 地址1
- `address_line_2`: 地址2

**处理逻辑**:
1. 如果 OfficialAccount 存在：更新提供的字段
2. 如果 OfficialAccount 不存在：创建新账号并设置提供的字段
3. 新创建的账号，`account_id` 和 `passkey` 默认设置为 email 值

**重要提示**: 如果未提供 `email`，即使提供了 `name`、`postal_code`、`address_line_1`、`address_line_2` 这些字段，也不会执行任何操作。

**冲突处理**: 如果已有 `official_account.email` 与传入 `email` 不一致，会记录冲突并跳过账号更新，同时不会更新 `account_used`。

#### iphone_type_names 参数详解

`iphone_type_names` 参数用于智能匹配和更新关联的库存项目。它接收一个包含1-2个iPhone型号名称的列表。

**匹配逻辑**:
1. 解析每个 `iphone_type_name` 获取对应的 iPhone 对象
2. 按创建时间顺序获取现有库存
3. 逐一匹配：
   - **匹配成功**: 库存的 iPhone 与解析出的 iPhone 相同 → 更新时间字段（如有提供）
   - **匹配失败**: 库存的 iPhone 不同或为 None → 记录 error 日志，不更新该库存的时间字段
   - **库存不存在**: 新建库存并关联
4. **数量不匹配**: 如果现有库存数量 > 传入的 iphone_type_names 数量，对多出的库存记录 error 日志

**日志级别**: 所有警告和错误信息使用 Python logging 模块的 `error` 级别

**场景示例**:

| 场景 | 现有库存数 | 传入数量 | 处理逻辑 |
|------|--------------|----------|----------|
| 1 | 0 | 1 | 新建1个库存并关联 |
| 2 | 1 | 1，类型相同 | 更新时间字段（如有） |
| 3 | 1 | 1，类型不同 | error日志，不更新时间字段 |
| 4 | 2 | 2，都相同 | 更新时间字段（如有） |
| 5 | 2 | 2，1个相同1个不同 | 相同的更新，不同的error日志 |
| 6 | 1 | 2，1个相同1个不存在 | 相同的更新，新建1个库存 |
| 7 | 1 | 2，1个不同1个不存在 | 不同的error日志，新建1个库存并error日志警告 |
| 8 | 3 | 2 | 匹配前2个，第3个error日志 |

#### 使用示例

**示例1: 基本更新**
```python
purchasing = Purchasing.objects.get(uuid='...')

# 更新订单信息
purchasing.update_fields(
    email='new@example.com',
    delivery_status='shipped',
    estimated_website_arrival_date='2025-01-20'
)

# email 会自动关联 OfficialAccount
# estimated_website_arrival_date 会同步更新所有库存的 checked_arrival_at_1
```

**示例1.1: 更新 email 并同时更新 OfficialAccount 信息**
```python
purchasing = Purchasing.objects.get(uuid='...')

# 更新订单信息并同时更新或创建 OfficialAccount
purchasing.update_fields(
    email='user@example.com',
    name='山田太郎',
    postal_code='100-0001',
    address_line_1='东京都千代田区',
    address_line_2='丸之内1-1-1',
    delivery_status='shipped'
)

# 如果 email 对应的 OfficialAccount 存在，则更新 name、postal_code、address_line_1、address_line_2
# 如果不存在，则创建新的 OfficialAccount 并设置这些字段
```

**示例1.2: 仅更新部分 OfficialAccount 字段**
```python
purchasing = Purchasing.objects.get(uuid='...')

# 仅更新 name 和 postal_code
purchasing.update_fields(
    email='user@example.com',
    name='山田花子',
    postal_code='100-0002'
)

# 只更新提供的字段，address_line_1 和 address_line_2 保持不变
```

**示例2: 使用 iphone_type_names 匹配库存**
```python
purchasing = Purchasing.objects.get(uuid='...')

# 匹配并更新单个库存
purchasing.update_fields(
    iphone_type_names=['iPhone 17 Pro Max 256GB コズミックオレンジ'],
    estimated_website_arrival_date='2025-01-20',
    estimated_delivery_date='2025-01-25'
)

# 如果库存的 iPhone 类型匹配，则更新时间字段
# 如果不匹配，则记录 error 日志
```

**示例3: 匹配多个库存**
```python
purchasing = Purchasing.objects.get(uuid='...')

# 匹配并更新2个库存
purchasing.update_fields(
    iphone_type_names=[
        'iPhone 17 Pro Max 256GB コズミックオレンジ',
        'iPhone 17 Pro 128GB ブラック'
    ],
    estimated_website_arrival_date='2025-01-20'
)

# 按创建时间顺序匹配库存
# 第1个库存匹配第1个 iphone_type_name
# 第2个库存匹配第2个 iphone_type_name
```

**示例4: 自动创建缺失的库存**
```python
purchasing = Purchasing.objects.get(uuid='...')  # 假设没有关联库存

# 传入 iphone_type_names 会自动创建库存
purchasing.update_fields(
    iphone_type_names=['iPhone 17 Pro Max 256GB コズミックオレンジ'],
    estimated_website_arrival_date='2025-01-20'
)

# 会自动创建1个新的 Inventory 并关联到该 Purchasing
```

## 类方法

### create_with_inventory
```python
@classmethod
def create_with_inventory(cls, **kwargs):
    """
    创建采购订单并自动创建关联的库存项目。

    Args:
        **kwargs: Purchasing 字段的关键字参数
            特殊键：
            - email (str): 用于查找 OfficialAccount
            - inventory_count (int): 要创建的库存数量（可选）
            - jan (str): JAN码，用于查找并关联产品（可选）
            - iphone_type_name (str): iPhone 型号名称（可选，用于创建相同类型的多个库存）
            - iphone_type_names (list): iPhone 型号名称列表（可选，用于创建不同类型的多个库存）
            - estimated_website_arrival_date (date | list[date]): 预计到达日期（可选）
                - 单个日期：应用到所有库存
                - 日期列表：按索引对应到每个库存（与 iphone_type_names 对应）
            - card_number_1 (str): 第一张卡号（可选）
            - card_number_2 (str): 第二张卡号（可选）
            - card_number_3 (str): 第三张卡号（可选）
            - payment_amount_1 (Decimal): 卡1支付金额（可选，默认0）
            - payment_amount_2 (Decimal): 卡2支付金额（可选，默认0）
            - payment_amount_3 (Decimal): 卡3支付金额（可选，默认0）
            - payment_cards (list): 旧格式支付卡列表（可选）
            - creation_source (str): 订单创建来源（可选，默认自动记录调用方）

    Returns:
        tuple: (purchasing_instance, [inventory_list])
    """
```

#### 库存数量逻辑
- 如果提供 `iphone_type_names`（列表），`inventory_count` 自动设为列表长度
- 如果提供 `jan` 或 `iphone_type_name` 但未提供 `inventory_count`，默认为 1
- 如果都未提供，`inventory_count` 默认为 0（不创建库存）
- 可以显式指定 `inventory_count`

#### iphone_type_name vs iphone_type_names
- **iphone_type_name** (str): 用于创建多个**相同类型**的库存
- **iphone_type_names** (list): 用于创建多个**不同类型**的库存，每个型号名称对应一个库存

#### 使用示例

**示例1: 基本创建（带库存）**
```python
from apps.data_aggregation.models import Purchasing

# 创建订单并关联3个库存
purchasing, inventories = Purchasing.create_with_inventory(
    email='user@example.com',
    inventory_count=3,
    jan='4547597992388',  # iPhone JAN码
    card_number_1='1234567890123456',
    payment_amount_1=10000,
    delivery_status='pending_confirmation'
)

print(f"创建订单 {purchasing.order_number}，包含 {len(inventories)} 个库存")
```

**示例2: 使用 iPhone 型号名称**
```python
# 通过型号名称创建
purchasing, inventories = Purchasing.create_with_inventory(
    email='user@example.com',
    iphone_type_name='iPhone 15 Pro Max 256GB 钛金属',
    card_number_1='1234567890123456',
    payment_amount_1=15000
)
# inventory_count 自动设为 1
```

**示例3: 多张支付卡**
```python
purchasing, inventories = Purchasing.create_with_inventory(
    email='user@example.com',
    inventory_count=5,
    jan='4547597992388',
    card_number_1='1111111111111111',
    payment_amount_1=5000,
    card_number_2='2222222222222222',
    payment_amount_2=3000,
    card_number_3='3333333333333333',
    payment_amount_3=2000
)
```

**示例4: 旧格式支付卡**
```python
purchasing, inventories = Purchasing.create_with_inventory(
    email='user@example.com',
    inventory_count=2,
    payment_cards=[
        {
            'method': 'gift_card',
            'card_number': 'CARD123',
            'amount': '1000'
        },
        {
            'method': 'credit_card',
            'alternative_name': 'CARD-1-1',
            'amount': '2000'
        }
    ]
)
```

**示例5: 多个不同类型的库存（使用 iphone_type_names）**
```python
# 创建包含2个不同型号iPhone的订单
purchasing, inventories = Purchasing.create_with_inventory(
    email='user@example.com',
    iphone_type_names=[
        'iPhone 15 Pro Max 256GB ブラックチタニウム',
        'iPhone 15 Pro 128GB ホワイトチタニウム'
    ]
)
# inventory_count 自动设为 2，每个库存关联不同的 iPhone
```

**示例6: 多个库存使用不同的到达日期**
```python
from datetime import date

# 创建包含2个不同型号iPhone的订单，每个有不同的预计到达日期
purchasing, inventories = Purchasing.create_with_inventory(
    email='user@example.com',
    iphone_type_names=[
        'iPhone 15 Pro Max 256GB ブラックチタニウム',
        'iPhone 15 Pro 128GB ホワイトチタニウム'
    ],
    estimated_website_arrival_date=[
        date(2025, 1, 20),  # 第1个库存的到达日期
        date(2025, 1, 25)   # 第2个库存的到达日期
    ]
)
# 每个库存的 checked_arrival_at_1 会设置为对应的日期
```

**示例7: 多个库存使用相同的到达日期**
```python
from datetime import date

# 如果所有库存的日期相同，可以传入单个日期值
purchasing, inventories = Purchasing.create_with_inventory(
    email='user@example.com',
    iphone_type_names=[
        'iPhone 15 Pro Max 256GB ブラックチタニウム',
        'iPhone 15 Pro 128GB ホワイトチタニウム'
    ],
    estimated_website_arrival_date=date(2025, 1, 20)  # 所有库存使用相同日期
)
```

### 辅助类方法

以下是内部使用的辅助方法，通常不需要直接调用：

#### _find_official_account
```python
@staticmethod
def _find_official_account(email):
    """通过 email 查找 OfficialAccount"""
```

#### _find_product_by_jan
```python
@staticmethod
def _find_product_by_jan(jan):
    """
    通过 JAN 码查找产品（iPhone或iPad）

    Returns:
        tuple: (product_instance, product_type)
            product_type 为 'iphone' 或 'ipad'

    Raises:
        ValueError: 如果产品未找到
    """
```

#### _find_iphone_by_type_name
```python
@staticmethod
def _find_iphone_by_type_name(iphone_type_name):
    """
    通过标准型号名称查找 iPhone

    Args:
        iphone_type_name (str): 标准 iPhone 型号名称
            格式: "iPhone 17 Pro Max 256GB コズミックオレンジ"

    Returns:
        iPhone: 匹配的 iPhone 实例

    Raises:
        ValueError: 如果解析失败或未找到匹配的 iPhone
    """
```

**型号名称格式**:
- 格式: `{型号} {容量数字} {单位} {颜色}`
- 示例: `iPhone 15 Pro 256GB 钛金属`
- 支持 TB 和 GB 单位（TB 会自动转换为 GB）

#### _find_card_by_number
```python
@staticmethod
def _find_card_by_number(card_number):
    """
    通过卡号查找支付卡（GiftCard、DebitCard 或 CreditCard）

    查找顺序: GiftCard → DebitCard → CreditCard

    Returns:
        tuple: (card_instance, card_type)
            card_type 为 'gift'、'debit' 或 'credit'

    Raises:
        ValueError: 如果卡未找到
    """
```

#### _generate_order_number
```python
@staticmethod
def _generate_order_number():
    """
    生成唯一订单号

    Returns:
        str: 格式为 "ORD-{timestamp}-{random}" 的订单号
    """
```

格式示例: `ORD-20250115123456-1a2b3c4d`

## 数据库索引

模型包含以下索引以优化查询性能：
- `uuid` 字段索引
- `order_number` 字段索引
- `delivery_status` 字段索引
- `created_at` 字段索引
- `shipped_at` 字段降序索引
- `tracking_number` 字段索引
- `is_locked` 字段索引
- `batch_encoding` 字段索引

## 与其他模型的关系

### 一对多关系
- **OfficialAccount** → Purchasing (一个官方账号可以有多个采购订单)
- **Purchasing** → Inventory (一个采购订单可以有多个库存项目)

### 多对多关系（通过中间表）
- **Purchasing** ↔ **GiftCard** (通过 GiftCardPayment)
- **Purchasing** ↔ **DebitCard** (通过 DebitCardPayment)
- **Purchasing** ↔ **CreditCard** (通过 CreditCardPayment)

## 业务逻辑说明

1. **订单号自动生成**: 仅在 `create_with_inventory` 中，如果不提供 `order_number`，系统会自动生成

2. **账号关联**:
   - 通过 `email` 自动查找并关联 `OfficialAccount`
   - 即使未找到账号，`account_used` 也会记录 email

3. **支付卡匹配**:
   - 优先通过 `card_number` 查找
   - 备选通过 `alternative_name` 查找
   - 未匹配的卡信息记录在 `payment_method` 字段

4. **库存同步更新**:
   - 更新 `estimated_website_arrival_date` 会同步更新库存的 `checked_arrival_at_1`
   - 更新 `estimated_delivery_date` 会同步更新库存的 `checked_arrival_at_2`

5. **Worker 锁定机制**:
   - 用于并发控制，防止多个 worker 同时处理同一订单
   - 锁定超时后自动释放

## 相关 Task

### official_account_order_planning
**文件位置**: `apps/data_acquisition/tasks.py:179-393`

**功能**: 官方账号订单规划任务

**参数**:
- `batch_encoding` (str): 批次编号，用于过滤账号和卡
- `jan` (str): 电子产品的 JAN 码
- `inventory_count` (int): 每个订单的库存数量
- `cards_per_group` (int): 每组卡的数量
- `card_type` (str): 卡类型 - 'GiftCard'、'CreditCard' 或 'DebitCard'

**任务流程**:
1. 验证参数（当前最多支持3张卡/组）
2. 查找指定 `batch_encoding` 的 OfficialAccount
3. 查找指定 `batch_encoding` 的支付卡
4. 验证卡数量可被 `cards_per_group` 整除
5. 验证卡组数量与账号数量匹配
6. 按 `alternative_name` 数字后缀排序卡
7. 分组卡片
8. 为每个账号创建采购订单（使用 `create_with_inventory`）

**使用示例**:
```python
from apps.data_acquisition.tasks import official_account_order_planning

# 异步调用
result = official_account_order_planning.delay(
    batch_encoding='BATCH-001',
    jan='4547597992388',
    inventory_count=2,
    cards_per_group=2,
    card_type='GiftCard'
)
```

**返回结果**:
```python
{
    'status': 'success',
    'task_id': '...',
    'batch_encoding': 'BATCH-001',
    'jan': '4547597992388',
    'card_type': 'GiftCard',
    'accounts_processed': 10,
    'orders_created': 10,
    'orders': [
        {
            'purchasing_id': 123,
            'purchasing_uuid': '...',
            'order_number': 'ORD-...',
            'account_email': 'user1@example.com',
            'inventory_count': 2,
            'card_numbers': ['CARD001', 'CARD002']
        },
        # ...
    ]
}
```

**注意事项**:
1. 当前最多支持每组3张卡（`create_with_inventory` 的限制）
2. 卡数量必须可被 `cards_per_group` 整除
3. 卡组数量必须与账号数量相等
4. 卡按 `alternative_name` 的数字后缀排序

## 相关 API 端点

详见 `docs/API_PURCHASING.md`

## 相关文档

- [Inventory 模型说明](MODEL_INVENTORY.md)
- [OfficialAccount 模型说明](MODEL_OFFICIAL_ACCOUNT.md)
- [数据采集 Workers 文档](DATA_ACQUISITION_WORKERS.md)

## 注意事项

1. **事务安全**: `create_with_inventory` 和 `update_fields` 都使用数据库事务

2. **卡数量限制**: 当前 `create_with_inventory` 最多支持3张支付卡

3. **JAN 码或型号名称**: 两者只需提供一个，都提供时优先使用 JAN 码

4. **Worker 锁定**:
   - 使用数据采集 worker 时注意锁定机制
   - 锁定超时默认5分钟
   - 过期锁定会被定时任务清理

5. **软删除**: 删除时应设置 `is_deleted=True`

6. **库存同步**: 更新预计到达日期会自动同步所有关联库存的对应字段

7. **支付卡匹配失败**: 未匹配的支付卡信息会记录在 `payment_method` 字段，格式为 `(card_type, identifier)|...`
8. **创建来源记录**: `create_with_inventory` 会在未提供 `creation_source` 时自动记录调用方
