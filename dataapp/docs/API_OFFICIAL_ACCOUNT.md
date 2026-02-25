# Official Account API Documentation

## 概要

Official Account（官方账号）模型的完整 REST API，支持 CRUD 操作。此模型用于管理账号信息，与 Purchasing（采购订单）模型为一对多关系（一个账号可关联多个采购订单）。

## 模型字段

| 字段 | 类型 | 必填 | 说明 | 示例 |
|------|------|------|------|------|
| `id` | Integer | 自动 | 主键ID | `1` |
| `uuid` | String(59) | 自动 | 全局唯一标识符 | `1a2b-3c4d-5e6f...` |
| `account_id` | String(50) | ✓ | 账号ID（可重复） | `ACC12345` |
| `email` | String(50) | ✓ | 邮箱（唯一） | `user@example.com` |
| `name` | String(50) | ✓ | 姓名 | `张三` |
| `postal_code` | String(50) | ✗ | 邮编 | `123-4567` |
| `address_line_1` | String(50) | ✗ | 地址1 | `东京都` |
| `address_line_2` | String(50) | ✗ | 地址2 | `新宿区` |
| `address_line_3` | String(50) | ✗ | 地址3 | `西新宿1-1-1` |
| `passkey` | String(50) | ✓ | 访问密钥 | `key123456` |
| `batch_encoding` | String(100) | ✗ | 批次编号（用于分组相关记录） | `BATCH-2025-01` |
| `purchasing_orders_count` | Integer | 只读 | 关联的采购订单数量 | `5` |
| `created_at` | DateTime | 自动 | 创建时间 | `2025-12-28T06:00:00Z` |
| `updated_at` | DateTime | 自动 | 更新时间 | `2025-12-28T06:00:00Z` |

## 数据验证

### 当前验证
- `account_id`: 不能为空
- `email`: 不能为空，必须唯一
- `name`: 不能为空
- `passkey`: 不能为空

### TODO 待实现验证
- ✅ `email`: 需要添加邮箱格式验证（正则表达式）
- ✅ `postal_code`: 需要添加邮编格式验证（如日本邮编格式 123-4567）
- ✅ `passkey`: 需要添加密钥强度验证和加密处理


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

### 基础 URL
```
http://localhost:8000/api/aggregation/official-accounts/
```

### 1. 列出所有 Official Account
```http
GET /api/aggregation/official-accounts/
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
            "uuid": "1a2b-3c4d-5e6f-7a8b-9c0d-1e2f-3a4b-5c6d-7e8f-9a0b-1c2d-3e4f",
            "account_id": "ACC12345",
            "email": "user1@example.com",
            "name": "张三",
            "postal_code": "123-4567",
            "address_line_1": "东京都",
            "address_line_2": "新宿区",
            "address_line_3": "西新宿1-1-1",
            "passkey": "key123456",
            "batch_encoding": "BATCH-2025-01",
            "purchasing_orders_count": 3,
            "created_at": "2025-12-28T06:00:00Z",
            "updated_at": "2025-12-28T06:00:00Z"
        },
        {
            "id": 2,
            "uuid": "9z8y-7x6w-5v4u-3t2s-1r0q-9p8o-7n6m-5l4k-3j2i-1h0g-9f8e-7d6c",
            "account_id": "ACC67890",
            "email": "user2@example.com",
            "name": "李四",
            "postal_code": "",
            "address_line_1": "",
            "address_line_2": "",
            "address_line_3": "",
            "passkey": "key789012",
            "batch_encoding": "",
            "purchasing_orders_count": 2,
            "created_at": "2025-12-28T07:00:00Z",
            "updated_at": "2025-12-28T07:00:00Z"
        }
    ]
}
```

### 2. 创建新 Official Account
```http
POST /api/aggregation/official-accounts/
Content-Type: application/json
```

**请求体:**
```json
{
    "account_id": "ACC12345",
    "email": "newuser@example.com",
    "name": "王五",
    "postal_code": "987-6543",
    "address_line_1": "大阪府",
    "address_line_2": "大阪市",
    "address_line_3": "北区梅田1-1-1",
    "passkey": "securekey123",
    "batch_encoding": "BATCH-2025-01"
}
```

**响应:** `201 Created`
```json
{
    "id": 3,
    "uuid": "8w7v-6u5t-4s3r-2q1p-0o9n-8m7l-6k5j-4i3h-2g1f-0e9d-8c7b-6a5z",
    "account_id": "ACC12345",
    "email": "newuser@example.com",
    "name": "王五",
    "postal_code": "987-6543",
    "address_line_1": "大阪府",
    "address_line_2": "大阪市",
    "address_line_3": "北区梅田1-1-1",
    "passkey": "securekey123",
    "batch_encoding": "BATCH-2025-01",
    "purchasing_orders_count": 0,
    "created_at": "2025-12-28T08:00:00Z",
    "updated_at": "2025-12-28T08:00:00Z"
}
```

### 3. 获取特定 Official Account
```http
GET /api/aggregation/official-accounts/{id}/
```

**示例:**
```http
GET /api/aggregation/official-accounts/1/
```

**响应:** `200 OK`
```json
{
    "id": 1,
    "uuid": "1a2b-3c4d-5e6f-7a8b-9c0d-1e2f-3a4b-5c6d-7e8f-9a0b-1c2d-3e4f",
    "account_id": "ACC12345",
    "email": "user1@example.com",
    "name": "张三",
    "postal_code": "123-4567",
    "address_line_1": "东京都",
    "address_line_2": "新宿区",
    "address_line_3": "西新宿1-1-1",
    "passkey": "key123456",
    "batch_encoding": "BATCH-2025-01",
    "purchasing_orders_count": 3,
    "created_at": "2025-12-28T06:00:00Z",
    "updated_at": "2025-12-28T06:00:00Z"
}
```

### 4. 更新 Official Account (完整更新)
```http
PUT /api/aggregation/official-accounts/{id}/
Content-Type: application/json
```

**请求体:**
```json
{
    "account_id": "ACC12345",
    "email": "updated@example.com",
    "name": "张三（更新）",
    "postal_code": "111-2222",
    "address_line_1": "东京都",
    "address_line_2": "渋谷区",
    "address_line_3": "道玄坂1-1-1",
    "passkey": "newkey456",
    "batch_encoding": "BATCH-2025-02"
}
```

**响应:** `200 OK`

### 5. 部分更新 Official Account
```http
PATCH /api/aggregation/official-accounts/{id}/
Content-Type: application/json
```

**请求体示例（仅更新邮编和地址）:**
```json
{
    "postal_code": "333-4444",
    "address_line_1": "京都府"
}
```

**响应:** `200 OK`

### 6. 删除 Official Account
```http
DELETE /api/aggregation/official-accounts/{id}/
```

**响应:** `204 No Content`

**注意:** 如果该账号关联了采购订单，且采购订单的 `on_delete` 策略为 `PROTECT`，则删除会失败。

## 过滤和搜索

### 过滤
可以通过以下字段进行过滤：

```http
# 按账号ID过滤
GET /api/aggregation/official-accounts/?account_id=ACC12345

# 按邮箱过滤
GET /api/aggregation/official-accounts/?email=user@example.com

# 按姓名过滤
GET /api/aggregation/official-accounts/?name=张三
```

### 搜索
可以在 `uuid`, `account_id`, `email`, `name`, `postal_code` 字段中搜索：

```http
GET /api/aggregation/official-accounts/?search=张三
GET /api/aggregation/official-accounts/?search=123-4567
```

### 排序
可以按以下字段排序：

```http
# 按创建时间降序（默认）
GET /api/aggregation/official-accounts/?ordering=-created_at

# 按邮箱升序
GET /api/aggregation/official-accounts/?ordering=email

# 按姓名升序
GET /api/aggregation/official-accounts/?ordering=name

# 多字段排序
GET /api/aggregation/official-accounts/?ordering=name,-created_at
```

## 与 Purchasing 的关系

Official Account 与 Purchasing（采购订单）为一对多关系：
- 一个 Official Account 可以关联多个 Purchasing 订单
- 在 Purchasing API 中可以通过 `official_account` 字段过滤：

```http
# 查询特定账号的所有采购订单
GET /api/aggregation/purchasing/?official_account=1
```

## 数据库索引

为了优化查询性能，以下字段已建立索引：
- `uuid` (唯一索引)
- `email` (唯一索引)
- `account_id` (普通索引)
- `created_at` (降序索引)

## 错误响应

### 400 Bad Request
```json
{
    "email": [
        "This field cannot be empty"
    ]
}
```

### 400 Bad Request (Email重复)
```json
{
    "email": [
        "official account with this 邮箱 already exists."
    ]
}
```

### 404 Not Found
```json
{
    "detail": "Not found."
}
```

## 使用示例

### Python (requests)
```python
import requests

# 创建新账号
data = {
    "account_id": "ACC99999",
    "email": "test@example.com",
    "name": "测试用户",
    "postal_code": "100-0001",
    "address_line_1": "东京都千代田区",
    "passkey": "testkey123",
    "batch_encoding": "BATCH-2025-01"
}

response = requests.post(
    "http://localhost:8000/api/aggregation/official-accounts/",
    json=data
)

print(response.json())
```

### cURL
```bash
# 获取所有账号
curl -X GET http://localhost:8000/api/aggregation/official-accounts/

# 创建新账号
curl -X POST http://localhost:8000/api/aggregation/official-accounts/ \
  -H "Content-Type: application/json" \
  -d '{
    "account_id": "ACC99999",
    "email": "test@example.com",
    "name": "测试用户",
    "postal_code": "100-0001",
    "address_line_1": "东京都千代田区",
    "passkey": "testkey123",
    "batch_encoding": "BATCH-2025-01"
  }'

# 更新账号
curl -X PATCH http://localhost:8000/api/aggregation/official-accounts/1/ \
  -H "Content-Type: application/json" \
  -d '{
    "postal_code": "200-0002"
  }'
```

## 注意事项

1. **Email 唯一性**: 邮箱必须唯一，不能重复
2. **Account ID 可重复**: account_id 可以重复（业务需求）
3. **UUID 自动生成**: UUID 在创建时自动生成，无需手动指定
4. **Passkey 安全性**: TODO - 目前 passkey 以明文存储，未来需要实现加密
5. **关联保护**: 删除账号前需确保没有关联的采购订单，或先删除关联订单
6. **地址字段可选**: postal_code 和 address_line_* 字段为可选，可以为空

## 迁移说明

首次部署时需要运行以下命令创建数据库表：

```bash
python manage.py makemigrations data_aggregation
python manage.py migrate
```

## 相关文档

- [Purchasing API 文档](./API_PURCHASING.md)
- [Inventory API 文档](./API_INVENTORY.md)
- [iPhone API 文档](./API_IPHONE.md)
