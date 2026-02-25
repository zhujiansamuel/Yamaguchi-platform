# LegalPersonOffline API 文档

## 概述

LegalPersonOffline（法人线下）API 提供了对法人线下门店访问和采购记录的完整 CRUD 操作支持。

**Base URL**: `/api/aggregation/legal-person-offline/`

---

## 模型字段说明

| 字段 | 类型 | 必填 | 只读 | 说明 |
|------|------|------|------|------|
| `id` | Integer | - | ✓ | 主键ID |
| `uuid` | String(59) | - | ✓ | 全局唯一标识符（自动生成） |
| `username` | String(50) | ✓ | - | 客户用户名 |
| `appointment_time` | DateTime | - | - | 预约时间 |
| `visit_time` | DateTime | - | - | 实际访问时间 |
| `order_created_at` | DateTime | - | ✓ | 订单创建时间（自动生成） |
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

### 1. 获取法人线下记录列表

**请求**
```http
GET /api/aggregation/legal-person-offline/
```

**查询参数**
- `username`: 按用户名过滤（例如：`?username=张三`）
- `visit_time`: 按访问时间过滤（例如：`?visit_time=2025-01-01`）
- `appointment_time`: 按预约时间过滤（例如：`?appointment_time=2025-01-01`）
- `search`: 搜索 UUID 或用户名（例如：`?search=user123`）
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
      "uuid": "1a2b3c4d-5e6f7a8b-9c0d1e2f-3a4b5c6d-7e8f9a0b-1c2d3e4f...",
      "username": "张三",
      "appointment_time": "2025-01-10T14:00:00Z",
      "visit_time": "2025-01-10T14:15:00Z",
      "order_created_at": "2025-01-10T14:20:00Z",
      "updated_at": "2025-01-10T14:20:00Z"
    }
  ]
}
```

---

### 2. 创建法人线下记录

**请求**
```http
POST /api/aggregation/legal-person-offline/
Content-Type: application/json
```

**请求体**
```json
{
  "username": "李四",
  "appointment_time": "2025-01-15T10:00:00Z",
  "visit_time": "2025-01-15T10:05:00Z"
}
```

**响应示例**
```json
{
  "id": 2,
  "uuid": "2b3c4d5e-6f7a8b9c-0d1e2f3a-4b5c6d7e-8f9a0b1c-2d3e4f5a...",
  "username": "李四",
  "appointment_time": "2025-01-15T10:00:00Z",
  "visit_time": "2025-01-15T10:05:00Z",
  "order_created_at": "2025-01-12T09:00:00Z",
  "updated_at": "2025-01-12T09:00:00Z"
}
```

**状态码**
- `201 Created`: 创建成功
- `400 Bad Request`: 请求数据验证失败

**验证规则**
- `username`: 不能为空

---

### 3. 获取单个法人线下记录详情

**请求**
```http
GET /api/aggregation/legal-person-offline/{id}/
```

**响应示例**
```json
{
  "id": 1,
  "uuid": "1a2b3c4d-5e6f7a8b-9c0d1e2f-3a4b5c6d-7e8f9a0b-1c2d3e4f...",
  "username": "张三",
  "appointment_time": "2025-01-10T14:00:00Z",
  "visit_time": "2025-01-10T14:15:00Z",
  "order_created_at": "2025-01-10T14:20:00Z",
  "updated_at": "2025-01-10T14:20:00Z"
}
```

**状态码**
- `200 OK`: 获取成功
- `404 Not Found`: 记录不存在

---

### 4. 更新法人线下记录（完整更新）

**请求**
```http
PUT /api/aggregation/legal-person-offline/{id}/
Content-Type: application/json
```

**请求体**
```json
{
  "username": "张三（更新）",
  "appointment_time": "2025-01-10T15:00:00Z",
  "visit_time": "2025-01-10T15:10:00Z"
}
```

**响应示例**
```json
{
  "id": 1,
  "uuid": "1a2b3c4d-5e6f7a8b-9c0d1e2f-3a4b5c6d-7e8f9a0b-1c2d3e4f...",
  "username": "张三（更新）",
  "appointment_time": "2025-01-10T15:00:00Z",
  "visit_time": "2025-01-10T15:10:00Z",
  "order_created_at": "2025-01-10T14:20:00Z",
  "updated_at": "2025-01-12T10:00:00Z"
}
```

---

### 5. 更新法人线下记录（部分更新）

**请求**
```http
PATCH /api/aggregation/legal-person-offline/{id}/
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
  "uuid": "1a2b3c4d-5e6f7a8b-9c0d1e2f-3a4b5c6d-7e8f9a0b-1c2d3e4f...",
  "username": "张三",
  "appointment_time": "2025-01-10T14:00:00Z",
  "visit_time": "2025-01-10T16:00:00Z",
  "order_created_at": "2025-01-10T14:20:00Z",
  "updated_at": "2025-01-12T11:00:00Z"
}
```

---

### 6. 删除法人线下记录

**请求**
```http
DELETE /api/aggregation/legal-person-offline/{id}/
```

**响应**
```http
HTTP/1.1 204 No Content
```

**状态码**
- `204 No Content`: 删除成功
- `404 Not Found`: 记录不存在

---

## 使用示例

### Python (requests)

```python
import requests

base_url = "http://your-domain.com/api/aggregation/legal-person-offline/"

# 1. 获取列表
response = requests.get(base_url)
records = response.json()

# 2. 创建法人线下记录
new_record = {
    "username": "王五",
    "appointment_time": "2025-01-20T11:00:00Z",
    "visit_time": "2025-01-20T11:10:00Z"
}
response = requests.post(base_url, json=new_record)
created_record = response.json()

# 3. 获取详情
record_id = created_record['id']
response = requests.get(f"{base_url}{record_id}/")
record_detail = response.json()

# 4. 更新访问时间
update_data = {
    "visit_time": "2025-01-20T12:00:00Z"
}
response = requests.patch(f"{base_url}{record_id}/", json=update_data)

# 5. 删除
response = requests.delete(f"{base_url}{record_id}/")
```

### cURL

```bash
# 获取列表
curl -X GET "http://your-domain.com/api/aggregation/legal-person-offline/"

# 创建记录
curl -X POST "http://your-domain.com/api/aggregation/legal-person-offline/" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "王五",
    "appointment_time": "2025-01-20T11:00:00Z",
    "visit_time": "2025-01-20T11:10:00Z"
  }'

# 更新记录
curl -X PATCH "http://your-domain.com/api/aggregation/legal-person-offline/1/" \
  -H "Content-Type: application/json" \
  -d '{"visit_time": "2025-01-20T12:00:00Z"}'

# 删除记录
curl -X DELETE "http://your-domain.com/api/aggregation/legal-person-offline/1/"
```

---

## 高级查询

### 过滤示例

```http
# 按用户名过滤
GET /api/aggregation/legal-person-offline/?username=张三

# 按访问时间过滤
GET /api/aggregation/legal-person-offline/?visit_time=2025-01-10

# 搜索 UUID 或用户名
GET /api/aggregation/legal-person-offline/?search=user123

# 组合查询
GET /api/aggregation/legal-person-offline/?username=张三&visit_time=2025-01-10
```

### 排序示例

```http
# 按创建时间降序
GET /api/aggregation/legal-person-offline/?ordering=-order_created_at

# 按访问时间升序
GET /api/aggregation/legal-person-offline/?ordering=visit_time

# 多字段排序
GET /api/aggregation/legal-person-offline/?ordering=-visit_time,username
```

---

## 关联关系

### Inventory 关联

LegalPersonOffline 与 Inventory 通过 `source3` 字段建立关联：

```python
# Inventory.source3 -> LegalPersonOffline
# LegalPersonOffline.legal_person_inventories -> Inventory (反向关系)
```

查询某个法人线下记录的所有库存：
```python
record = LegalPersonOffline.objects.get(id=1)
inventories = record.legal_person_inventories.all()
```

---

## UUID 生成规则

UUID 格式：48个字符的十六进制字符串，分为12组，每组4个字符：
```
1a2b-3c4d-5e6f-7a8b-9c0d-1e2f-3a4b-5c6d-7e8f-9a0b-1c2d-3e4f
```

- **长度**: 59字符（包含11个连字符）
- **唯一性**: 全局唯一
- **自动生成**: 创建时自动生成，不可修改

---

## 错误处理

### 常见错误

**400 Bad Request - 用户名为空**
```json
{
  "username": ["Username cannot be empty"]
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
CREATE TABLE legal_person_offline (
    id SERIAL PRIMARY KEY,
    uuid VARCHAR(59) UNIQUE NOT NULL,
    username VARCHAR(50) NOT NULL,
    appointment_time TIMESTAMP NULL,
    visit_time TIMESTAMP NULL,
    order_created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL
);

CREATE INDEX ON legal_person_offline(uuid);
CREATE INDEX ON legal_person_offline(username);
CREATE INDEX ON legal_person_offline(order_created_at DESC);
CREATE INDEX ON legal_person_offline(visit_time);
```

---

## 注意事项

1. **UUID 唯一性**: UUID 自动生成，确保全局唯一
2. **时区处理**: 所有时间字段使用 UTC 时区
3. **可选时间字段**: `appointment_time` 和 `visit_time` 都是可选的
4. **删除限制**: 如果记录已关联库存（source3），删除时会受到 `PROTECT` 约束保护

---

## 相关文档

- [Inventory API 文档](./API_INVENTORY.md)
- [EcSite API 文档](./API_EC_SITE.md)
- [模型架构文档](../ARCHITECTURE.md)
