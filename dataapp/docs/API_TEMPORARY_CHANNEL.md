# TemporaryChannel API 文档

## 概述

TemporaryChannel（临时渠道）API 提供了对临时采购渠道的完整 CRUD 操作支持。

**Base URL**: `/api/aggregation/temporary-channels/`

---

## 模型字段说明

| 字段 | 类型 | 必填 | 只读 | 说明 |
|------|------|------|------|------|
| `id` | Integer | - | ✓ | 主键ID |
| `created_time` | DateTime | - | ✓ | 创建时间（自动生成） |
| `expected_time` | DateTime | ✓ | - | 入库预计时间 |
| `record` | String(255) | ✓ | - | 记录信息 |
| `last_updated` | DateTime | - | ✓ | 最后更新时间（自动更新） |
| `inventory_count` | Integer | - | ✓ | 关联的库存数量（SerializerMethod） |

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

### 1. 获取临时渠道列表

**请求**
```http
GET /api/aggregation/temporary-channels/
```

**查询参数**
- `expected_time`: 按预计时间过滤（例如：`?expected_time=2025-01-01`）
- `search`: 搜索记录内容（例如：`?search=关键词`）
- `ordering`: 排序字段（例如：`?ordering=-created_time`）

**响应示例**
```json
{
  "count": 10,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "created_time": "2025-01-01T10:00:00Z",
      "expected_time": "2025-01-15T12:00:00Z",
      "record": "临时渠道采购记录A",
      "last_updated": "2025-01-05T14:30:00Z",
      "inventory_count": 5
    }
  ]
}
```

---

### 2. 创建临时渠道

**请求**
```http
POST /api/aggregation/temporary-channels/
Content-Type: application/json
```

**请求体**
```json
{
  "expected_time": "2025-01-20T15:00:00Z",
  "record": "新的临时渠道记录"
}
```

**响应示例**
```json
{
  "id": 2,
  "created_time": "2025-01-10T09:00:00Z",
  "expected_time": "2025-01-20T15:00:00Z",
  "record": "新的临时渠道记录",
  "last_updated": "2025-01-10T09:00:00Z",
  "inventory_count": 0
}
```

**状态码**
- `201 Created`: 创建成功
- `400 Bad Request`: 请求数据验证失败

---

### 3. 获取单个临时渠道详情

**请求**
```http
GET /api/aggregation/temporary-channels/{id}/
```

**响应示例**
```json
{
  "id": 1,
  "created_time": "2025-01-01T10:00:00Z",
  "expected_time": "2025-01-15T12:00:00Z",
  "record": "临时渠道采购记录A",
  "last_updated": "2025-01-05T14:30:00Z",
  "inventory_count": 5
}
```

**状态码**
- `200 OK`: 获取成功
- `404 Not Found`: 临时渠道不存在

---

### 4. 更新临时渠道（完整更新）

**请求**
```http
PUT /api/aggregation/temporary-channels/{id}/
Content-Type: application/json
```

**请求体**
```json
{
  "expected_time": "2025-01-25T16:00:00Z",
  "record": "更新后的临时渠道记录"
}
```

**响应示例**
```json
{
  "id": 1,
  "created_time": "2025-01-01T10:00:00Z",
  "expected_time": "2025-01-25T16:00:00Z",
  "record": "更新后的临时渠道记录",
  "last_updated": "2025-01-10T10:00:00Z",
  "inventory_count": 5
}
```

---

### 5. 更新临时渠道（部分更新）

**请求**
```http
PATCH /api/aggregation/temporary-channels/{id}/
Content-Type: application/json
```

**请求体**
```json
{
  "expected_time": "2025-01-28T10:00:00Z"
}
```

**响应示例**
```json
{
  "id": 1,
  "created_time": "2025-01-01T10:00:00Z",
  "expected_time": "2025-01-28T10:00:00Z",
  "record": "临时渠道采购记录A",
  "last_updated": "2025-01-10T11:00:00Z",
  "inventory_count": 5
}
```

---

### 6. 删除临时渠道

**请求**
```http
DELETE /api/aggregation/temporary-channels/{id}/
```

**响应**
```http
HTTP/1.1 204 No Content
```

**状态码**
- `204 No Content`: 删除成功
- `404 Not Found`: 临时渠道不存在

---

## 使用示例

### Python (requests)

```python
import requests

base_url = "http://your-domain.com/api/aggregation/temporary-channels/"

# 1. 获取列表
response = requests.get(base_url)
channels = response.json()

# 2. 创建临时渠道
new_channel = {
    "expected_time": "2025-02-01T12:00:00Z",
    "record": "测试临时渠道"
}
response = requests.post(base_url, json=new_channel)
created_channel = response.json()

# 3. 获取详情
channel_id = created_channel['id']
response = requests.get(f"{base_url}{channel_id}/")
channel_detail = response.json()

# 4. 更新
update_data = {
    "record": "更新后的记录"
}
response = requests.patch(f"{base_url}{channel_id}/", json=update_data)

# 5. 删除
response = requests.delete(f"{base_url}{channel_id}/")
```

### cURL

```bash
# 获取列表
curl -X GET "http://your-domain.com/api/aggregation/temporary-channels/"

# 创建临时渠道
curl -X POST "http://your-domain.com/api/aggregation/temporary-channels/" \
  -H "Content-Type: application/json" \
  -d '{
    "expected_time": "2025-02-01T12:00:00Z",
    "record": "测试临时渠道"
  }'

# 更新临时渠道
curl -X PATCH "http://your-domain.com/api/aggregation/temporary-channels/1/" \
  -H "Content-Type: application/json" \
  -d '{"record": "更新后的记录"}'

# 删除临时渠道
curl -X DELETE "http://your-domain.com/api/aggregation/temporary-channels/1/"
```

---

## 高级查询

### 过滤示例

```http
# 按预计时间过滤
GET /api/aggregation/temporary-channels/?expected_time=2025-01-15

# 搜索记录内容
GET /api/aggregation/temporary-channels/?search=关键词

# 组合查询
GET /api/aggregation/temporary-channels/?expected_time=2025-01-15&search=采购
```

### 排序示例

```http
# 按创建时间降序
GET /api/aggregation/temporary-channels/?ordering=-created_time

# 按预计时间升序
GET /api/aggregation/temporary-channels/?ordering=expected_time

# 多字段排序
GET /api/aggregation/temporary-channels/?ordering=-expected_time,created_time
```

---

## 关联关系

### Inventory 关联

TemporaryChannel 与 Inventory 通过 `source4` 字段建立关联：

```python
# Inventory.source4 -> TemporaryChannel
# TemporaryChannel.temporary_channel_inventories -> Inventory (反向关系)
```

查询某个临时渠道的所有库存：
```python
channel = TemporaryChannel.objects.get(id=1)
inventories = channel.temporary_channel_inventories.all()
```

---

## 错误处理

### 常见错误

**400 Bad Request - 缺少必填字段**
```json
{
  "expected_time": ["This field is required."],
  "record": ["This field is required."]
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
CREATE TABLE temporary_channels (
    id SERIAL PRIMARY KEY,
    created_time TIMESTAMP NOT NULL,
    expected_time TIMESTAMP NOT NULL,
    record VARCHAR(255) NOT NULL,
    last_updated TIMESTAMP NOT NULL
);

CREATE INDEX ON temporary_channels(created_time DESC);
CREATE INDEX ON temporary_channels(expected_time);
```

---

## 注意事项

1. **时区处理**: 所有时间字段使用 UTC 时区
2. **自动更新**: `last_updated` 字段在每次更新时自动更新
3. **库存数量**: `inventory_count` 是计算字段，实时统计关联的库存数量
4. **删除限制**: 如果临时渠道已关联库存（source4），删除时会受到 `PROTECT` 约束保护

---

## 相关文档

- [Inventory API 文档](./API_INVENTORY.md)
- [模型架构文档](../ARCHITECTURE.md)
