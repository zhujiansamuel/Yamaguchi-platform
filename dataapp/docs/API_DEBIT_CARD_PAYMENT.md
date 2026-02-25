# DebitCardPayment API 文档

## 概述

DebitCardPayment（借记卡支付）API 是 DebitCard 和 Purchasing 之间的中间表 API，用于管理借记卡在采购订单中的支付记录。

**Base URL**: `/api/aggregation/debitcard-payments/`

---

## 模型说明

DebitCardPayment 是一个中间模型，记录了借记卡与采购订单之间的支付关系，包括支付金额、支付时间和支付状态。

---

## 模型字段说明

| 字段 | 类型 | 必填 | 只读 | 说明 |
|------|------|------|------|------|
| `id` | Integer | - | ✓ | 主键ID |
| `debit_card` | Integer | ✓ | - | 借记卡ID（外键） |
| `debit_card_number` | String | - | ✓ | 借记卡号（SerializerMethod） |
| `purchasing` | Integer | ✓ | - | 采购订单ID（外键） |
| `purchasing_order_number` | String | - | ✓ | 采购订单号（SerializerMethod） |
| `payment_amount` | Decimal | ✓ | - | 支付金额（最大12位，2位小数） |
| `payment_time` | DateTime | - | ✓ | 支付时间（自动生成） |
| `payment_status` | String(20) | - | - | 支付状态（默认：pending） |
| `created_at` | DateTime | - | ✓ | 创建时间（自动生成） |
| `updated_at` | DateTime | - | ✓ | 更新时间（自动更新） |

---

## 枚举值

### 支付状态 (payment_status)

| 值 | 显示名称 | 说明 |
|----|----------|------|
| `pending` | 待处理 | 支付待处理 |
| `completed` | 已完成 | 支付已完成 |
| `failed` | 失败 | 支付失败 |
| `refunded` | 已退款 | 支付已退款 |

---


## 认证

所有 API 请求需要使用 `BATCH_STATS_API_TOKEN` 进行认证。

### 认证方式

在请求头中添加 Authorization：

```
Authorization: Bearer <BATCH_STATS_API_TOKEN>
```

### 配置 Token

在 `.env` 文件或 `settings.py` 中配置：

```env
BATCH_STATS_API_TOKEN=your-secure-token-here
```

### 认证失败响应

| 状态码 | 说明 |
|--------|------|
| 401 | Token 缺失、无效或未配置 |

```json
{
    "detail": "Invalid token"
}
```

---
## API 端点

### 1. 获取支付记录列表

**请求**
```http
GET /api/aggregation/debitcard-payments/
```

**查询参数**
- `payment_status`: 按支付状态过滤（例如：`?payment_status=completed`）
- `debit_card`: 按借记卡ID过滤（例如：`?debit_card=1`）
- `purchasing`: 按采购订单ID过滤（例如：`?purchasing=1`）
- `search`: 搜索支付状态（例如：`?search=completed`）
- `ordering`: 排序字段（例如：`?ordering=-payment_time`）

**响应示例**
```json
{
  "count": 10,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "debit_card": 1,
      "debit_card_number": "9876543210987654",
      "purchasing": 1,
      "purchasing_order_number": "ORD20250110001",
      "payment_amount": "12000.00",
      "payment_time": "2025-01-10T10:00:00Z",
      "payment_status": "completed",
      "created_at": "2025-01-10T10:00:00Z",
      "updated_at": "2025-01-10T11:00:00Z"
    }
  ]
}
```

---

### 2. 创建支付记录

**请求**
```http
POST /api/aggregation/debitcard-payments/
Content-Type: application/json
```

**请求体**
```json
{
  "debit_card": 1,
  "purchasing": 2,
  "payment_amount": "18000.00",
  "payment_status": "pending"
}
```

**响应示例**
```json
{
  "id": 2,
  "debit_card": 1,
  "debit_card_number": "9876543210987654",
  "purchasing": 2,
  "purchasing_order_number": "ORD20250115001",
  "payment_amount": "18000.00",
  "payment_time": "2025-01-12T10:00:00Z",
  "payment_status": "pending",
  "created_at": "2025-01-12T10:00:00Z",
  "updated_at": "2025-01-12T10:00:00Z"
}
```

**状态码**
- `201 Created`: 创建成功
- `400 Bad Request`: 请求数据验证失败

**验证规则**
- `payment_amount`: 必须大于 0

---

### 3. 获取单个支付记录详情

**请求**
```http
GET /api/aggregation/debitcard-payments/{id}/
```

**响应示例**
```json
{
  "id": 1,
  "debit_card": 1,
  "debit_card_number": "9876543210987654",
  "purchasing": 1,
  "purchasing_order_number": "ORD20250110001",
  "payment_amount": "12000.00",
  "payment_time": "2025-01-10T10:00:00Z",
  "payment_status": "completed",
  "created_at": "2025-01-10T10:00:00Z",
  "updated_at": "2025-01-10T11:00:00Z"
}
```

---

### 4. 更新支付记录（部分更新）

**请求**
```http
PATCH /api/aggregation/debitcard-payments/{id}/
Content-Type: application/json
```

**请求体示例 - 更新支付状态**
```json
{
  "payment_status": "completed"
}
```

**响应示例**
```json
{
  "id": 2,
  "debit_card": 1,
  "debit_card_number": "9876543210987654",
  "purchasing": 2,
  "purchasing_order_number": "ORD20250115001",
  "payment_amount": "18000.00",
  "payment_time": "2025-01-12T10:00:00Z",
  "payment_status": "completed",
  "created_at": "2025-01-12T10:00:00Z",
  "updated_at": "2025-01-13T09:00:00Z"
}
```

---

### 5. 删除支付记录

**请求**
```http
DELETE /api/aggregation/debitcard-payments/{id}/
```

**响应**
```http
HTTP/1.1 204 No Content
```

---

## 使用示例

### Python (requests)

```python
import requests

base_url = "http://your-domain.com/api/aggregation/debitcard-payments/"

# 1. 查询某张借记卡的所有支付记录
response = requests.get(base_url, params={"debit_card": 1})
payments = response.json()

# 2. 创建支付记录
new_payment = {
    "debit_card": 1,
    "purchasing": 3,
    "payment_amount": "22000.00",
    "payment_status": "pending"
}
response = requests.post(base_url, json=new_payment)
created_payment = response.json()

# 3. 更新支付状态为已完成
payment_id = created_payment['id']
update_data = {"payment_status": "completed"}
response = requests.patch(f"{base_url}{payment_id}/", json=update_data)

# 4. 查询某个订单的所有借记卡支付
response = requests.get(base_url, params={"purchasing": 1})
order_payments = response.json()

# 5. 删除支付记录
response = requests.delete(f"{base_url}{payment_id}/")
```

### cURL

```bash
# 获取列表（按借记卡过滤）
curl -X GET "http://your-domain.com/api/aggregation/debitcard-payments/?debit_card=1"

# 创建支付记录
curl -X POST "http://your-domain.com/api/aggregation/debitcard-payments/" \
  -H "Content-Type: application/json" \
  -d '{
    "debit_card": 1,
    "purchasing": 3,
    "payment_amount": "22000.00",
    "payment_status": "pending"
  }'

# 更新支付状态
curl -X PATCH "http://your-domain.com/api/aggregation/debitcard-payments/1/" \
  -H "Content-Type: application/json" \
  -d '{"payment_status": "completed"}'

# 删除支付记录
curl -X DELETE "http://your-domain.com/api/aggregation/debitcard-payments/1/"
```

---

## 高级查询

### 过滤示例

```http
# 按支付状态过滤
GET /api/aggregation/debitcard-payments/?payment_status=completed

# 按借记卡过滤
GET /api/aggregation/debitcard-payments/?debit_card=1

# 按采购订单过滤
GET /api/aggregation/debitcard-payments/?purchasing=1

# 组合查询：某张卡的已完成支付
GET /api/aggregation/debitcard-payments/?debit_card=1&payment_status=completed
```

### 排序示例

```http
# 按支付时间降序
GET /api/aggregation/debitcard-payments/?ordering=-payment_time

# 按支付金额降序
GET /api/aggregation/debitcard-payments/?ordering=-payment_amount

# 按创建时间升序
GET /api/aggregation/debitcard-payments/?ordering=created_at
```

---

## 关联关系

### 外键关系

```python
# DebitCardPayment.debit_card -> DebitCard
# DebitCardPayment.purchasing -> Purchasing
# DebitCard.payments -> DebitCardPayment (反向关系)
# Purchasing.debit_card_payments -> DebitCardPayment (反向关系)
```

### 查询示例

```python
# 查询某张借记卡的所有支付记录
debit_card = DebitCard.objects.get(id=1)
payments = debit_card.payments.all()

# 查询某个订单的所有借记卡支付
purchasing = Purchasing.objects.get(id=1)
payments = purchasing.debit_card_payments.all()

# 计算某张卡的总支付金额
from django.db.models import Sum
total = DebitCardPayment.objects.filter(
    debit_card_id=1,
    payment_status='completed'
).aggregate(Sum('payment_amount'))
```

---

## 错误处理

### 常见错误

**400 Bad Request - 支付金额无效**
```json
{
  "payment_amount": ["Payment amount must be greater than zero"]
}
```

**400 Bad Request - 缺少必填字段**
```json
{
  "debit_card": ["This field is required."],
  "purchasing": ["This field is required."],
  "payment_amount": ["This field is required."]
}
```

**400 Bad Request - 借记卡不存在**
```json
{
  "debit_card": ["Invalid pk \"999\" - object does not exist."]
}
```

**404 Not Found - 资源不存在**
```json
{
  "detail": "Not found."
}
```

---

## 数据库表结构

```sql
CREATE TABLE debit_card_payments (
    id SERIAL PRIMARY KEY,
    debit_card_id INTEGER REFERENCES debit_cards(id) ON DELETE SET NULL,
    purchasing_id INTEGER REFERENCES purchasing(id) ON DELETE SET NULL,
    payment_amount DECIMAL(12, 2) NOT NULL CHECK (payment_amount > 0),
    payment_time TIMESTAMP NOT NULL,
    payment_status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL
);

CREATE INDEX ON debit_card_payments(payment_status);
CREATE INDEX ON debit_card_payments(payment_time DESC);
```

---

## 业务场景示例

### 场景1：使用借记卡支付订单

```python
# 1. 获取借记卡和订单信息
debit_card_id = 1
purchasing_id = 5
payment_amount = "28000.00"

# 2. 检查借记卡余额是否足够
debit_card_url = "http://your-domain.com/api/aggregation/debitcards/"
response = requests.get(f"{debit_card_url}{debit_card_id}/")
card_info = response.json()

if float(card_info['balance']) >= float(payment_amount):
    # 3. 创建待处理的支付记录
    payment_data = {
        "debit_card": debit_card_id,
        "purchasing": purchasing_id,
        "payment_amount": payment_amount,
        "payment_status": "pending"
    }
    response = requests.post(base_url, json=payment_data)
    payment = response.json()

    # 4. 处理支付...（外部支付系统）

    # 5. 更新支付状态和卡余额
    update_status = {"payment_status": "completed"}
    requests.patch(f"{base_url}{payment['id']}/", json=update_status)

    new_balance = float(card_info['balance']) - float(payment_amount)
    update_balance = {"balance": str(new_balance)}
    requests.patch(f"{debit_card_url}{debit_card_id}/", json=update_balance)
else:
    print("Insufficient balance")
```

### 场景2：查询订单的总支付金额

```python
# 查询订单的所有支付记录
response = requests.get(base_url, params={
    "purchasing": 1,
    "payment_status": "completed"
})
payments = response.json()['results']

# 计算总金额
total_amount = sum(float(p['payment_amount']) for p in payments)
print(f"Total payment: {total_amount}")
```

### 场景3：退款处理

```python
# 1. 查找需要退款的支付记录
payment_id = 1
response = requests.get(f"{base_url}{payment_id}/")
payment = response.json()

# 2. 更新支付状态为已退款
update_data = {"payment_status": "refunded"}
requests.patch(f"{base_url}{payment_id}/", json=update_data)

# 3. 退回借记卡余额
debit_card_id = payment['debit_card']
debit_card_url = "http://your-domain.com/api/aggregation/debitcards/"
response = requests.get(f"{debit_card_url}{debit_card_id}/")
card_info = response.json()

new_balance = float(card_info['balance']) + float(payment['payment_amount'])
update_balance = {"balance": str(new_balance)}
requests.patch(f"{debit_card_url}{debit_card_id}/", json=update_balance)
```

---

## 注意事项

1. **外键约束**: 借记卡和采购订单被删除时，支付记录的外键会设置为 NULL（ON DELETE SET NULL）
2. **支付金额**: 必须大于 0
3. **支付时间**: 自动生成，不可修改
4. **余额管理**: 系统不自动扣减借记卡余额，需要手动更新
5. **状态转换**: 建议按照 pending -> completed/failed 的流程更新状态
6. **退款处理**: 退款时应将状态更新为 'refunded' 并手动退回余额

---

## 相关文档

- [Debit Card API 文档](./API_DEBIT_CARD.md)
- [Credit Card Payment API 文档](./API_CREDIT_CARD_PAYMENT.md)
- [Purchasing API 文档](./API_PURCHASING.md)
- [模型架构文档](../ARCHITECTURE.md)
