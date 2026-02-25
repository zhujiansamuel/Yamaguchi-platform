# create_with_inventory 方法使用说明

## 概述

`Purchasing.create_with_inventory()` 是一个类方法，用于创建采购订单并自动关联库存、产品和支付卡。该方法提供了灵活的参数配置，支持多种业务场景。

**位置**: `apps/data_aggregation/models.py` - Purchasing 模型

---

## 方法签名

```python
@classmethod
def create_with_inventory(cls, **kwargs):
    """
    创建采购订单并自动创建关联的库存项目。

    Returns:
        tuple: (purchasing_instance, [inventory_list])
    """
```

---

## Special Keys（特殊参数）

### 基础参数

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| `email` | String | 否 | None | 官方账号的邮箱，用于查找并关联 OfficialAccount |
| `inventory_count` | Integer | 否 | 见下方逻辑 | 要创建的库存数量 |

### 产品关联参数

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| `jan` | String(13) | 否 | None | JAN码（Japanese Article Number），用于查找并关联 iPhone 或 iPad 产品 |
| `iphone_type_name` | String | 否 | None | iPhone 标准型号命名，用于查找并关联 iPhone（如 `iPhone 17 Pro Max 256GB コズミックオレンジ`，其中 1TB 会按 1024GB 匹配） |

### 支付卡参数

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| `card_number_1` | String | 否 | None | 第一张支付卡的卡号 |
| `payment_amount_1` | Decimal | 否 | 0 | 第一张卡的支付金额 |
| `card_number_2` | String | 否 | None | 第二张支付卡的卡号 |
| `payment_amount_2` | Decimal | 否 | 0 | 第二张卡的支付金额 |
| `card_number_3` | String | 否 | None | 第三张支付卡的卡号 |
| `payment_amount_3` | Decimal | 否 | 0 | 第三张卡的支付金额 |

### 其他 Purchasing 字段

可以传入任何 Purchasing 模型的字段作为参数，例如：
- `delivery_status`: 配送状态
- `order_number`: 订单号（如果不提供会自动生成）
- `payment_method`: 支付方式
- 等等...

---

## 库存创建逻辑

`inventory_count` 的值由以下逻辑决定：

1. **如果明确提供了 `inventory_count`**：按指定数量创建库存
2. **如果提供了 `jan` 或 `iphone_type_name` 但未提供 `inventory_count`**：默认创建 1 个库存
3. **如果既未提供 `jan`/`iphone_type_name` 也未提供 `inventory_count`**：不创建库存（inventory_count = 0）

```python
# 示例
Purchasing.create_with_inventory(email='user@example.com')
# 结果：创建订单，但不创建库存

Purchasing.create_with_inventory(jan='4547597992388')
# 结果：创建订单 + 1个关联产品的库存

Purchasing.create_with_inventory(iphone_type_name='iPhone 17 Pro Max 256GB コズミックオレンジ')
# 结果：创建订单 + 1个关联 iPhone 产品的库存

Purchasing.create_with_inventory(inventory_count=3, jan='4547597992388')
# 结果：创建订单 + 3个关联产品的库存
```

---

## JAN码产品关联

### 查找逻辑

当提供 `jan` 参数时：
1. 首先在 `iPhone` 模型中查找匹配的 JAN 码
2. 如果未找到，继续在 `iPad` 模型中查找
3. 如果都未找到，抛出 `ValueError` 异常（带 TODO 标签）

### 自动关联

找到产品后，创建的所有库存都会自动关联该产品：
- 如果是 iPhone：`inventory.iphone = 找到的iPhone实例`
- 如果是 iPad：`inventory.ipad = 找到的iPad实例`

---

## iPhone 标准型号关联

当提供 `iphone_type_name` 参数时（且未提供 `jan`）：
1. 按 `型号 + 容量 + 颜色` 解析标准命名字符串
2. 在 `iPhone` 模型中查找匹配的记录（容量 1TB 会按 1024GB 匹配）
3. 若未找到或匹配到多条记录，将抛出 `ValueError`

---

## 支付卡关联

### 卡号查找顺序

当提供 `card_number_X` 参数时，系统按以下顺序查找：
1. `GiftCard`（礼品卡）
2. `DebitCard`（借记卡）
3. `CreditCard`（信用卡）

找到第一个匹配的卡后停止搜索。

### 支付记录创建

系统会自动创建对应的支付记录：
- **GiftCard** → `GiftCardPayment`
- **DebitCard** → `DebitCardPayment`
- **CreditCard** → `CreditCardPayment`

所有支付记录的默认属性：
- `payment_status`: `'pending'`（待处理）
- `payment_time`: `None`（留空）
- `payment_amount`: 对应的 `payment_amount_X` 值（默认 0）

### 异常处理

- 如果提供了 `card_number_X` 但未找到卡：抛出 `ValueError`（带 TODO 标签）
- 如果提供了 `payment_amount_X` 但未提供 `card_number_X`：抛出 `ValueError`（带 TODO 标签）

---

## 使用示例

### 示例 1：基础订单创建（无库存）

```python
from apps.data_aggregation.models import Purchasing

# 创建订单，不创建库存
purchasing, inventories = Purchasing.create_with_inventory(
    email='user@example.com',
    delivery_status='pending_confirmation',
    payment_method='现金'
)

print(f"订单号: {purchasing.order_number}")
print(f"库存数量: {len(inventories)}")  # 输出: 0
```

### 示例 2：创建订单 + 关联产品库存

```python
# 通过JAN码查找并关联iPhone产品
purchasing, inventories = Purchasing.create_with_inventory(
    email='user@example.com',
    jan='4547597992388',  # iPhone的JAN码
    delivery_status='pending_confirmation'
)

print(f"订单号: {purchasing.order_number}")
print(f"库存数量: {len(inventories)}")  # 输出: 1
print(f"关联产品: {inventories[0].iphone.model_name}")
```

### 示例 3：创建订单 + 多个库存 + 产品关联

```python
purchasing, inventories = Purchasing.create_with_inventory(
    email='user@example.com',
    inventory_count=3,  # 创建3个库存
    jan='4547597992388',
    delivery_status='in_delivery'
)

print(f"库存数量: {len(inventories)}")  # 输出: 3
# 所有3个库存都关联了同一个iPhone产品
for inv in inventories:
    print(f"库存UUID: {inv.uuid}, 产品: {inv.iphone.model_name}")
```

### 示例 4：创建订单 + 单张支付卡

```python
purchasing, inventories = Purchasing.create_with_inventory(
    email='user@example.com',
    jan='4547597992388',
    card_number_1='CARD20250110001',  # 礼品卡卡号
    payment_amount_1=10000,
    delivery_status='pending_confirmation'
)

# 查看支付记录
payments = purchasing.gift_cards.all()
print(f"支付卡数量: {payments.count()}")
```

### 示例 5：创建订单 + 多张支付卡

```python
purchasing, inventories = Purchasing.create_with_inventory(
    email='user@example.com',
    inventory_count=2,
    jan='4547597992388',
    # 第一张卡：礼品卡
    card_number_1='CARD20250110001',
    payment_amount_1=5000,
    # 第二张卡：信用卡
    card_number_2='1234567890123456',
    payment_amount_2=3000,
    # 第三张卡：借记卡（payment_amount未提供，默认0）
    card_number_3='9876543210987654',
    delivery_status='shipped'
)

print(f"订单号: {purchasing.order_number}")
print(f"库存数量: {len(inventories)}")  # 输出: 2
```

### 示例 6：完整示例（所有功能）

```python
from decimal import Decimal

purchasing, inventories = Purchasing.create_with_inventory(
    # 官方账号
    email='user@example.com',

    # 库存和产品
    inventory_count=3,
    jan='4547597992388',

    # 支付卡（最多3张）
    card_number_1='CARD20250110001',      # GiftCard
    payment_amount_1=Decimal('10000.00'),
    card_number_2='1234567890123456',     # CreditCard
    payment_amount_2=Decimal('5000.00'),
    card_number_3='9876543210987654',     # DebitCard
    payment_amount_3=Decimal('3000.00'),

    # Purchasing模型的其他字段
    delivery_status='pending_confirmation',
    order_number='CUSTOM-ORD-001',  # 可选，不提供会自动生成
    payment_method='组合支付'
)

# 结果分析
print(f"订单号: {purchasing.order_number}")
print(f"官方账号: {purchasing.official_account.email}")
print(f"库存数量: {len(inventories)}")
print(f"每个库存关联的产品: {inventories[0].iphone.model_name}")

# 查看支付记录
print(f"\n支付卡记录:")
for payment in purchasing.gift_cards.all():
    print(f"  礼品卡: {payment.gift_card.card_number}, 金额: {payment.payment_amount}")
for payment in purchasing.credit_cards.all():
    print(f"  信用卡: {payment.credit_card.card_number}, 金额: {payment.payment_amount}")
for payment in purchasing.debit_cards.all():
    print(f"  借记卡: {payment.debit_card.card_number}, 金额: {payment.payment_amount}")
```

---

## 错误处理

### JAN码未找到

```python
try:
    purchasing, inventories = Purchasing.create_with_inventory(
        jan='9999999999999',  # 不存在的JAN码
        email='user@example.com'
    )
except ValueError as e:
    print(f"错误: {e}")
    # 输出: Product with JAN code 9999999999999 not found in iPhone or iPad models
```

### 卡号未找到

```python
try:
    purchasing, inventories = Purchasing.create_with_inventory(
        card_number_1='INVALID_CARD_NUMBER',
        payment_amount_1=1000,
        email='user@example.com'
    )
except ValueError as e:
    print(f"错误: {e}")
    # 输出: Card with card_number INVALID_CARD_NUMBER not found in GiftCard, DebitCard, or CreditCard models
```

### payment_amount 提供但 card_number 未提供

```python
try:
    purchasing, inventories = Purchasing.create_with_inventory(
        payment_amount_1=1000,  # 提供了金额但没有卡号
        email='user@example.com'
    )
except ValueError as e:
    print(f"错误: {e}")
    # 输出: payment_amount_1 provided but card_number_1 is missing
```

---

## 事务处理

该方法使用 Django 的 `transaction.atomic()` 包装，确保所有操作的原子性：
- 如果任何步骤失败，所有更改都会回滚
- 订单、库存和支付记录要么全部创建成功，要么全部不创建

```python
from django.db import transaction

try:
    with transaction.atomic():
        purchasing, inventories = Purchasing.create_with_inventory(
            jan='INVALID_JAN',
            card_number_1='INVALID_CARD'
        )
except ValueError:
    # 如果JAN或卡号无效，订单和库存都不会被创建
    print("创建失败，所有更改已回滚")
```

---

## 返回值

该方法返回一个元组：

```python
(purchasing_instance, inventory_list)
```

- `purchasing_instance`: 创建的 Purchasing 实例
- `inventory_list`: 创建的 Inventory 实例列表（可能为空列表）

---

## 最佳实践

### 1. 使用 try-except 处理异常

```python
try:
    purchasing, inventories = Purchasing.create_with_inventory(**params)
except ValueError as e:
    # 处理JAN或卡号未找到的错误
    logger.error(f"创建订单失败: {e}")
except Exception as e:
    # 处理其他错误
    logger.error(f"未预期的错误: {e}")
```

### 2. 验证数据后再调用

```python
# 先验证JAN码是否存在
if jan_code:
    if not (iPhone.objects.filter(jan=jan_code).exists() or
            iPad.objects.filter(jan=jan_code).exists()):
        raise ValueError(f"JAN码 {jan_code} 不存在")

# 先验证卡号是否存在
for card_number in [card_num_1, card_num_2, card_num_3]:
    if card_number:
        if not (GiftCard.objects.filter(card_number=card_number).exists() or
                DebitCard.objects.filter(card_number=card_number).exists() or
                CreditCard.objects.filter(card_number=card_number).exists()):
            raise ValueError(f"卡号 {card_number} 不存在")

# 然后调用方法
purchasing, inventories = Purchasing.create_with_inventory(**params)
```

### 3. 使用 Decimal 类型处理金额

```python
from decimal import Decimal

purchasing, inventories = Purchasing.create_with_inventory(
    payment_amount_1=Decimal('10000.00'),  # 推荐
    # payment_amount_1=10000,  # 也可以，会自动转换
    # payment_amount_1='10000.00',  # 也可以，会自动转换
)
```

---

## TODO 标签位置

代码中包含以下 TODO 标签，标记了需要后续完善的逻辑：

1. **`_parse_kwargs` 方法** (line 994-995)
   - 当提供 `payment_amount` 但未提供 `card_number` 时的处理逻辑

2. **`_find_product_by_jan` 方法** (line 1060)
   - JAN 码未找到时的 fallback 逻辑

3. **`_find_card_by_number` 方法** (line 1104)
   - 卡号未找到时的 fallback 逻辑

---

## 相关文档

- [Purchasing API 文档](./API_PURCHASING.md)
- [Inventory 模型文档](./MODEL_INVENTORY.md)
- [Credit Card API 文档](./API_CREDIT_CARD.md)
- [Debit Card API 文档](./API_DEBIT_CARD.md)
- [Gift Card API 文档](./API_GIFT_CARD.md)
- [Official Account API 文档](./API_OFFICIAL_ACCOUNT.md)

---

## 更新历史

- **2026-01-03**:
  - 添加 `jan` 参数支持产品关联
  - 添加 `card_number_1/2/3` 和 `payment_amount_1/2/3` 参数支持直接卡号支付
  - 修改库存创建逻辑（不再默认创建1个库存）
  - 添加 TODO 标签标记后续逻辑

- **之前版本**:
  - 基础的订单和库存创建功能
  - 支持 `email` 和 `inventory_count` 参数
  - 支持 legacy `payment_cards` 格式

---

## 项目内 `CREATE_WITH_INVENTORY` 使用位置汇总

> 说明：代码中方法名实际为 `create_with_inventory`，以下汇总的是项目中真实调用点（按业务模块归类）。

### 1) 数据采集任务（批量建单）

- 文件：`apps/data_acquisition/tasks.py`
- 调用：`Purchasing.create_with_inventory(**order_kwargs)`
- 场景：订单规划任务中，按账号与卡分组批量创建采购订单，并同时创建库存记录。

### 2) 邮件解析（通知邮件）

- 文件：`apps/data_acquisition/EmailParsing/send_notification_email.py`
- 调用：`Purchasing.create_with_inventory(**create_kwargs)`
- 场景：当未匹配到现有订单时，根据邮件内容（机型、数量、物流字段等）新建采购单与库存，再补充更新账号/地址信息。

### 3) 邮件解析（初始下单确认邮件）

- 文件：`apps/data_acquisition/EmailParsing/initial_order_confirmation_email.py`
- 调用：`Purchasing.create_with_inventory(**create_kwargs)`
- 场景：未命中现有订单时，从确认邮件解析出的订单信息创建采购单与库存，然后回填 OfficialAccount 相关字段。

### 4) 追踪器（Japan Post）

- 文件：`apps/data_acquisition/trackers/redirect_to_japan_post_tracking.py`
- 调用：`Purchasing.create_with_inventory(email=..., inventory_count=1, iphone_type_name=..., order_number=...)`
- 场景：追踪结果回写时若订单不存在，则创建新的 Purchasing 记录（显式传入 `order_number`，避免自动生成）。

### 5) 追踪器（Yamato 官网）

- 文件：`apps/data_acquisition/trackers/official_website_redirect_to_yamato_tracking.py`
- 调用：`Purchasing.create_with_inventory(email=..., inventory_count=1, iphone_type_name=..., order_number=...)`
- 场景：与 Japan Post 追踪器同类逻辑，订单不存在时先创建采购单再执行后续字段更新。

### 6) 法人线下入库 API（另一个模型）

- 文件：`apps/data_aggregation/views.py`
- 调用：`LegalPersonOffline.create_with_inventory(inventory_data=..., skip_on_error=True, **legal_person_fields)`
- 场景：API 批量创建 `LegalPersonOffline` 及其关联库存，支持跳过错误条目并返回 `skipped_count`。

### 7) 模型定义入口（方法实现位置）

- 文件：`apps/data_aggregation/models.py`
- `LegalPersonOffline.create_with_inventory(...)`：法人线下数据 + 库存联动创建实现。
- `Purchasing.create_with_inventory(...)`：采购单 + 库存（及支付卡关联）联动创建实现。

