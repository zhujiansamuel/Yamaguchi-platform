# CreditCard API 文档

## 概述

CreditCard（信用卡）API 提供了对信用卡信息和支付记录的完整 CRUD 操作支持。

**Base URL**: `/api/aggregation/creditcards/`

---

## 模型字段说明

| 字段 | 类型 | 必填 | 只读 | 说明 |
|------|------|------|------|------|
| `id` | Integer | - | ✓ | 主键ID |
| `card_number` | String(19) | ✓ | - | 卡号（唯一，最多19位） |
| `alternative_name` | String(100) | - | - | 别名（方便人类管理的标签） |
| `expiry_month` | Integer | ✓ | - | 有效期月份（1-12） |
| `expiry_year` | Integer | ✓ | - | 有效期年份（>=2000） |
| `passkey` | String(128) | ✓ | - | Passkey |
| `last_balance_update` | DateTime | - | - | 最近更新余额时间 |
| `credit_limit` | Decimal | - | - | 额度（最大12位，2位小数） |
| `batch_encoding` | String(100) | - | - | 批次编号（用于分组相关记录） |
| `purchasings` | Array | - | - | 关联的采购订单ID列表 |
| `purchasings_count` | Integer | - | ✓ | 关联的采购订单数量 |
| `payments_count` | Integer | - | ✓ | 支付记录数量 |
| `payments_details` | Array | - | ✓ | 支付记录详细信息 |
| `created_at` | DateTime | - | ✓ | 创建时间（自动生成） |
| `updated_at` | DateTime | - | ✓ | 更新时间（自动更新） |

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

### 1. 获取信用卡列表

**请求**
```http
GET /api/aggregation/creditcards/
```

**查询参数**
- `card_number`: 按卡号过滤（例如：`?card_number=1234567890123456`）
- `credit_limit`: 按额度过滤（例如：`?credit_limit=100000`）
- `expiry_year`: 按过期年份过滤（例如：`?expiry_year=2025`）
- `expiry_month`: 按过期月份过滤（例如：`?expiry_month=12`）
- `search`: 搜索卡号（例如：`?search=1234`）
- `ordering`: 排序字段（例如：`?ordering=-created_at`）

**响应示例**
```json
{
  "count": 10,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "card_number": "1234567890123456",
      "alternative_name": "CREDIT-1-1",
      "expiry_month": 12,
      "expiry_year": 2025,
      "passkey": "****",
      "last_balance_update": "2025-01-10T14:00:00Z",
      "credit_limit": "100000.00",
      "batch_encoding": "BATCH-2025-01",
      "purchasings": [1, 2],
      "purchasings_count": 2,
      "payments_count": 5,
      "payments_details": [
        {
          "id": 1,
          "purchasing_order": "ORD001",
          "payment_amount": "5000.00",
          "payment_time": "2025-01-10T10:00:00Z",
          "payment_status": "completed"
        }
      ],
      "created_at": "2025-01-01T09:00:00Z",
      "updated_at": "2025-01-10T14:00:00Z"
    }
  ]
}
```

---

### 2. 创建信用卡

**请求**
```http
POST /api/aggregation/creditcards/
Content-Type: application/json
```

**请求体**
```json
{
  "card_number": "9876543210987654",
  "alternative_name": "CREDIT-2-1",
  "expiry_month": 6,
  "expiry_year": 2026,
  "passkey": "SECURE_PASS_123",
  "credit_limit": "50000.00",
  "batch_encoding": "BATCH-2025-02"
}
```

**响应示例**
```json
{
  "id": 2,
  "card_number": "9876543210987654",
  "alternative_name": "CREDIT-2-1",
  "expiry_month": 6,
  "expiry_year": 2026,
  "passkey": "SECURE_PASS_123",
  "last_balance_update": null,
  "credit_limit": "50000.00",
  "batch_encoding": "BATCH-2025-02",
  "purchasings": [],
  "purchasings_count": 0,
  "payments_count": 0,
  "payments_details": [],
  "created_at": "2025-01-12T10:00:00Z",
  "updated_at": "2025-01-12T10:00:00Z"
}
```

**状态码**
- `201 Created`: 创建成功
- `400 Bad Request`: 请求数据验证失败

**验证规则**
- `card_number`: 不能为空，必须唯一
- `expiry_month`: 必须在 1-12 之间
- `expiry_year`: 必须 >= 2000，不能是过去的年份
- `credit_limit`: 不能为负数
- 卡片不能已过期

---

### 3. 获取单个信用卡详情

**请求**
```http
GET /api/aggregation/creditcards/{id}/
```

**响应示例**
```json
{
  "id": 1,
  "card_number": "1234567890123456",
  "expiry_month": 12,
  "expiry_year": 2025,
  "passkey": "****",
  "last_balance_update": "2025-01-10T14:00:00Z",
  "credit_limit": "100000.00",
  "batch_encoding": "BATCH-2025-01",
  "purchasings": [1, 2],
  "purchasings_count": 2,
  "payments_count": 5,
  "payments_details": [
    {
      "id": 1,
      "purchasing_order": "ORD001",
      "payment_amount": "5000.00",
      "payment_time": "2025-01-10T10:00:00Z",
      "payment_status": "completed"
    },
    {
      "id": 2,
      "purchasing_order": "ORD002",
      "payment_amount": "8000.00",
      "payment_time": "2025-01-11T15:00:00Z",
      "payment_status": "completed"
    }
  ],
  "created_at": "2025-01-01T09:00:00Z",
  "updated_at": "2025-01-10T14:00:00Z"
}
```

---

### 4. 更新信用卡（部分更新）

**请求**
```http
PATCH /api/aggregation/creditcards/{id}/
Content-Type: application/json
```

**请求体示例 - 更新额度**
```json
{
  "credit_limit": "120000.00",
  "last_balance_update": "2025-01-13T10:00:00Z"
}
```

**请求体示例 - 关联采购订单（通过中间表）**

注意：信用卡通过 `CreditCardPayment` 中间表与 Purchasing 关联，应该通过 Payment API 创建关联。

**响应示例**
```json
{
  "id": 1,
  "card_number": "1234567890123456",
  "expiry_month": 12,
  "expiry_year": 2025,
  "passkey": "****",
  "last_balance_update": "2025-01-13T10:00:00Z",
  "credit_limit": "120000.00",
  "batch_encoding": "BATCH-2025-01",
  "purchasings": [1, 2],
  "purchasings_count": 2,
  "payments_count": 5,
  "payments_details": [...],
  "created_at": "2025-01-01T09:00:00Z",
  "updated_at": "2025-01-13T10:00:00Z"
}
```

---

### 5. 删除信用卡

**请求**
```http
DELETE /api/aggregation/creditcards/{id}/
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
from datetime import datetime

base_url = "http://your-domain.com/api/aggregation/creditcards/"

# 1. 获取列表（查询未过期的卡）
current_year = datetime.now().year
response = requests.get(base_url, params={"expiry_year": current_year + 1})
cards = response.json()

# 2. 创建信用卡
new_card = {
    "card_number": "5555666677778888",
    "expiry_month": 12,
    "expiry_year": 2027,
    "passkey": "SECURE_KEY",
    "credit_limit": "80000.00"
}
response = requests.post(base_url, json=new_card)
created_card = response.json()

# 3. 更新额度
card_id = created_card['id']
update_data = {
    "credit_limit": "100000.00",
    "last_balance_update": datetime.now().isoformat()
}
response = requests.patch(f"{base_url}{card_id}/", json=update_data)

# 4. 查询卡片详情（包括支付记录）
response = requests.get(f"{base_url}{card_id}/")
card_detail = response.json()
print(f"Total payments: {card_detail['payments_count']}")

# 5. 删除
response = requests.delete(f"{base_url}{card_id}/")
```

### cURL

```bash
# 获取列表
curl -X GET "http://your-domain.com/api/aggregation/creditcards/"

# 创建信用卡
curl -X POST "http://your-domain.com/api/aggregation/creditcards/" \
  -H "Content-Type: application/json" \
  -d '{
    "card_number": "5555666677778888",
    "expiry_month": 12,
    "expiry_year": 2027,
    "passkey": "SECURE_KEY",
    "credit_limit": "80000.00"
  }'

# 更新额度
curl -X PATCH "http://your-domain.com/api/aggregation/creditcards/1/" \
  -H "Content-Type: application/json" \
  -d '{"credit_limit": "100000.00"}'

# 删除信用卡
curl -X DELETE "http://your-domain.com/api/aggregation/creditcards/1/"
```

---

## 高级查询

### 过滤示例

```http
# 按卡号过滤
GET /api/aggregation/creditcards/?card_number=1234567890123456

# 按额度过滤
GET /api/aggregation/creditcards/?credit_limit=100000

# 查询即将过期的卡（2025年）
GET /api/aggregation/creditcards/?expiry_year=2025

# 搜索卡号
GET /api/aggregation/creditcards/?search=5555
```

### 排序示例

```http
# 按创建时间降序
GET /api/aggregation/creditcards/?ordering=-created_at

# 按额度降序
GET /api/aggregation/creditcards/?ordering=-credit_limit

# 按最近余额更新时间降序
GET /api/aggregation/creditcards/?ordering=-last_balance_update
```

---

## 关联关系

### Purchasing 关联（多对多，通过中间表）

信用卡与采购订单通过 `CreditCardPayment` 中间表建立多对多关系：

```python
# CreditCard ←→ CreditCardPayment ←→ Purchasing
# CreditCard.purchasings -> Purchasing (through CreditCardPayment)
# CreditCard.payments -> CreditCardPayment
# Purchasing.credit_cards -> CreditCard (反向关系)
```

**查询示例**：

```python
# 查询某张信用卡的所有支付记录
credit_card = CreditCard.objects.get(id=1)
payments = credit_card.payments.all()

# 查询某张信用卡的所有采购订单
purchasings = credit_card.purchasings.all()

# 查询某个采购订单使用的所有信用卡
purchasing = Purchasing.objects.get(id=1)
credit_cards = purchasing.credit_cards.all()
```

---

## 错误处理

### 常见错误

**400 Bad Request - 卡号重复**
```json
{
  "card_number": ["credit card with this card number already exists."]
}
```

**400 Bad Request - 卡片已过期**
```json
{
  "non_field_errors": ["Card has expired (expiry date is in the past)"]
}
```

**400 Bad Request - 过期月份无效**
```json
{
  "expiry_month": ["Expiry month must be between 1 and 12"]
}
```

**400 Bad Request - 过期年份无效**
```json
{
  "expiry_year": ["Expiry year cannot be before 2025"]
}
```

**400 Bad Request - 额度为负**
```json
{
  "credit_limit": ["Credit limit cannot be negative"]
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
CREATE TABLE credit_cards (
    id SERIAL PRIMARY KEY,
    card_number VARCHAR(19) UNIQUE NOT NULL,
    alternative_name VARCHAR(100),
    expiry_month INTEGER NOT NULL CHECK (expiry_month >= 1 AND expiry_month <= 12),
    expiry_year INTEGER NOT NULL CHECK (expiry_year >= 2000),
    passkey VARCHAR(128) NOT NULL,
    last_balance_update TIMESTAMP NULL,
    credit_limit DECIMAL(12, 2) DEFAULT 0 CHECK (credit_limit >= 0),
    batch_encoding VARCHAR(100),
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL
);

CREATE INDEX ON credit_cards(card_number);
CREATE INDEX ON credit_cards(created_at DESC);
CREATE INDEX ON credit_cards(last_balance_update);
```

---

## 业务场景示例

### 场景1：创建信用卡并进行支付

```python
# 1. 创建信用卡
new_card = {
    "card_number": "4111111111111111",
    "expiry_month": 12,
    "expiry_year": 2026,
    "passkey": "PASS123",
    "credit_limit": "50000.00"
}
response = requests.post(f"{base_url}", json=new_card)
card = response.json()

# 2. 创建支付记录（通过 CreditCardPayment API）
payment_url = "http://your-domain.com/api/aggregation/creditcard-payments/"
payment_data = {
    "credit_card": card['id'],
    "purchasing": 1,
    "payment_amount": "10000.00",
    "payment_status": "completed"
}
requests.post(payment_url, json=payment_data)

# 3. 查看卡片的所有支付记录
response = requests.get(f"{base_url}{card['id']}/")
card_detail = response.json()
print(card_detail['payments_details'])
```

### 场景2：检查即将过期的信用卡

```python
from datetime import datetime

current_date = datetime.now()
current_year = current_date.year
current_month = current_date.month

# 查询今年过期的卡
response = requests.get(base_url, params={"expiry_year": current_year})
expiring_cards = response.json()['results']

for card in expiring_cards:
    if card['expiry_month'] <= current_month + 3:  # 3个月内过期
        print(f"Warning: Card {card['card_number']} expiring soon!")
```

---

## 注意事项

1. **卡号唯一性**: `card_number` 必须唯一
2. **过期验证**: 创建和更新时会验证卡片是否已过期
3. **额度限制**: 额度不能为负数
4. **中间表关联**: 与 Purchasing 的关联通过 CreditCardPayment 中间表管理
5. **Passkey 安全**: 当前 passkey 以明文存储，生产环境建议加密
6. **支付记录**: `payments_details` 包含所有使用该卡的支付记录

---

## 相关文档

- [Credit Card Payment API 文档](./API_CREDIT_CARD_PAYMENT.md)
- [Purchasing API 文档](./API_PURCHASING.md)
- [Debit Card API 文档](./API_DEBIT_CARD.md)
- [Gift Card API 文档](./API_GIFT_CARD.md)
- [模型架构文档](../ARCHITECTURE.md)
