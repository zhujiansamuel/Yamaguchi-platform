# iPad API Documentation

## 概要

iPad 模型的完整 REST API，支持 CRUD 操作。

## 模型字段

| 字段 | 类型 | 必填 | 说明 | 示例 |
|------|------|------|------|------|
| `id` | Integer | 自动 | 主键ID | `1` |
| `part_number` | String(50) | ✓ | 型号（唯一） | `MUW63J/A` |
| `model_name` | String(100) | ✓ | 机型名称 | `iPad Pro 12.9` |
| `capacity_gb` | Integer | ✓ | 容量(GB) | `256` |
| `color` | String(50) | ✓ | 颜色 | `スペースグレイ` |
| `release_date` | Date | ✓ | 发布日期 | `2024-11-06` |
| `jan` | String(13) | ✓ | JAN码（唯一） | `4549995649161` |
| `created_at` | DateTime | 自动 | 创建时间 | `2025-12-28T04:00:00Z` |
| `updated_at` | DateTime | 自动 | 更新时间 | `2025-12-28T04:00:00Z` |


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
http://localhost:8000/api/aggregation/ipads/
```

### 1. 列出所有 iPad
```http
GET /api/aggregation/ipads/
```

**响应示例:**
```json
{
    "count": 1,
    "next": null,
    "previous": null,
    "results": [
        {
            "id": 1,
            "part_number": "MUW63J/A",
            "model_name": "iPad Pro 12.9",
            "capacity_gb": 256,
            "color": "スペースグレイ",
            "release_date": "2024-11-06",
            "jan": "4549995649161",
            "created_at": "2025-12-28T04:00:00Z",
            "updated_at": "2025-12-28T04:00:00Z"
        }
    ]
}
```

### 2. 创建新 iPad
```http
POST /api/aggregation/ipads/
Content-Type: application/json
```

**请求体:**
```json
{
    "part_number": "MUW63J/A",
    "model_name": "iPad Pro 12.9",
    "capacity_gb": 256,
    "color": "スペースグレイ",
    "release_date": "2024-11-06",
    "jan": "4549995649161"
}
```

**响应:** `201 Created`
```json
{
    "id": 1,
    "part_number": "MUW63J/A",
    "model_name": "iPad Pro 12.9",
    "capacity_gb": 256,
    "color": "スペースグレイ",
    "release_date": "2024-11-06",
    "jan": "4549995649161",
    "created_at": "2025-12-28T04:00:00Z",
    "updated_at": "2025-12-28T04:00:00Z"
}
```

### 3. 获取特定 iPad
```http
GET /api/aggregation/ipads/{id}/
```

**示例:**
```http
GET /api/aggregation/ipads/1/
```

### 4. 更新 iPad (完整更新)
```http
PUT /api/aggregation/ipads/{id}/
Content-Type: application/json
```

**请求体:** (所有字段必填)
```json
{
    "part_number": "MUW63J/A",
    "model_name": "iPad Pro 12.9",
    "capacity_gb": 512,
    "color": "シルバー",
    "release_date": "2024-11-06",
    "jan": "4549995649161"
}
```

### 5. 部分更新 iPad
```http
PATCH /api/aggregation/ipads/{id}/
Content-Type: application/json
```

**请求体:** (仅更新需要的字段)
```json
{
    "capacity_gb": 512,
    "color": "シルバー"
}
```

### 6. 删除 iPad
```http
DELETE /api/aggregation/ipads/{id}/
```

**响应:** `204 No Content`

---

## 高级功能

### 过滤 (Filtering)

按特定字段过滤结果：

```http
# 按机型名称过滤
GET /api/aggregation/ipads/?model_name=iPad Pro 12.9

# 按容量过滤
GET /api/aggregation/ipads/?capacity_gb=256

# 按颜色过滤
GET /api/aggregation/ipads/?color=スペースグレイ

# 按发布日期过滤
GET /api/aggregation/ipads/?release_date=2024-11-06

# 组合过滤
GET /api/aggregation/ipads/?model_name=iPad Pro 12.9&capacity_gb=256
```

### 搜索 (Search)

在多个字段中搜索：

```http
# 搜索包含 "iPad" 的记录（在 part_number, model_name, color, jan 中搜索）
GET /api/aggregation/ipads/?search=iPad

# 搜索 JAN 码
GET /api/aggregation/ipads/?search=4549995649161

# 搜索颜色
GET /api/aggregation/ipads/?search=スペースグレイ
```

### 排序 (Ordering)

按指定字段排序：

```http
# 按发布日期降序（最新的在前）
GET /api/aggregation/ipads/?ordering=-release_date

# 按发布日期升序
GET /api/aggregation/ipads/?ordering=release_date

# 按机型名称排序
GET /api/aggregation/ipads/?ordering=model_name

# 按容量降序
GET /api/aggregation/ipads/?ordering=-capacity_gb

# 多字段排序
GET /api/aggregation/ipads/?ordering=-release_date,model_name
```

### 分页 (Pagination)

```http
# 获取第2页，每页20条
GET /api/aggregation/ipads/?page=2&page_size=20

# 默认每页100条（在 settings.py 中配置）
GET /api/aggregation/ipads/?page=1
```

### 组合查询示例

```http
# 搜索 iPad Pro，按容量降序排列
GET /api/aggregation/ipads/?search=iPad Pro&ordering=-capacity_gb

# 过滤256GB的设备，按发布日期排序
GET /api/aggregation/ipads/?capacity_gb=256&ordering=-release_date

# 搜索灰色设备，每页10条
GET /api/aggregation/ipads/?search=グレイ&page_size=10
```

---

## 数据验证

### JAN 码验证
- 必须是 **13 位数字**
- 仅包含数字字符

**错误示例:**
```json
{
    "jan": ["JAN code must be exactly 13 digits"]
}
```

### 容量验证
- 必须是 **正整数**

**错误示例:**
```json
{
    "capacity_gb": ["Capacity must be a positive number"]
}
```

### 唯一性验证
- `part_number` 必须唯一
- `jan` 必须唯一

**错误示例:**
```json
{
    "part_number": ["i pad with this Part Number already exists."]
}
```

---

## 错误响应

### 400 Bad Request
```json
{
    "capacity_gb": ["Capacity must be a positive number"],
    "jan": ["JAN code must be exactly 13 digits"]
}
```

### 404 Not Found
```json
{
    "detail": "Not found."
}
```

### 500 Internal Server Error
```json
{
    "detail": "Internal server error"
}
```

---

## 使用示例

### Python (requests)

```python
import requests

BASE_URL = "http://localhost:8000/api/aggregation/ipads/"

# 创建 iPad
data = {
    "part_number": "MUW63J/A",
    "model_name": "iPad Pro 12.9",
    "capacity_gb": 256,
    "color": "スペースグレイ",
    "release_date": "2024-11-06",
    "jan": "4549995649161"
}
headers = {"Authorization": "Bearer your-token-here"}
response = requests.post(BASE_URL, json=data, headers=headers)
print(response.json())

# 获取所有 iPad
response = requests.get(BASE_URL, headers=headers)
print(response.json())

# 搜索
response = requests.get(f"{BASE_URL}?search=", headers=headersiPad Pro")
print(response.json())

# 更新
ipad_id = 1
update_data = {"capacity_gb": 512}
response = requests.patch(f"{BASE_URL}{", headers=headersipad_id}/", json=update_data)
print(response.json())
```

### JavaScript (fetch)

```javascript
const BASE_URL = "http://localhost:8000/api/aggregation/ipads/";

// 创建 iPad
const createiPad = async () => {
    const data = {
        part_number: "MUW63J/A",
        model_name: "iPad Pro 12.9",
        capacity_gb: 256,
        color: "スペースグレイ",
        release_date: "2024-11-06",
        jan: "4549995649161"
    };

    const response = await fetch(BASE_URL, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(data)
    });

    return await response.json();
};

// 获取所有 iPad
const getiPads = async () => {
    const response = await fetch(BASE_URL);
    return await response.json();
};

// 搜索
const searchiPads = async (query) => {
    const response = await fetch(`${BASE_URL}?search=${query}`);
    return await response.json();
};
```

### cURL

```bash
# 创建 iPad
curl -X POST http://localhost:8000/api/aggregation/ipads/ \
  -H "Authorization: Bearer your-token-here" \
  -H "Content-Type: application/json" \
  -d '{
    "part_number": "MUW63J/A",
    "model_name": "iPad Pro 12.9",
    "capacity_gb": 256,
    "color": "スペースグレイ",
    "release_date": "2024-11-06",
    "jan": "4549995649161"
  }'

# 获取所有 iPad
curl -H "Authorization: Bearer your-token-here" http://localhost:8000/api/aggregation/ipads/

# 搜索
curl -H "Authorization: Bearer your-token-here" "http://localhost:8000/api/aggregation/ipads/?search=iPad"

# 更新
curl -X PATCH http://localhost:8000/api/aggregation/ipads/1/ \
  -H "Authorization: Bearer your-token-here" \
  -H "Content-Type: application/json" \
  -d '{"capacity_gb": 512}'

# 删除
curl -X DELETE -H "Authorization: Bearer your-token-here" http://localhost:8000/api/aggregation/ipads/1/
```

---

## 数据库索引

为了优化查询性能，以下字段已创建索引：

- `model_name` - 机型名称
- `release_date` - 发布日期
- `jan` - JAN码
- `part_number` - 型号

---

## 访问 API 文档

启动服务器后，可通过以下地址访问交互式 API 文档：

- **Swagger UI**: http://localhost:8000/api/docs/
- **ReDoc**: http://localhost:8000/api/redoc/
- **Admin Panel**: http://localhost:8000/admin/

---

## 注意事项

1. **日期格式**: 使用 ISO 8601 格式 (`YYYY-MM-DD`)
2. **时区**: 所有时间戳使用 Asia/Tokyo 时区
3. **分页**: 默认每页返回 100 条记录
4. **唯一性**: `part_number` 和 `jan` 必须唯一
5. **JAN 码**: 必须是13位数字
