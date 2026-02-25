# Purchasing API 文档

## 概述

Purchasing（采购订单）API 提供了对采购订单和配送信息的完整 CRUD 操作支持。

**Base URL**: `/api/aggregation/purchasing/`

---

## 模型字段说明

| 字段 | 类型 | 必填 | 只读 | 说明 |
|------|------|------|------|------|
| `id` | Integer | - | ✓ | 主键ID |
| `uuid` | String(59) | - | ✓ | 全局唯一标识符（自动生成） |
| `order_number` | String(50) | - | - | 订单号（可为空，允许重复） |
| `official_account` | Integer | - | - | 关联的官方账号ID |
| `official_account_display` | Object | - | ✓ | 官方账号详细信息 |
| `batch_encoding` | String(50) | - | - | 批次编码 |
| `batch_level_1` | String(50) | - | - | 批次层级1 |
| `batch_level_2` | String(50) | - | - | 批次层级2 |
| `batch_level_3` | String(50) | - | - | 批次层级3 |
| `created_at` | DateTime | - | ✓ | 创建时间（自动生成） |
| `confirmed_at` | DateTime | - | - | 认可时间 |
| `shipped_at` | DateTime | - | - | 发送时间 |
| `estimated_website_arrival_date` | Date | - | - | 官网到达预计时间 |
| `estimated_website_arrival_date_2` | Date | - | - | 官网到达预计时间2 |
| `tracking_number` | String(50) | - | - | 邮寄单号 |
| `estimated_delivery_date` | Date | - | - | 邮寄送达预计时间 |
| `shipping_method` | String(100) | - | - | 快递方式 |
| `official_query_url` | String(500) | - | - | 官方查询URL |
| `delivery_status` | String(30) | - | - | 送达状态 |
| `delivery_status_display` | String | - | ✓ | 送达状态显示名称 |
| `latest_delivery_status` | String(10) | - | - | 最新送达状态（日文，最多10个字符） |
| `delivery_status_query_time` | DateTime | - | - | 配送状态查询时间 |
| `delivery_status_query_source` | String(100) | - | - | 配送状态查询来源 |
| `last_info_updated_at` | DateTime | - | - | 最后信息更新时间 |
| `account_used` | String(50) | - | - | 使用账号 |
| `payment_method` | Text | - | - | 使用付款方式或未匹配的支付信息 |
| `inventory_count` | Integer | - | ✓ | 关联的库存数量 |
| `inventory_items` | Array | - | ✓ | 关联的库存项目详情列表 |
| `is_locked` | Boolean | - | ✓ | 是否被 worker 锁定 |
| `locked_at` | DateTime | - | ✓ | 锁定时间 |
| `locked_by_worker` | String(50) | - | ✓ | 锁定该记录的 worker |
| `is_deleted` | Boolean | - | ✓ | 软删除标记 |
| `creation_source` | String(200) | - | - | 创建来源 |
| `updated_at` | DateTime | - | ✓ | 更新时间（自动更新） |

---

## 枚举值

### 送达状态 (delivery_status)

| 值 | 显示名称 | 说明 |
|----|----------|------|
| `pending_confirmation` | 等待确认 | 订单等待确认 |
| `shipped` | 已发送 | 订单已发送 |
| `in_delivery` | 配送中 | 订单配送中 |
| `delivered` | 已送达 | 订单已送达 |

### 付款方式 (payment_method)

`payment_method` 为自由文本字段，可记录支付方式或未匹配的支付卡信息，不做枚举限制。

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

### 1. 获取采购订单列表

**请求**
```http
GET /api/aggregation/purchasing/
```

**查询参数**
- `delivery_status`: 按送达状态过滤（例如：`?delivery_status=shipped`）
- `payment_method`: 按付款方式过滤（例如：`?payment_method=credit_card`）
- `order_number`: 按订单号过滤（例如：`?order_number=ORD123`）
- `official_account`: 按官方账号ID过滤（例如：`?official_account=1`）
- `tracking_number`: 按邮寄单号过滤（例如：`?tracking_number=TRACK123`）
- `batch_encoding`: 按批次编码过滤（例如：`?batch_encoding=BATCH-2025`）
- `batch_level_1`: 按批次层级1过滤（例如：`?batch_level_1=LEVEL1`）
- `batch_level_2`: 按批次层级2过滤（例如：`?batch_level_2=LEVEL2`）
- `batch_level_3`: 按批次层级3过滤（例如：`?batch_level_3=LEVEL3`）
- `creation_source`: 按创建来源过滤（例如：`?creation_source=API`）
- `is_locked`: 按锁定状态过滤（例如：`?is_locked=true`）
- `is_deleted`: 按软删除状态过滤（例如：`?is_deleted=false`）
- `search`: 搜索UUID、订单号、邮寄单号、使用账号或批次编码（例如：`?search=ORD123`）
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
      "uuid": "1a2b3c4d-5e6f7a8b-9c0d1e2f-3a4b5c6d-7e8f9a0b-1c2d3e4f...",
      "order_number": "ORD20250110001",
      "official_account": 1,
      "official_account_display": {
        "id": 1,
        "account_id": "ACC001",
        "email": "user@example.com",
        "name": "张三"
      },
      "batch_encoding": "BATCH-2025-01",
      "batch_level_1": "LEVEL-1",
      "batch_level_2": "LEVEL-2",
      "batch_level_3": "LEVEL-3",
      "created_at": "2025-01-10T09:00:00Z",
      "confirmed_at": "2025-01-10T10:00:00Z",
      "shipped_at": "2025-01-11T08:00:00Z",
      "estimated_website_arrival_date": "2025-01-15",
      "estimated_website_arrival_date_2": null,
      "tracking_number": "TRACK123456",
      "estimated_delivery_date": "2025-01-15",
      "shipping_method": "DHL",
      "official_query_url": "https://example.com/track/TRACK123456",
      "delivery_status": "in_delivery",
      "delivery_status_display": "配送中",
      "latest_delivery_status": "配送中",
      "delivery_status_query_time": "2025-01-12T13:30:00Z",
      "delivery_status_query_source": "yamato_tracking",
      "last_info_updated_at": "2025-01-12T14:00:00Z",
      "account_used": "user@example.com",
      "payment_method": "credit_card",
      "inventory_count": 3,
      "inventory_items": [
        {
          "id": 1,
          "uuid": "abc123...",
          "flag": "FLAG001",
          "status": "in_transit",
          "product_type": "iPhone",
          "created_at": "2025-01-10T09:30:00Z"
        },
        {
          "id": 2,
          "uuid": "def456...",
          "flag": "FLAG002",
          "status": "arrived",
          "product_type": "iPhone",
          "created_at": "2025-01-10T09:31:00Z"
        },
        {
          "id": 3,
          "uuid": "ghi789...",
          "flag": "FLAG003",
          "status": "in_transit",
          "product_type": "iPad",
          "created_at": "2025-01-10T09:32:00Z"
        }
      ],
      "is_locked": false,
      "locked_at": null,
      "locked_by_worker": "",
      "is_deleted": false,
      "creation_source": "api",
      "updated_at": "2025-01-12T14:00:00Z"
    }
  ]
}
```

---

### 2. 创建采购订单

**请求**
```http
POST /api/aggregation/purchasing/
Content-Type: application/json
```

**请求体**
```json
{
  "order_number": "ORD20250115001",
  "official_account": 1,
  "batch_encoding": "BATCH-2025-01",
  "estimated_website_arrival_date": "2025-01-20",
  "shipping_method": "Express",
  "official_query_url": "https://example.com/track/order",
  "delivery_status": "pending_confirmation",
  "payment_method": "credit_card",
  "account_used": "user@example.com"
}
```

**响应示例**
```json
{
  "id": 2,
  "uuid": "2b3c4d5e-6f7a8b9c-0d1e2f3a-4b5c6d7e-8f9a0b1c-2d3e4f5a...",
  "order_number": "ORD20250115001",
  "official_account": 1,
  "official_account_display": {
    "id": 1,
    "account_id": "ACC001",
    "email": "user@example.com",
    "name": "张三"
  },
  "batch_encoding": "BATCH-2025-01",
  "batch_level_1": "",
  "batch_level_2": "",
  "batch_level_3": "",
  "created_at": "2025-01-12T10:00:00Z",
  "confirmed_at": null,
  "shipped_at": null,
  "estimated_website_arrival_date": "2025-01-20",
  "estimated_website_arrival_date_2": null,
  "tracking_number": "",
  "estimated_delivery_date": null,
  "shipping_method": "Express",
  "official_query_url": "https://example.com/track/order",
  "delivery_status": "pending_confirmation",
  "delivery_status_display": "等待确认",
  "latest_delivery_status": null,
  "delivery_status_query_time": null,
  "delivery_status_query_source": null,
  "last_info_updated_at": null,
  "account_used": "user@example.com",
  "payment_method": "credit_card",
  "inventory_count": 0,
  "inventory_items": [],
  "is_locked": false,
  "locked_at": null,
  "locked_by_worker": "",
  "is_deleted": false,
  "creation_source": null,
  "updated_at": "2025-01-12T10:00:00Z"
}
```

**状态码**
- `201 Created`: 创建成功
- `400 Bad Request`: 请求数据验证失败

**验证规则**
- `order_number`: 可选，允许为空（不会自动生成）

---

### 3. 获取单个采购订单详情

**请求**
```http
GET /api/aggregation/purchasing/{id}/
```

**响应示例**
```json
{
  "id": 1,
  "uuid": "1a2b3c4d-5e6f7a8b-9c0d1e2f-3a4b5c6d-7e8f9a0b-1c2d3e4f...",
  "order_number": "ORD20250110001",
  "official_account": 1,
  "official_account_display": {
    "id": 1,
    "account_id": "ACC001",
    "email": "user@example.com",
    "name": "张三"
  },
  "batch_encoding": "BATCH-2025-01",
  "batch_level_1": "LEVEL-1",
  "batch_level_2": "LEVEL-2",
  "batch_level_3": "LEVEL-3",
  "created_at": "2025-01-10T09:00:00Z",
  "confirmed_at": "2025-01-10T10:00:00Z",
  "shipped_at": "2025-01-11T08:00:00Z",
  "estimated_website_arrival_date": "2025-01-15",
  "estimated_website_arrival_date_2": null,
  "tracking_number": "TRACK123456",
  "estimated_delivery_date": "2025-01-15",
  "shipping_method": "DHL",
  "official_query_url": "https://example.com/track/TRACK123456",
  "delivery_status": "in_delivery",
  "delivery_status_display": "配送中",
  "latest_delivery_status": "配送中",
  "delivery_status_query_time": "2025-01-12T13:30:00Z",
  "delivery_status_query_source": "yamato_tracking",
  "last_info_updated_at": "2025-01-12T14:00:00Z",
  "account_used": "user@example.com",
  "payment_method": "credit_card",
  "inventory_count": 3,
  "inventory_items": [
    {
      "id": 1,
      "uuid": "abc123...",
      "flag": "FLAG001",
      "status": "in_transit",
      "product_type": "iPhone",
      "created_at": "2025-01-10T09:30:00Z"
    },
    {
      "id": 2,
      "uuid": "def456...",
      "flag": "FLAG002",
      "status": "arrived",
      "product_type": "iPhone",
      "created_at": "2025-01-10T09:31:00Z"
    },
    {
      "id": 3,
      "uuid": "ghi789...",
      "flag": "FLAG003",
      "status": "in_transit",
      "product_type": "iPad",
      "created_at": "2025-01-10T09:32:00Z"
    }
  ],
  "is_locked": false,
  "locked_at": null,
  "locked_by_worker": "",
  "is_deleted": false,
  "creation_source": "api",
  "updated_at": "2025-01-12T14:00:00Z"
}
```

---

### 4. 更新采购订单（部分更新）

**请求**
```http
PATCH /api/aggregation/purchasing/{id}/
Content-Type: application/json
```

**请求体示例 - 更新配送状态**
```json
{
  "delivery_status": "delivered",
  "last_info_updated_at": "2025-01-15T16:00:00Z"
}
```

**响应示例**
```json
{
  "id": 1,
  "uuid": "1a2b3c4d-5e6f7a8b-9c0d1e2f-3a4b5c6d-7e8f9a0b-1c2d3e4f...",
  "order_number": "ORD20250110001",
  "official_account": 1,
  "official_account_display": {
    "id": 1,
    "account_id": "ACC001",
    "email": "user@example.com",
    "name": "张三"
  },
  "batch_encoding": "BATCH-2025-01",
  "batch_level_1": "LEVEL-1",
  "batch_level_2": "LEVEL-2",
  "batch_level_3": "LEVEL-3",
  "created_at": "2025-01-10T09:00:00Z",
  "confirmed_at": "2025-01-10T10:00:00Z",
  "shipped_at": "2025-01-11T08:00:00Z",
  "estimated_website_arrival_date": "2025-01-15",
  "estimated_website_arrival_date_2": null,
  "tracking_number": "TRACK123456",
  "estimated_delivery_date": "2025-01-15",
  "shipping_method": "DHL",
  "official_query_url": "https://example.com/track/TRACK123456",
  "delivery_status": "delivered",
  "delivery_status_display": "已送达",
  "latest_delivery_status": "已送达",
  "delivery_status_query_time": "2025-01-15T15:45:00Z",
  "delivery_status_query_source": "yamato_tracking",
  "last_info_updated_at": "2025-01-15T16:00:00Z",
  "account_used": "user@example.com",
  "payment_method": "credit_card",
  "inventory_count": 3,
  "inventory_items": [
    {
      "id": 1,
      "uuid": "abc123...",
      "flag": "FLAG001",
      "status": "arrived",
      "product_type": "iPhone",
      "created_at": "2025-01-10T09:30:00Z"
    },
    {
      "id": 2,
      "uuid": "def456...",
      "flag": "FLAG002",
      "status": "arrived",
      "product_type": "iPhone",
      "created_at": "2025-01-10T09:31:00Z"
    },
    {
      "id": 3,
      "uuid": "ghi789...",
      "flag": "FLAG003",
      "status": "arrived",
      "product_type": "iPad",
      "created_at": "2025-01-10T09:32:00Z"
    }
  ],
  "is_locked": false,
  "locked_at": null,
  "locked_by_worker": "",
  "is_deleted": false,
  "creation_source": "api",
  "updated_at": "2025-01-15T16:00:00Z"
}
```

---

### 5. 删除采购订单

**请求**
```http
DELETE /api/aggregation/purchasing/{id}/
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

base_url = "http://your-domain.com/api/aggregation/purchasing/"

# 1. 获取列表（按状态过滤）
response = requests.get(base_url, params={"delivery_status": "in_delivery"})
orders = response.json()

# 2. 创建采购订单
new_order = {
    "order_number": "ORD20250120001",
    "official_account": 1,
    "delivery_status": "pending_confirmation",
    "payment_method": "credit_card"
}
response = requests.post(base_url, json=new_order)
created_order = response.json()

# 3. 更新配送状态
update_data = {
    "delivery_status": "shipped",
    "shipped_at": "2025-01-20T09:00:00Z",
    "tracking_number": "TRACK789"
}
response = requests.patch(f"{base_url}{created_order['id']}/", json=update_data)

# 4. 搜索订单
response = requests.get(base_url, params={"search": "ORD2025"})
```

---

## 新增功能：订单关键库存数量

### inventory_count 字段

`inventory_count` 字段提供了与该采购订单关联的库存项目总数量。这是一个只读字段，由系统自动计算。

**特性：**
- 类型：Integer
- 只读：是
- 描述：统计通过 `Inventory.source2` 字段关联到此采购订单的所有库存项目数量

**示例：**
```json
{
  "inventory_count": 3
}
```

### inventory_items 字段

`inventory_items` 字段提供了与该采购订单关联的所有库存项目的详细信息列表。这是一个只读字段，包含每个库存项目的关键信息。

**特性：**
- 类型：Array of Objects
- 只读：是
- 描述：包含所有关联库存项目的详细信息

**每个库存项目对象包含：**
- `id`: 库存项目ID
- `uuid`: 库存项目UUID
- `flag`: 库存标识
- `status`: 库存状态（in_transit/arrived/out_of_stock/abnormal）
- `product_type`: 产品类型（iPhone/iPad/null）
- `created_at`: 库存创建时间

**示例：**
```json
{
  "inventory_items": [
    {
      "id": 1,
      "uuid": "abc123-def456-...",
      "flag": "FLAG001",
      "status": "in_transit",
      "product_type": "iPhone",
      "created_at": "2025-01-10T09:30:00Z"
    },
    {
      "id": 2,
      "uuid": "def456-ghi789-...",
      "flag": "FLAG002",
      "status": "arrived",
      "product_type": "iPad",
      "created_at": "2025-01-10T09:31:00Z"
    }
  ]
}
```

### 使用场景

1. **订单管理**: 快速查看每个采购订单关联的库存数量
2. **库存追踪**: 查看订单下所有库存项目的状态和详情
3. **数据分析**: 统计和分析采购订单与库存的关系

### Python 使用示例

```python
import requests

# 获取采购订单详情（包含库存信息）
response = requests.get("http://your-domain.com/api/aggregation/purchasing/1/")
order = response.json()

# 查看库存数量
print(f"订单 {order['order_number']} 共有 {order['inventory_count']} 件库存")

# 遍历所有库存项目
for item in order['inventory_items']:
    print(f"库存 {item['uuid'][:8]}... - {item['status']} - {item['product_type']}")
```

---

## 关联关系

### OfficialAccount 关联

```python
# Purchasing.official_account -> OfficialAccount
# OfficialAccount.purchasing_orders -> Purchasing (反向关系)
```

### Inventory 关联

```python
# Inventory.source2 -> Purchasing
# Purchasing.purchasing_inventories -> Inventory (反向关系)
```

### 支付方式关联

```python
# GiftCard ←→ Purchasing (ManyToMany)
# DebitCard ←→ Purchasing (through DebitCardPayment)
# CreditCard ←→ Purchasing (through CreditCardPayment)
```

---

## 数据库表结构

```sql
CREATE TABLE purchasing (
    id SERIAL PRIMARY KEY,
    uuid VARCHAR(59) UNIQUE NOT NULL,
    order_number VARCHAR(50) NULL,
    official_account_id INTEGER REFERENCES official_accounts(id),
    batch_encoding VARCHAR(50) NOT NULL,
    batch_level_1 VARCHAR(50) NOT NULL,
    batch_level_2 VARCHAR(50) NOT NULL,
    batch_level_3 VARCHAR(50) NOT NULL,
    account_used VARCHAR(50) NOT NULL,
    payment_method TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL,
    confirmed_at TIMESTAMP NULL,
    shipped_at TIMESTAMP NULL,
    estimated_website_arrival_date DATE NULL,
    estimated_website_arrival_date_2 DATE NULL,
    tracking_number VARCHAR(50) NOT NULL,
    estimated_delivery_date DATE NULL,
    shipping_method VARCHAR(100) NULL,
    official_query_url VARCHAR(500) NULL,
    delivery_status VARCHAR(30) DEFAULT 'pending_confirmation',
    latest_delivery_status VARCHAR(10) NULL,
    delivery_status_query_time TIMESTAMP NULL,
    delivery_status_query_source VARCHAR(100) NULL,
    last_info_updated_at TIMESTAMP NULL,
    updated_at TIMESTAMP NOT NULL,
    is_locked BOOLEAN DEFAULT FALSE,
    locked_at TIMESTAMP NULL,
    locked_by_worker VARCHAR(50) NOT NULL,
    is_deleted BOOLEAN DEFAULT FALSE,
    creation_source VARCHAR(200) NULL
);

CREATE INDEX ON purchasing(uuid);
CREATE INDEX ON purchasing(order_number);
CREATE INDEX ON purchasing(delivery_status);
CREATE INDEX ON purchasing(created_at);
CREATE INDEX ON purchasing(shipped_at DESC);
CREATE INDEX ON purchasing(tracking_number);
CREATE INDEX ON purchasing(is_locked);
CREATE INDEX ON purchasing(batch_encoding);
```

---

## 注意事项

1. **UUID 唯一性**: UUID 自动生成，确保全局唯一
2. **订单号可重复**: `order_number` 允许为空或重复（非强制唯一）
3. **官方账号关联**: 支持可选的官方账号关联
4. **删除限制**: 如果订单已关联库存（source2），删除时会受到 `PROTECT` 约束保护
5. **支付方式**: 订单可以与多种支付方式（礼品卡、借记卡、信用卡）关联

---

## 相关文档

- [Official Account API 文档](./API_OFFICIAL_ACCOUNT.md)
- [Inventory API 文档](./API_INVENTORY.md)
- [Gift Card API 文档](./API_GIFT_CARD.md)
- [Debit Card API 文档](./API_DEBIT_CARD.md)
- [Credit Card API 文档](./API_CREDIT_CARD.md)
- [模型架构文档](../ARCHITECTURE.md)
