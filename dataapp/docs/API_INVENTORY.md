# Inventory API Documentation

## 概要

库存管理模型的完整 REST API，支持 CRUD 操作，用于跟踪产品库存状态和物流信息。

## 模型字段

| 字段 | 类型 | 必填 | 说明 | 示例 |
|------|------|------|------|------|
| `id` | Integer | 自动 | 主键ID | `1` |
| `uuid` | String(59) | 自动 | 全局唯一标识符（48字符） | `1a2b-3c4d-5e6f-7a8b-9c0d-1e2f-3a4b-5c6d-7e8f-9a0b-1c2d-3e4f` |
| `flag` | String(100) | - | 人类可识别标识 | `BATCH-2025-001` |
| `iphone` | ForeignKey | - | 关联的 iPhone 产品 | `1` (iPhone ID) |
| `ipad` | ForeignKey | - | 关联的 iPad 产品 | `2` (iPad ID) |
| `imei` | String(17) | - | 设备 IMEI 编号（唯一） | `123456789012345` |
| `batch_level_1` | String(255) | - | 一级批次标识符 | `WAREHOUSE-A` |
| `batch_level_2` | String(255) | - | 二级批次标识符 | `AREA-1` |
| `batch_level_3` | String(255) | - | 三级批次标识符 | `SHELF-01` |
| `product_type` | String | 只读 | 产品类型 | `iPhone` / `iPad` |
| `product_display` | Object | 只读 | 产品详细信息 | `{"type": "iPhone", "id": 1, "name": "..."}` |
| `source1` | ForeignKey | - | 进货来源1（EC Site） | `1` (EcSite ID) |
| `source2` | ForeignKey | - | 进货来源2（Purchasing） | `2` (Purchasing ID) |
| `source3` | ForeignKey | - | 进货来源3（Legal Person Offline） | `3` (LegalPersonOffline ID) |
| `source3_display` | Object | 只读 | 进货来源3的简要信息 | `{"id": 1, "uuid": "...", "username": "张三", "visit_time": "...", "order_created_at": "..."}` |
| `source4` | ForeignKey | - | 进货来源4（Temporary Channel） | `4` (TemporaryChannel ID) |
| `transaction_confirmed_at` | DateTime | - | 交易确认时间 | `2025-12-20T10:00:00Z` |
| `scheduled_arrival_at` | DateTime | - | 预约到货时间 | `2025-12-25T14:00:00Z` |
| `checked_arrival_at_1` | DateTime | - | 第一次查询到货时间 | `2025-12-23T09:00:00Z` |
| `checked_arrival_at_2` | DateTime | - | 第二次查询到货时间 | `2025-12-24T11:00:00Z` |
| `actual_arrival_at` | DateTime | - | 实际到货时间 | `2025-12-25T15:30:00Z` |
| `status` | String(20) | ✓ | 状态 | `planned` / `in_transit` / `arrived` / `out_of_stock` / `abnormal` |
| `created_at` | DateTime | 自动 | 记录创建时间 | `2025-12-28T06:55:00Z` |
| `updated_at` | DateTime | 自动 | 记录更新时间 | `2025-12-28T06:55:00Z` |
| `is_deleted` | Boolean | 只读 | 软删除标志 | `false` |

### 状态选项

| 值 | 显示名称 | 说明 |
|---|---------|------|
| `planned` | 计划中 | 商品计划中（默认状态） |
| `in_transit` | 到达中 | 商品在途中 |
| `arrived` | 到达 | 商品已到达 |
| `out_of_stock` | 出库 | 商品已出库 |
| `abnormal` | 异常 | 异常状态 |

### 批次管理字段说明

三级批次管理字段用于库存分批工作和组织管理：

**使用场景：**
- **物理位置管理**: `batch_level_1`=仓库 → `batch_level_2`=区域 → `batch_level_3`=货架
- **逻辑分组**: `batch_level_1`=供应商 → `batch_level_2`=批次 → `batch_level_3`=子批次
- **时间维度**: `batch_level_1`=年份 → `batch_level_2`=月份 → `batch_level_3`=周次

**特性：**
- 所有批次字段都是可选的
- 支持独立使用任意级别
- 已添加数据库索引以优化查询性能


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
http://localhost:8000/api/aggregation/inventory/
```

### 1. 列出所有库存
```http
GET /api/aggregation/inventory/
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
            "uuid": "1a2b-3c4d-5e6f-7a8b-9c0d-1e2f-3a4b-5c6d-7e8f-9a0b-1c2d-3e4f",
            "flag": "BATCH-2025-001",
            "iphone": 1,
            "ipad": null,
            "imei": "123456789012345",
            "batch_level_1": "WAREHOUSE-A",
            "batch_level_2": "AREA-1",
            "batch_level_3": "SHELF-01",
            "product_type": "iPhone",
            "product_display": {
                "type": "iPhone",
                "id": 1,
                "name": "iPhone 17 256GB ブラック"
            },
            "source1": 1,
            "source2": null,
            "source3": null,
            "source3_display": null,
            "source4": null,
            "transaction_confirmed_at": "2025-12-20T10:00:00Z",
            "scheduled_arrival_at": "2025-12-25T14:00:00Z",
            "checked_arrival_at_1": "2025-12-23T09:00:00Z",
            "checked_arrival_at_2": "2025-12-24T11:00:00Z",
            "actual_arrival_at": "2025-12-25T15:30:00Z",
            "status": "arrived",
            "created_at": "2025-12-28T06:55:00Z",
            "updated_at": "2025-12-28T06:55:00Z",
            "is_deleted": false
        }
    ]
}
```

### 2. 创建新库存
```http
POST /api/aggregation/inventory/
Content-Type: application/json
```

**请求体（关联 iPhone）:**
```json
{
    "flag": "BATCH-2025-001",
    "iphone": 1,
    "source1": 1,
    "imei": "123456789012345",
    "batch_level_1": "WAREHOUSE-A",
    "batch_level_2": "AREA-1",
    "batch_level_3": "SHELF-01",
    "transaction_confirmed_at": "2025-12-20T10:00:00",
    "scheduled_arrival_at": "2025-12-25T14:00:00",
    "status": "in_transit"
}
```

**请求体（关联 iPad）:**
```json
{
    "flag": "BATCH-2025-002",
    "ipad": 2,
    "source1": 2,
    "transaction_confirmed_at": "2025-12-21T09:00:00",
    "scheduled_arrival_at": "2025-12-26T10:00:00",
    "status": "in_transit"
}
```

**请求体（未分配产品）:**
```json
{
    "flag": "BATCH-2025-003",
    "source1": 3,
    "status": "in_transit"
}
```

**响应:** `201 Created`
```json
{
    "id": 1,
    "uuid": "1a2b-3c4d-5e6f-7a8b-9c0d-1e2f-3a4b-5c6d-7e8f-9a0b-1c2d-3e4f",
    "flag": "BATCH-2025-001",
    "iphone": 1,
    "ipad": null,
    "imei": "123456789012345",
    "batch_level_1": "WAREHOUSE-A",
    "batch_level_2": "AREA-1",
    "batch_level_3": "SHELF-01",
    "product_type": "iPhone",
    "product_display": {
        "type": "iPhone",
        "id": 1,
        "name": "iPhone 17 256GB ブラック"
    },
    "source1": 1,
    "source2": null,
    "source3": null,
    "source3_display": null,
    "source4": null,
    "transaction_confirmed_at": "2025-12-20T10:00:00Z",
    "scheduled_arrival_at": "2025-12-25T14:00:00Z",
    "checked_arrival_at_1": null,
    "checked_arrival_at_2": null,
    "actual_arrival_at": null,
    "status": "in_transit",
    "created_at": "2025-12-28T06:55:00Z",
    "updated_at": "2025-12-28T06:55:00Z",
    "is_deleted": false
}
```

### 3. 获取特定库存
```http
GET /api/aggregation/inventory/{id}/
```

**示例:**
```http
GET /api/aggregation/inventory/1/
```

### 4. 更新库存 (完整更新)
```http
PUT /api/aggregation/inventory/{id}/
Content-Type: application/json
```

**请求体:** (所有非只读字段)
```json
{
    "flag": "BATCH-2025-001-UPDATED",
    "iphone": 1,
    "source1": 1,
    "source2": 2,
    "transaction_confirmed_at": "2025-12-20T10:00:00",
    "scheduled_arrival_at": "2025-12-25T14:00:00",
    "checked_arrival_at_1": "2025-12-23T09:00:00",
    "checked_arrival_at_2": "2025-12-24T11:00:00",
    "actual_arrival_at": "2025-12-25T15:30:00",
    "status": "arrived"
}
```

### 5. 部分更新库存
```http
PATCH /api/aggregation/inventory/{id}/
Content-Type: application/json
```

**请求体（更新状态和实际到货时间）:**
```json
{
    "status": "arrived",
    "actual_arrival_at": "2025-12-25T15:30:00"
}
```

**请求体（添加查询时间）:**
```json
{
    "checked_arrival_at_1": "2025-12-23T09:00:00"
}
```

### 6. 删除库存
```http
DELETE /api/aggregation/inventory/{id}/
```

**响应:** `204 No Content`

---

## 高级功能

### 过滤 (Filtering)

按特定字段过滤结果：

```http
# 按状态过滤
GET /api/aggregation/inventory/?status=in_transit
GET /api/aggregation/inventory/?status=arrived

# 按 iPhone 产品过滤
GET /api/aggregation/inventory/?iphone=1

# 按 iPad 产品过滤
GET /api/aggregation/inventory/?ipad=2

# 按 IMEI 过滤
GET /api/aggregation/inventory/?imei=123456789012345

# 按批次过滤
GET /api/aggregation/inventory/?batch_level_1=WAREHOUSE-A

# 按来源过滤
GET /api/aggregation/inventory/?source1=1
GET /api/aggregation/inventory/?source2=2

# 按软删除状态过滤
GET /api/aggregation/inventory/?is_deleted=false

# 组合过滤（状态为已到达的 iPhone）
GET /api/aggregation/inventory/?status=arrived&iphone=1
```

### 搜索 (Search)

在 UUID、flag 和 IMEI 字段中搜索：

```http
# 搜索包含 "BATCH" 的记录
GET /api/aggregation/inventory/?search=BATCH

# 搜索 UUID
GET /api/aggregation/inventory/?search=1a2b-3c4d

# 搜索标识
GET /api/aggregation/inventory/?search=2025-001
```

### 排序 (Ordering)

按指定字段排序：

```http
# 按创建时间降序（最新的在前，默认）
GET /api/aggregation/inventory/?ordering=-created_at

# 按创建时间升序
GET /api/aggregation/inventory/?ordering=created_at

# 按实际到货时间降序
GET /api/aggregation/inventory/?ordering=-actual_arrival_at

# 按预计到货时间排序
GET /api/aggregation/inventory/?ordering=scheduled_arrival_at

# 按交易确认时间排序
GET /api/aggregation/inventory/?ordering=-transaction_confirmed_at

# 按状态排序
GET /api/aggregation/inventory/?ordering=status

# 按更新时间降序
GET /api/aggregation/inventory/?ordering=-updated_at

# 多字段排序（先按状态，再按创建时间降序）
GET /api/aggregation/inventory/?ordering=status,-created_at
```

### 分页 (Pagination)

```http
# 获取第2页，每页20条
GET /api/aggregation/inventory/?page=2&page_size=20

# 默认每页100条（在 settings.py 中配置）
GET /api/aggregation/inventory/?page=1
```

### 组合查询示例

```http
# 查找所有在途中的 iPhone，按创建时间排序
GET /api/aggregation/inventory/?status=in_transit&iphone__isnull=false&ordering=-created_at

# 搜索包含 "BATCH" 的已到达商品
GET /api/aggregation/inventory/?search=BATCH&status=arrived

# 查找特定 iPhone 的所有库存，按实际到货时间降序
GET /api/aggregation/inventory/?iphone=1&ordering=-actual_arrival_at

# 查找异常状态的库存，每页10条
GET /api/aggregation/inventory/?status=abnormal&page_size=10
```

---

## 数据验证

### 产品互斥验证
- **不能同时关联** iPhone 和 iPad
- 可以两者都不关联（未分配产品的库存）
- 只能关联一个产品类型

**错误示例:**
```json
{
    "non_field_errors": [
        "Cannot assign both iPhone and iPad to the same inventory item. Choose one."
    ]
}
```

### UUID 自动生成
- UUID 在创建时自动生成
- 格式：48 个字符，12 组 4 位十六进制数，用连字符分隔
- 示例：`1a2b-3c4d-5e6f-7a8b-9c0d-1e2f-3a4b-5c6d-7e8f-9a0b-1c2d-3e4f`
- **全局唯一**，使用密码学安全的随机数生成

### 外键验证
- `iphone` 必须是存在的 iPhone 记录的 ID
- `ipad` 必须是存在的 iPad 记录的 ID

**错误示例:**
```json
{
    "iphone": ["Invalid pk \"999\" - object does not exist."]
}
```

---

## 错误响应

### 400 Bad Request
```json
{
    "non_field_errors": [
        "Cannot assign both iPhone and iPad to the same inventory item. Choose one."
    ]
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
from datetime import datetime

BASE_URL = "http://localhost:8000/api/aggregation/inventory/"

# 创建库存记录（关联 iPhone）
data = {
    "flag": "BATCH-2025-001",
    "iphone": 1,
    "source1": 1,
    "transaction_confirmed_at": "2025-12-20T10:00:00",
    "scheduled_arrival_at": "2025-12-25T14:00:00",
    "status": "in_transit"
}
headers = {"Authorization": "Bearer your-token-here"}
response = requests.post(BASE_URL, json=data, headers=headers)
print(response.json())

# 获取所有库存
response = requests.get(BASE_URL, headers=headers)
print(response.json())

# 搜索
response = requests.get(f"{BASE_URL}?search=BATCH", headers=headers)
print(response.json())

# 过滤在途中的商品
response = requests.get(f"{BASE_URL}?status=in_transit")
print(response.json())

# 更新状态（商品到达）
inventory_id = 1
update_data = {
    "status": "arrived",
    "actual_arrival_at": datetime.now().isoformat()
}
response = requests.patch(f"{BASE_URL}{inventory_id}/", headers=headers, json=update_data)
print(response.json())

# 添加查询时间
update_data = {
    "checked_arrival_at_1": "2025-12-23T09:00:00"
}
response = requests.patch(f"{BASE_URL}{inventory_id}/", headers=headers, json=update_data)
print(response.json())
```

### JavaScript (fetch)

```javascript
const BASE_URL = "http://localhost:8000/api/aggregation/inventory/";

// 创建库存记录（关联 iPad）
const createInventory = async () => {
    const data = {
        flag: "BATCH-2025-002",
        ipad: 2,
        source1: 2,
        transaction_confirmed_at: "2025-12-21T09:00:00",
        scheduled_arrival_at: "2025-12-26T10:00:00",
        status: "in_transit"
    };

    const response = await fetch(BASE_URL, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(data)
    });

    return await response.json();
};

// 获取所有库存
const getInventory = async () => {
    const response = await fetch(BASE_URL);
    return await response.json();
};

// 搜索
const searchInventory = async (query) => {
    const response = await fetch(`${BASE_URL}?search=${query}`);
    return await response.json();
};

// 按状态过滤
const filterByStatus = async (status) => {
    const response = await fetch(`${BASE_URL}?status=${status}`);
    return await response.json();
};

// 更新到达状态
const markAsArrived = async (id) => {
    const data = {
        status: "arrived",
        actual_arrival_at: new Date().toISOString()
    };

    const response = await fetch(`${BASE_URL}${id}/`, {
        method: 'PATCH',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(data)
    });

    return await response.json();
};
```

### cURL

```bash
# 创建库存记录（关联 iPhone）
curl -X POST http://localhost:8000/api/aggregation/inventory/ \
  -H "Authorization: Bearer your-token-here" \
  -H "Content-Type: application/json" \
  -d '{
    "flag": "BATCH-2025-001",
    "iphone": 1,
    "source1": 1,
    "transaction_confirmed_at": "2025-12-20T10:00:00",
    "scheduled_arrival_at": "2025-12-25T14:00:00",
    "status": "in_transit"
  }'

# 获取所有库存
curl -H "Authorization: Bearer your-token-here" http://localhost:8000/api/aggregation/inventory/

# 搜索
curl -H "Authorization: Bearer your-token-here" "http://localhost:8000/api/aggregation/inventory/?search=BATCH"

# 按状态过滤
curl -H "Authorization: Bearer your-token-here" "http://localhost:8000/api/aggregation/inventory/?status=in_transit"

# 更新状态和实际到货时间
curl -X PATCH http://localhost:8000/api/aggregation/inventory/1/ \
  -H "Authorization: Bearer your-token-here" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "arrived",
    "actual_arrival_at": "2025-12-25T15:30:00"
  }'

# 添加第一次查询时间
curl -X PATCH http://localhost:8000/api/aggregation/inventory/1/ \
  -H "Authorization: Bearer your-token-here" \
  -H "Content-Type: application/json" \
  -d '{
    "checked_arrival_at_1": "2025-12-23T09:00:00"
  }'

# 删除库存记录
curl -X DELETE -H "Authorization: Bearer your-token-here" http://localhost:8000/api/aggregation/inventory/1/
```

---

## 业务流程示例

### 典型的库存生命周期

```python
import requests
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000/api/aggregation/inventory/"

# 1. 创建库存记录（交易确认）
inventory = requests.post(BASE_URL, json={
    "flag": "BATCH-2025-001",
    "iphone": 1,
    "source1": 1,
    "transaction_confirmed_at": datetime.now().isoformat(),
    "scheduled_arrival_at": (datetime.now() + timedelta(days=5)).isoformat(),
    "status": "in_transit"
}).json()

inventory_id = inventory['id']

# 2. 第一次查询物流（3天后）
requests.patch(f"{BASE_URL}{inventory_id}/", json={
    "checked_arrival_at_1": datetime.now().isoformat()
})

# 3. 第二次查询物流（4天后）
requests.patch(f"{BASE_URL}{inventory_id}/", json={
    "checked_arrival_at_2": datetime.now().isoformat()
})

# 4. 商品到达（5天后）
requests.patch(f"{BASE_URL}{inventory_id}/", json={
    "status": "arrived",
    "actual_arrival_at": datetime.now().isoformat()
})

# 5. 商品出库（7天后）
requests.patch(f"{BASE_URL}{inventory_id}/", json={
    "status": "out_of_stock"
})

# 6. 如遇异常情况
requests.patch(f"{BASE_URL}{inventory_id}/", json={
    "status": "abnormal"
})
```

---

## 数据库索引

为了优化查询性能，以下字段已创建索引：

- `uuid` - 全局唯一标识符
- `status` - 状态
- `created_at` - 创建时间
- `actual_arrival_at` (降序) - 实际到货时间
- `batch_level_1` - 一级批次标识符
- `batch_level_2` - 二级批次标识符
- `batch_level_3` - 三级批次标识符

**特殊约束：**
- `imei` 字段具有唯一性约束（UNIQUE），确保每个设备编号唯一

---

## 访问 API 文档

启动服务器后，可通过以下地址访问交互式 API 文档：

- **Swagger UI**: http://localhost:8000/api/docs/
- **ReDoc**: http://localhost:8000/api/redoc/
- **Admin Panel**: http://localhost:8000/admin/

---

## 注意事项

1. **时间格式**: 使用 ISO 8601 格式 (`YYYY-MM-DDTHH:MM:SS` 或带时区 `YYYY-MM-DDTHH:MM:SSZ`)
2. **时区**: 所有时间戳使用 Asia/Tokyo 时区
3. **分页**: 默认每页返回 100 条记录
4. **UUID**: 自动生成，不可手动指定
5. **产品关联**: iPhone 和 iPad 不能同时关联到同一库存记录
6. **未分配产品**: 可以创建不关联任何产品的库存记录
7. **进货来源**: source1-4 字段已更改为外键，分别关联 EcSite、Purchasing、LegalPersonOffline、TemporaryChannel
8. **Flag 规则**: 当前可手动指定，部分场景下自动生成（如 LegalPersonOffline.create_with_inventory）
9. **只读字段**: `id`, `uuid`, `created_at`, `updated_at`, `product_type`, `product_display`, `source3_display`, `is_deleted` 不可修改
10. **IMEI 唯一性**: `imei` 字段具有唯一性约束，重复的 IMEI 将导致创建失败
11. **批次管理**: 三个批次字段（batch_level_1/2/3）可用于多维度库存分类管理
12. **软删除**: 使用 `is_deleted` 字段实现软删除，不直接从数据库删除记录

---

## 相关 API

- [iPhone API 文档](API_IPHONE.md)
- [iPad API 文档](API_IPAD.md)
- [电子产品架构文档](ELECTRONIC_PRODUCTS_ARCHITECTURE.md)

---

## 状态流转图

```
in_transit (到达中)
    ↓
    ├─→ arrived (到达)
    │       ↓
    │   out_of_stock (出库)
    │
    └─→ abnormal (异常)
```

典型的状态流转：
1. `in_transit` → `arrived` → `out_of_stock` (正常流程)
2. `in_transit` → `abnormal` (物流异常)
3. `arrived` → `abnormal` (到货异常)
