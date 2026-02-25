# EcSite API 文档

## 概述

EcSite（电商网站）API 提供了对电商网站订单/预约数据的完整 CRUD 操作支持。

**Base URL**: `/api/aggregation/ec-sites/`

---

## 模型字段说明

| 字段 | 类型 | 必填 | 只读 | 说明 |
|------|------|------|------|------|
| `id` | Integer | - | ✓ | 主键ID |
| `reservation_number` | String(50) | ✓ | - | 预约号（唯一） |
| `username` | String(50) | ✓ | - | 用户名 |
| `method` | String(50) | ✓ | - | 方法/渠道 |
| `reservation_time` | DateTime | - | - | 预约时间 |
| `visit_time` | DateTime | - | - | 访问时间 |
| `order_created_at` | DateTime | - | ✓ | 订单创建时间（自动生成） |
| `info_updated_at` | DateTime | - | ✓ | 信息更新时间（自动更新） |
| `order_detail_url` | String(255) | ✓ | - | 订单详情URL |
| `inventory_count` | Integer | - | ✓ | 关联的库存数量（SerializerMethod） |
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

### 1. 获取电商订单列表

**请求**
```http
GET /api/aggregation/ec-sites/
```

**查询参数**
- `username`: 按用户名过滤（例如：`?username=user123`）
- `method`: 按方法过滤（例如：`?method=online`）
- `order_created_at`: 按订单创建时间过滤（例如：`?order_created_at=2025-01-01`）
- `visit_time`: 按访问时间过滤（例如：`?visit_time=2025-01-01`）
- `search`: 搜索预约号、用户名或订单详情URL（例如：`?search=RES123`）
- `ordering`: 排序字段（例如：`?ordering=-order_created_at`）

**响应示例**
```json
{
  "count": 10,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "reservation_number": "RES20250110001",
      "username": "user123",
      "method": "online",
      "reservation_time": "2025-01-10T10:00:00Z",
      "visit_time": "2025-01-10T14:00:00Z",
      "order_created_at": "2025-01-10T09:00:00Z",
      "info_updated_at": "2025-01-10T14:30:00Z",
      "order_detail_url": "https://example.com/orders/RES20250110001",
      "inventory_count": 3,
      "created_at": "2025-01-10T09:00:00Z",
      "updated_at": "2025-01-10T14:30:00Z"
    }
  ]
}
```

---

### 2. 创建电商订单

**请求**
```http
POST /api/aggregation/ec-sites/
Content-Type: application/json
```

**请求体**
```json
{
  "reservation_number": "RES20250115001",
  "username": "user456",
  "method": "store_pickup",
  "reservation_time": "2025-01-15T11:00:00Z",
  "visit_time": null,
  "order_detail_url": "https://example.com/orders/RES20250115001"
}
```

**响应示例**
```json
{
  "id": 2,
  "reservation_number": "RES20250115001",
  "username": "user456",
  "method": "store_pickup",
  "reservation_time": "2025-01-15T11:00:00Z",
  "visit_time": null,
  "order_created_at": "2025-01-12T10:00:00Z",
  "info_updated_at": "2025-01-12T10:00:00Z",
  "order_detail_url": "https://example.com/orders/RES20250115001",
  "inventory_count": 0,
  "created_at": "2025-01-12T10:00:00Z",
  "updated_at": "2025-01-12T10:00:00Z"
}
```

**状态码**
- `201 Created`: 创建成功
- `400 Bad Request`: 请求数据验证失败

**验证规则**
- `reservation_number`: 必须唯一
- 所有必填字段不能为空

---

### 3. 获取单个电商订单详情

**请求**
```http
GET /api/aggregation/ec-sites/{id}/
```

**响应示例**
```json
{
  "id": 1,
  "reservation_number": "RES20250110001",
  "username": "user123",
  "method": "online",
  "reservation_time": "2025-01-10T10:00:00Z",
  "visit_time": "2025-01-10T14:00:00Z",
  "order_created_at": "2025-01-10T09:00:00Z",
  "info_updated_at": "2025-01-10T14:30:00Z",
  "order_detail_url": "https://example.com/orders/RES20250110001",
  "inventory_count": 3,
  "created_at": "2025-01-10T09:00:00Z",
  "updated_at": "2025-01-10T14:30:00Z"
}
```

**状态码**
- `200 OK`: 获取成功
- `404 Not Found`: 订单不存在

---

### 4. 更新电商订单（完整更新）

**请求**
```http
PUT /api/aggregation/ec-sites/{id}/
Content-Type: application/json
```

**请求体**
```json
{
  "reservation_number": "RES20250110001",
  "username": "user123_updated",
  "method": "online",
  "reservation_time": "2025-01-10T10:00:00Z",
  "visit_time": "2025-01-10T15:00:00Z",
  "order_detail_url": "https://example.com/orders/RES20250110001"
}
```

**响应示例**
```json
{
  "id": 1,
  "reservation_number": "RES20250110001",
  "username": "user123_updated",
  "method": "online",
  "reservation_time": "2025-01-10T10:00:00Z",
  "visit_time": "2025-01-10T15:00:00Z",
  "order_created_at": "2025-01-10T09:00:00Z",
  "info_updated_at": "2025-01-12T11:00:00Z",
  "order_detail_url": "https://example.com/orders/RES20250110001",
  "inventory_count": 3,
  "created_at": "2025-01-10T09:00:00Z",
  "updated_at": "2025-01-12T11:00:00Z"
}
```

---

### 5. 更新电商订单（部分更新）

**请求**
```http
PATCH /api/aggregation/ec-sites/{id}/
Content-Type: application/json
```

**请求体**
```json
{
  "visit_time": "2025-01-10T16:00:00Z"
}
```

**响应示例**
```json
{
  "id": 1,
  "reservation_number": "RES20250110001",
  "username": "user123",
  "method": "online",
  "reservation_time": "2025-01-10T10:00:00Z",
  "visit_time": "2025-01-10T16:00:00Z",
  "order_created_at": "2025-01-10T09:00:00Z",
  "info_updated_at": "2025-01-12T12:00:00Z",
  "order_detail_url": "https://example.com/orders/RES20250110001",
  "inventory_count": 3,
  "created_at": "2025-01-10T09:00:00Z",
  "updated_at": "2025-01-12T12:00:00Z"
}
```

---

### 6. 删除电商订单

**请求**
```http
DELETE /api/aggregation/ec-sites/{id}/
```

**响应**
```http
HTTP/1.1 204 No Content
```

**状态码**
- `204 No Content`: 删除成功
- `404 Not Found`: 订单不存在

---

## 使用示例

### Python (requests)

```python
import requests

base_url = "http://your-domain.com/api/aggregation/ec-sites/"

# 1. 获取列表
response = requests.get(base_url)
orders = response.json()

# 2. 创建电商订单
new_order = {
    "reservation_number": "RES20250120001",
    "username": "test_user",
    "method": "online",
    "reservation_time": "2025-01-20T12:00:00Z",
    "order_detail_url": "https://example.com/orders/RES20250120001"
}
response = requests.post(base_url, json=new_order)
created_order = response.json()

# 3. 获取详情
order_id = created_order['id']
response = requests.get(f"{base_url}{order_id}/")
order_detail = response.json()

# 4. 更新访问时间
update_data = {
    "visit_time": "2025-01-20T14:00:00Z"
}
response = requests.patch(f"{base_url}{order_id}/", json=update_data)

# 5. 删除
response = requests.delete(f"{base_url}{order_id}/")
```

### cURL

```bash
# 获取列表
curl -X GET "http://your-domain.com/api/aggregation/ec-sites/"

# 创建订单
curl -X POST "http://your-domain.com/api/aggregation/ec-sites/" \
  -H "Content-Type: application/json" \
  -d '{
    "reservation_number": "RES20250120001",
    "username": "test_user",
    "method": "online",
    "reservation_time": "2025-01-20T12:00:00Z",
    "order_detail_url": "https://example.com/orders/RES20250120001"
  }'

# 更新订单
curl -X PATCH "http://your-domain.com/api/aggregation/ec-sites/1/" \
  -H "Content-Type: application/json" \
  -d '{"visit_time": "2025-01-20T14:00:00Z"}'

# 删除订单
curl -X DELETE "http://your-domain.com/api/aggregation/ec-sites/1/"
```

---

## 高级查询

### 过滤示例

```http
# 按用户名过滤
GET /api/aggregation/ec-sites/?username=user123

# 按方法过滤
GET /api/aggregation/ec-sites/?method=online

# 按订单创建时间过滤
GET /api/aggregation/ec-sites/?order_created_at=2025-01-10

# 搜索预约号
GET /api/aggregation/ec-sites/?search=RES2025

# 组合查询
GET /api/aggregation/ec-sites/?username=user123&method=online
```

### 排序示例

```http
# 按订单创建时间降序
GET /api/aggregation/ec-sites/?ordering=-order_created_at

# 按访问时间升序
GET /api/aggregation/ec-sites/?ordering=visit_time

# 多字段排序
GET /api/aggregation/ec-sites/?ordering=-order_created_at,username
```

---

## 关联关系

### Inventory 关联

EcSite 与 Inventory 通过 `source1` 字段建立关联：

```python
# Inventory.source1 -> EcSite
# EcSite.ecsite_inventories -> Inventory (反向关系)
```

查询某个电商订单的所有库存：
```python
ec_site = EcSite.objects.get(id=1)
inventories = ec_site.ecsite_inventories.all()
```

---

## 错误处理

### 常见错误

**400 Bad Request - 预约号重复**
```json
{
  "reservation_number": ["ec site with this reservation number already exists."]
}
```

**400 Bad Request - 缺少必填字段**
```json
{
  "reservation_number": ["This field is required."],
  "username": ["This field is required."],
  "method": ["This field is required."],
  "order_detail_url": ["This field is required."]
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
CREATE TABLE ec_site (
    id SERIAL PRIMARY KEY,
    reservation_number VARCHAR(50) UNIQUE NOT NULL,
    username VARCHAR(50) NOT NULL,
    method VARCHAR(50) NOT NULL,
    reservation_time TIMESTAMP NULL,
    visit_time TIMESTAMP NULL,
    order_created_at TIMESTAMP NOT NULL,
    info_updated_at TIMESTAMP NOT NULL,
    order_detail_url VARCHAR(255) NOT NULL,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL
);

CREATE INDEX ON ec_site(reservation_number);
CREATE INDEX ON ec_site(order_created_at);
CREATE INDEX ON ec_site(visit_time);
```

---

## 注意事项

1. **预约号唯一性**: `reservation_number` 必须唯一
2. **时区处理**: 所有时间字段使用 UTC 时区
3. **自动更新**: `info_updated_at` 和 `updated_at` 在每次更新时自动更新
4. **库存数量**: `inventory_count` 是计算字段，实时统计关联的库存数量
5. **删除限制**: 如果订单已关联库存（source1），删除时会受到 `PROTECT` 约束保护

---

## 相关文档

- [Inventory API 文档](./API_INVENTORY.md)
- [Legal Person Offline API 文档](./API_LEGAL_PERSON_OFFLINE.md)
- [Temporary Channel API 文档](./API_TEMPORARY_CHANNEL.md)
- [模型架构文档](../ARCHITECTURE.md)
