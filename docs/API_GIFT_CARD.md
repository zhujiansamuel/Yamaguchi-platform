# GiftCard API 文档

## 概述

GiftCard（礼品卡）API 提供了对礼品卡信息的完整 CRUD 操作支持。

**Base URL**: `/api/aggregation/giftcards/`

---

## 模型字段说明

| 字段 | 类型 | 必填 | 只读 | 说明 |
|------|------|------|------|------|
| `id` | Integer | - | ✓ | 主键ID |
| `card_number` | String(50) | ✓ | - | 卡号（唯一） |
| `alternative_name` | String(100) | - | - | 别名（方便人类管理的标签） |
| `passkey1` | String(50) | ✓ | - | Passkey 1 |
| `passkey2` | String(50) | ✓ | - | Passkey 2 |
| `balance` | Integer | ✓ | - | 余额 |
| `batch_encoding` | String(100) | - | - | 批次编号（用于分组相关记录） |
| `purchasings` | Array | - | - | 关联的采购订单ID列表 |
| `purchasings_count` | Integer | - | ✓ | 关联的采购订单数量 |
| `purchasings_details` | Array | - | ✓ | 关联的采购订单详细信息 |
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

### 1. 获取礼品卡列表

**请求**
```http
GET /api/aggregation/giftcards/
```

**查询参数**
- `card_number`: 按卡号过滤（例如：`?card_number=CARD123`）
- `balance`: 按余额过滤（例如：`?balance=1000`）
- `search`: 搜索卡号（例如：`?search=CARD`）
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
      "card_number": "CARD20250110001",
      "alternative_name": "CARD-1-1",
      "passkey1": "PASS1234",
      "passkey2": "KEY5678",
      "balance": 10000,
      "batch_encoding": "BATCH-2025-01",
      "purchasings": [1, 2],
      "purchasings_count": 2,
      "purchasings_details": [
        {
          "id": 1,
          "uuid": "1a2b3c4d...",
          "order_number": "ORD001",
          "delivery_status": "delivered"
        },
        {
          "id": 2,
          "uuid": "2b3c4d5e...",
          "order_number": "ORD002",
          "delivery_status": "in_delivery"
        }
      ],
      "created_at": "2025-01-10T09:00:00Z",
      "updated_at": "2025-01-12T14:00:00Z"
    }
  ]
}
```

---

### 2. 创建礼品卡

**请求**
```http
POST /api/aggregation/giftcards/
Content-Type: application/json
```

**请求体**
```json
{
  "card_number": "CARD20250115001",
  "alternative_name": "CARD-2-1",
  "passkey1": "NEWPASS1",
  "passkey2": "NEWKEY2",
  "balance": 5000,
  "batch_encoding": "BATCH-2025-01",
  "purchasings": []
}
```

**响应示例**
```json
{
  "id": 2,
  "card_number": "CARD20250115001",
  "alternative_name": "CARD-2-1",
  "passkey1": "NEWPASS1",
  "passkey2": "NEWKEY2",
  "balance": 5000,
  "batch_encoding": "BATCH-2025-01",
  "purchasings": [],
  "purchasings_count": 0,
  "purchasings_details": [],
  "created_at": "2025-01-12T10:00:00Z",
  "updated_at": "2025-01-12T10:00:00Z"
}
```

**状态码**
- `201 Created`: 创建成功
- `400 Bad Request`: 请求数据验证失败

**验证规则**
- `card_number`: 不能为空，必须唯一
- `balance`: 不能为负数

---

### 3. 获取单个礼品卡详情

**请求**
```http
GET /api/aggregation/giftcards/{id}/
```

**响应示例**
```json
{
  "id": 1,
  "card_number": "CARD20250110001",
  "passkey1": "PASS1234",
  "passkey2": "KEY5678",
  "balance": 10000,
  "batch_encoding": "BATCH-2025-01",
  "purchasings": [1, 2],
  "purchasings_count": 2,
  "purchasings_details": [
    {
      "id": 1,
      "uuid": "1a2b3c4d...",
      "order_number": "ORD001",
      "delivery_status": "delivered"
    },
    {
      "id": 2,
      "uuid": "2b3c4d5e...",
      "order_number": "ORD002",
      "delivery_status": "in_delivery"
    }
  ],
  "created_at": "2025-01-10T09:00:00Z",
  "updated_at": "2025-01-12T14:00:00Z"
}
```

---

### 4. 更新礼品卡（部分更新）

**请求**
```http
PATCH /api/aggregation/giftcards/{id}/
Content-Type: application/json
```

**请求体示例 - 更新余额**
```json
{
  "balance": 8000
}
```

**请求体示例 - 关联采购订单**
```json
{
  "purchasings": [1, 2, 3]
}
```

**响应示例**
```json
{
  "id": 1,
  "card_number": "CARD20250110001",
  "passkey1": "PASS1234",
  "passkey2": "KEY5678",
  "balance": 8000,
  "batch_encoding": "BATCH-2025-01",
  "purchasings": [1, 2, 3],
  "purchasings_count": 3,
  "purchasings_details": [
    {
      "id": 1,
      "uuid": "1a2b3c4d...",
      "order_number": "ORD001",
      "delivery_status": "delivered"
    },
    {
      "id": 2,
      "uuid": "2b3c4d5e...",
      "order_number": "ORD002",
      "delivery_status": "in_delivery"
    },
    {
      "id": 3,
      "uuid": "3c4d5e6f...",
      "order_number": "ORD003",
      "delivery_status": "pending_confirmation"
    }
  ],
  "created_at": "2025-01-10T09:00:00Z",
  "updated_at": "2025-01-13T11:00:00Z"
}
```

---

### 5. 删除礼品卡

**请求**
```http
DELETE /api/aggregation/giftcards/{id}/
```

**响应**
```http
HTTP/1.1 204 No Content
```

**状态码**
- `204 No Content`: 删除成功
- `404 Not Found`: 礼品卡不存在

---

## 使用示例

### Python (requests)

```python
import requests

base_url = "http://your-domain.com/api/aggregation/giftcards/"

# 1. 获取列表
response = requests.get(base_url)
cards = response.json()

# 2. 创建礼品卡
new_card = {
    "card_number": "CARD20250120001",
    "passkey1": "TESTPASS1",
    "passkey2": "TESTKEY2",
    "balance": 15000,
    "batch_encoding": "BATCH-2025-01"
}
response = requests.post(base_url, json=new_card)
created_card = response.json()

# 3. 更新余额
card_id = created_card['id']
update_data = {"balance": 12000}
response = requests.patch(f"{base_url}{card_id}/", json=update_data)

# 4. 关联采购订单
update_data = {"purchasings": [1, 2]}
response = requests.patch(f"{base_url}{card_id}/", json=update_data)

# 5. 删除
response = requests.delete(f"{base_url}{card_id}/")
```

### cURL

```bash
# 获取列表
curl -X GET "http://your-domain.com/api/aggregation/giftcards/"

# 创建礼品卡
curl -X POST "http://your-domain.com/api/aggregation/giftcards/" \
  -H "Content-Type: application/json" \
  -d '{
    "card_number": "CARD20250120001",
    "passkey1": "TESTPASS1",
    "passkey2": "TESTKEY2",
    "balance": 15000,
    "batch_encoding": "BATCH-2025-01"
  }'

# 更新余额
curl -X PATCH "http://your-domain.com/api/aggregation/giftcards/1/" \
  -H "Content-Type: application/json" \
  -d '{"balance": 12000}'

# 删除礼品卡
curl -X DELETE "http://your-domain.com/api/aggregation/giftcards/1/"
```

---

## 高级查询

### 过滤示例

```http
# 按卡号过滤
GET /api/aggregation/giftcards/?card_number=CARD20250110001

# 按余额过滤
GET /api/aggregation/giftcards/?balance=10000

# 搜索卡号
GET /api/aggregation/giftcards/?search=CARD2025
```

### 排序示例

```http
# 按创建时间降序
GET /api/aggregation/giftcards/?ordering=-created_at

# 按余额升序
GET /api/aggregation/giftcards/?ordering=balance

# 按余额降序
GET /api/aggregation/giftcards/?ordering=-balance
```

---

## 关联关系

### Purchasing 关联（多对多）

礼品卡与采购订单是多对多关系：

```python
# GiftCard ←→ Purchasing (ManyToMany)
# GiftCard.purchasings -> Purchasing
# Purchasing.gift_cards -> GiftCard (反向关系)
```

**查询示例**：

```python
# 查询某个礼品卡的所有采购订单
gift_card = GiftCard.objects.get(id=1)
purchasings = gift_card.purchasings.all()

# 查询某个采购订单使用的所有礼品卡
purchasing = Purchasing.objects.get(id=1)
gift_cards = purchasing.gift_cards.all()
```

---

## 错误处理

### 常见错误

**400 Bad Request - 卡号重复**
```json
{
  "card_number": ["gift card with this card number already exists."]
}
```

**400 Bad Request - 余额为负**
```json
{
  "balance": ["Balance cannot be negative"]
}
```

**400 Bad Request - 卡号为空**
```json
{
  "card_number": ["Card number cannot be empty"]
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
CREATE TABLE gift_cards (
    id SERIAL PRIMARY KEY,
    card_number VARCHAR(50) UNIQUE NOT NULL,
    passkey1 VARCHAR(50) NOT NULL,
    passkey2 VARCHAR(50) NOT NULL,
    balance INTEGER NOT NULL,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL
);

-- 多对多关系表
CREATE TABLE gift_cards_purchasings (
    id SERIAL PRIMARY KEY,
    giftcard_id INTEGER REFERENCES gift_cards(id),
    purchasing_id INTEGER REFERENCES purchasing(id)
);

CREATE INDEX ON gift_cards(card_number);
CREATE INDEX ON gift_cards(created_at DESC);
```

---

## 业务场景示例

### 场景1：创建新礼品卡并关联到订单

```python
# 1. 创建礼品卡
new_card = {
    "card_number": "GIFT2025001",
    "passkey1": "PASS123",
    "passkey2": "KEY456",
    "balance": 20000,
    "purchasings": []
}
response = requests.post(f"{base_url}", json=new_card)
card = response.json()

# 2. 将礼品卡关联到采购订单
update_data = {"purchasings": [1, 2]}
requests.patch(f"{base_url}{card['id']}/", json=update_data)
```

### 场景2：使用礼品卡后更新余额

```python
# 假设订单使用了 5000 元
current_balance = 20000
used_amount = 5000
new_balance = current_balance - used_amount

update_data = {"balance": new_balance}
requests.patch(f"{base_url}{card_id}/", json=update_data)
```

---

## 注意事项

1. **卡号唯一性**: `card_number` 必须唯一
2. **余额限制**: 余额不能为负数
3. **多对多关系**: 一张礼品卡可以用于多个采购订单
4. **Passkey 安全**: 当前 passkey 以明文存储，生产环境建议加密
5. **余额管理**: 系统不自动扣减余额，需要手动更新

---

## 相关文档

- [Purchasing API 文档](./API_PURCHASING.md)
- [Debit Card API 文档](./API_DEBIT_CARD.md)
- [Credit Card API 文档](./API_CREDIT_CARD.md)
- [模型架构文档](../ARCHITECTURE.md)
