# Debit Card API Documentation

## 概要

Debit Card（借记卡）模型的完整 REST API，支持 CRUD 操作。此模型用于管理借记卡信息，与 Purchasing（采购订单）模型为多对多关系（通过 DebitCardPayment 中间表）。

## 模型字段

### DebitCard（借记卡）

| 字段 | 类型 | 必填 | 说明 | 示例 |
|------|------|------|------|------|
| `id` | Integer | 自动 | 主键ID | `1` |
| `card_number` | String(19) | ✓ | 卡号（唯一） | `1234567890123456` |
| `alternative_name` | String(100) | ✗ | 别名（方便人类管理的标签） | `DEBIT-1-1` |
| `expiry_month` | Integer | ✓ | 有效期月份（1-12） | `12` |
| `expiry_year` | Integer | ✓ | 有效期年份（≥2000） | `2025` |
| `passkey` | String(128) | ✓ | 访问密钥 | `key123456` |
| `last_balance_update` | DateTime | ✗ | 最近更新余额时间 | `2025-12-28T06:00:00Z` |
| `balance` | Decimal(12,2) | ✓ | 余额（默认0） | `1000.50` |
| `batch_encoding` | String(100) | ✗ | 批次编号（用于分组相关记录） | `BATCH-2025-01` |
| `purchasings` | ManyToMany | ✗ | 关联的采购订单 | `[1, 2, 3]` |
| `purchasings_count` | Integer | 只读 | 关联的采购订单数量 | `3` |
| `payments_count` | Integer | 只读 | 支付记录数量 | `5` |
| `payments_details` | Array | 只读 | 支付详情列表 | 见下文 |
| `created_at` | DateTime | 自动 | 创建时间 | `2025-12-28T06:00:00Z` |
| `updated_at` | DateTime | 自动 | 更新时间 | `2025-12-28T06:00:00Z` |

### DebitCardPayment（借记卡支付中间表）

| 字段 | 类型 | 必填 | 说明 | 示例 |
|------|------|------|------|------|
| `id` | Integer | 自动 | 主键ID | `1` |
| `debit_card` | ForeignKey | ✗ | 借记卡（SET_NULL） | `1` |
| `debit_card_number` | String | 只读 | 借记卡卡号 | `1234567890123456` |
| `purchasing` | ForeignKey | ✗ | 采购订单（SET_NULL） | `1` |
| `purchasing_order_number` | String | 只读 | 采购订单号 | `ORD12345` |
| `payment_amount` | Decimal(12,2) | ✓ | 支付金额（>0） | `500.00` |
| `payment_time` | DateTime | 自动 | 支付时间 | `2025-12-28T06:00:00Z` |
| `payment_status` | String(20) | ✓ | 支付状态（默认pending） | `completed` |
| `created_at` | DateTime | 自动 | 创建时间 | `2025-12-28T06:00:00Z` |
| `updated_at` | DateTime | 自动 | 更新时间 | `2025-12-28T06:00:00Z` |

#### payment_status 选项
- `pending`: 待处理
- `completed`: 已完成
- `failed`: 失败
- `refunded`: 已退款

## 数据验证

### DebitCard 验证
- `card_number`: 不能为空，必须唯一
- `expiry_month`: 必须在1-12之间
- `expiry_year`: 必须≥当前年份
- `expiry_date`: 不能是过去的日期（年月组合）
- `balance`: 不能为负数

### DebitCardPayment 验证
- `payment_amount`: 必须大于0


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

### DebitCard 端点

#### 基础 URL
```
http://localhost:8000/api/aggregation/debitcards/
```

#### 1. 列出所有 Debit Card
```http
GET /api/aggregation/debitcards/
```

**响应示例:**
```json
{
    "count": 2,
    "next": null,
    "previous": null,
    "results": [
        {
            "id": 1,
            "card_number": "1234567890123456",
            "alternative_name": "DEBIT-1-1",
            "expiry_month": 12,
            "expiry_year": 2025,
            "passkey": "key123456",
            "last_balance_update": "2025-12-28T06:00:00Z",
            "balance": "1000.50",
            "batch_encoding": "BATCH-2025-01",
            "purchasings": [1, 2],
            "purchasings_count": 2,
            "payments_count": 3,
            "payments_details": [
                {
                    "id": 1,
                    "purchasing_order": "ORD12345",
                    "payment_amount": "500.00",
                    "payment_time": "2025-12-28T06:00:00Z",
                    "payment_status": "completed"
                },
                {
                    "id": 2,
                    "purchasing_order": "ORD67890",
                    "payment_amount": "300.50",
                    "payment_time": "2025-12-28T07:00:00Z",
                    "payment_status": "completed"
                }
            ],
            "created_at": "2025-12-28T05:00:00Z",
            "updated_at": "2025-12-28T06:00:00Z"
        }
    ]
}
```

#### 2. 创建新 Debit Card
```http
POST /api/aggregation/debitcards/
Content-Type: application/json
```

**请求体:**
```json
{
    "card_number": "1234567890123456",
    "alternative_name": "DEBIT-1-1",
    "expiry_month": 12,
    "expiry_year": 2025,
    "passkey": "key123456",
    "balance": "1000.50",
    "batch_encoding": "BATCH-2025-01",
    "last_balance_update": "2025-12-28T06:00:00Z"
}
```

**响应示例:**
```json
{
    "id": 1,
    "card_number": "1234567890123456",
    "alternative_name": "DEBIT-1-1",
    "expiry_month": 12,
    "expiry_year": 2025,
    "passkey": "key123456",
    "last_balance_update": "2025-12-28T06:00:00Z",
    "balance": "1000.50",
    "batch_encoding": "BATCH-2025-01",
    "purchasings": [],
    "purchasings_count": 0,
    "payments_count": 0,
    "payments_details": [],
    "created_at": "2025-12-28T06:00:00Z",
    "updated_at": "2025-12-28T06:00:00Z"
}
```

#### 3. 获取特定 Debit Card
```http
GET /api/aggregation/debitcards/{id}/
```

**响应示例:** 同创建响应

#### 4. 更新 Debit Card
```http
PUT /api/aggregation/debitcards/{id}/
Content-Type: application/json
```

**请求体:** 同创建请求

**PATCH 请求（部分更新）:**
```http
PATCH /api/aggregation/debitcards/{id}/
Content-Type: application/json
```

```json
{
    "balance": "1500.00",
    "last_balance_update": "2025-12-29T06:00:00Z"
}
```

#### 5. 删除 Debit Card
```http
DELETE /api/aggregation/debitcards/{id}/
```

**响应:** 204 No Content

---

### DebitCardPayment 端点

#### 基础 URL
```
http://localhost:8000/api/aggregation/debitcard-payments/
```

#### 1. 列出所有 Debit Card Payment
```http
GET /api/aggregation/debitcard-payments/
```

**响应示例:**
```json
{
    "count": 2,
    "next": null,
    "previous": null,
    "results": [
        {
            "id": 1,
            "debit_card": 1,
            "debit_card_number": "1234567890123456",
            "purchasing": 1,
            "purchasing_order_number": "ORD12345",
            "payment_amount": "500.00",
            "payment_time": "2025-12-28T06:00:00Z",
            "payment_status": "completed",
            "created_at": "2025-12-28T06:00:00Z",
            "updated_at": "2025-12-28T06:00:00Z"
        }
    ]
}
```

#### 2. 创建新 Debit Card Payment
```http
POST /api/aggregation/debitcard-payments/
Content-Type: application/json
```

**请求体:**
```json
{
    "debit_card": 1,
    "purchasing": 1,
    "payment_amount": "500.00",
    "payment_status": "pending"
}
```

**响应示例:**
```json
{
    "id": 1,
    "debit_card": 1,
    "debit_card_number": "1234567890123456",
    "purchasing": 1,
    "purchasing_order_number": "ORD12345",
    "payment_amount": "500.00",
    "payment_time": "2025-12-28T06:00:00Z",
    "payment_status": "pending",
    "created_at": "2025-12-28T06:00:00Z",
    "updated_at": "2025-12-28T06:00:00Z"
}
```

#### 3. 获取特定 Debit Card Payment
```http
GET /api/aggregation/debitcard-payments/{id}/
```

#### 4. 更新 Debit Card Payment
```http
PATCH /api/aggregation/debitcard-payments/{id}/
Content-Type: application/json
```

```json
{
    "payment_status": "completed"
}
```

#### 5. 删除 Debit Card Payment
```http
DELETE /api/aggregation/debitcard-payments/{id}/
```

## 过滤、搜索和排序

### DebitCard 过滤选项
- `?card_number=1234567890123456` - 按卡号过滤
- `?balance=1000.00` - 按余额过滤
- `?expiry_year=2025` - 按有效期年份过滤
- `?expiry_month=12` - 按有效期月份过滤

### DebitCard 搜索
- `?search=1234` - 在卡号中搜索

### DebitCard 排序
- `?ordering=created_at` - 按创建时间升序
- `?ordering=-created_at` - 按创建时间降序（默认）
- `?ordering=balance` - 按余额排序
- `?ordering=-last_balance_update` - 按最近余额更新时间降序

### DebitCardPayment 过滤选项
- `?payment_status=completed` - 按支付状态过滤
- `?debit_card=1` - 按借记卡ID过滤
- `?purchasing=1` - 按采购订单ID过滤

### DebitCardPayment 搜索
- `?search=completed` - 在支付状态中搜索

### DebitCardPayment 排序
- `?ordering=-payment_time` - 按支付时间降序（默认）
- `?ordering=payment_amount` - 按支付金额升序

## 使用示例

### 示例 1: 创建借记卡并关联到采购订单

**步骤 1: 创建借记卡**
```bash
curl -X POST http://localhost:8000/api/aggregation/debitcards/ \
  -H "Authorization: Bearer your-token-here" \
  -H "Content-Type: application/json" \
  -d '{
    "card_number": "1234567890123456",
    "expiry_month": 12,
    "expiry_year": 2025,
    "passkey": "key123456",
    "balance": "2000.00",
    "batch_encoding": "BATCH-2025-01"
  }'
```

**步骤 2: 创建支付记录（关联到采购订单）**
```bash
curl -X POST http://localhost:8000/api/aggregation/debitcard-payments/ \
  -H "Content-Type: application/json" \
  -d '{
    "debit_card": 1,
    "purchasing": 1,
    "payment_amount": "500.00",
    "payment_status": "pending"
  }'
```

**步骤 3: 更新支付状态为已完成**
```bash
curl -X PATCH http://localhost:8000/api/aggregation/debitcard-payments/1/ \
  -H "Content-Type: application/json" \
  -d '{
    "payment_status": "completed"
  }'
```

### 示例 2: 更新借记卡余额

```bash
curl -X PATCH http://localhost:8000/api/aggregation/debitcards/1/ \
  -H "Authorization: Bearer your-token-here" \
  -H "Content-Type: application/json" \
  -d '{
    "balance": "1500.00",
    "last_balance_update": "2025-12-29T06:00:00Z"
  }'
```

### 示例 3: 查询特定借记卡的所有支付记录

```bash
curl http://localhost:8000/api/aggregation/debitcard-payments/?debit_card=1
```

### 示例 4: 查询已完成的支付记录

```bash
curl http://localhost:8000/api/aggregation/debitcard-payments/?payment_status=completed
```

## 错误处理

### 常见错误

#### 400 Bad Request - 验证错误
```json
{
    "card_number": ["This field is required."],
    "expiry_month": ["Expiry month must be between 1 and 12"],
    "balance": ["Balance cannot be negative"]
}
```

#### 400 Bad Request - 卡片已过期
```json
{
    "non_field_errors": ["Card has expired (expiry date is in the past)"]
}
```

#### 400 Bad Request - 支付金额无效
```json
{
    "payment_amount": ["Payment amount must be greater than zero"]
}
```

#### 404 Not Found
```json
{
    "detail": "Not found."
}
```

## 关系说明

### DebitCard ↔ Purchasing (多对多)
- 通过 `DebitCardPayment` 中间表实现
- 一个借记卡可以用于多个采购订单
- 一个采购订单可以使用多张借记卡支付
- 中间表记录每次支付的详细信息（金额、时间、状态）

### 删除行为
- 删除 DebitCard 时，相关的 DebitCardPayment 记录的 `debit_card` 字段设置为 NULL
- 删除 Purchasing 时，相关的 DebitCardPayment 记录的 `purchasing` 字段设置为 NULL
- 这样可以保留支付历史记录

## Admin 界面

Django Admin 支持完整的 CRUD 操作：

### DebitCard Admin
- 列表显示：卡号、有效期、余额、最近余额更新时间、支付次数
- 过滤：有效期年份、有效期月份、创建时间
- 搜索：卡号、passkey
- 支持批量操作

### DebitCardPayment Admin
- 列表显示：ID、借记卡、采购订单、支付金额、支付状态、支付时间
- 过滤：支付状态、支付时间
- 搜索：借记卡卡号、采购订单号

## 数据库架构

### 表结构

**debit_cards 表**
```sql
CREATE TABLE debit_cards (
    id BIGSERIAL PRIMARY KEY,
    card_number VARCHAR(19) UNIQUE NOT NULL,
    expiry_month INTEGER NOT NULL,
    expiry_year INTEGER NOT NULL,
    passkey VARCHAR(128) NOT NULL,
    last_balance_update TIMESTAMP WITH TIME ZONE,
    balance NUMERIC(12, 2) DEFAULT 0 NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL
);

CREATE INDEX ON debit_cards (card_number);
CREATE INDEX ON debit_cards (created_at DESC);
CREATE INDEX ON debit_cards (last_balance_update);
```

**debit_card_payments 表**
```sql
CREATE TABLE debit_card_payments (
    id BIGSERIAL PRIMARY KEY,
    debit_card_id BIGINT REFERENCES debit_cards(id) ON DELETE SET NULL,
    purchasing_id BIGINT REFERENCES purchasing(id) ON DELETE SET NULL,
    payment_amount NUMERIC(12, 2) NOT NULL,
    payment_time TIMESTAMP WITH TIME ZONE NOT NULL,
    payment_status VARCHAR(20) DEFAULT 'pending' NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL
);

CREATE INDEX ON debit_card_payments (payment_status);
CREATE INDEX ON debit_card_payments (payment_time DESC);
```

## 注意事项

1. **安全性**: passkey 字段当前未加密，生产环境应考虑加密存储
2. **余额管理**: 系统不自动更新余额，需要手动维护
3. **支付验证**: 目前不验证支付金额是否超过卡余额
4. **卡片有效期**: 系统验证卡片不能过期，但不阻止创建接近过期的卡
5. **中间表**: DebitCardPayment 作为独立模型，可以直接通过 API 管理

## 待实现功能 (TODO)

- [ ] passkey 字段加密存储
- [ ] 支付金额自动从余额扣除
- [ ] 支付金额验证（不能超过卡余额）
- [ ] 卡号格式验证（Luhn 算法）
- [ ] 批量支付功能
- [ ] 支付退款自动更新余额
- [ ] 卡片过期自动警告/禁用
