# Historical Data Stats API 文档

## 概述

Historical Data Stats API 提供了统计各模型数据并记录到 `HistoricalData` 模型的功能，用于追踪历史数据变化。

**Base URL**: `/api/aggregation/v1/historical-data/`

**认证方式**: `QueryParamTokenAuthentication`（查询参数传递 Token）

---

## 认证配置

### Token 配置

在 `.env` 文件或 `settings.py` 中配置：

```python
# settings.py
BATCH_STATS_API_TOKEN = 'your-secure-token-here'
```

或在 `.env` 文件中：

```env
BATCH_STATS_API_TOKEN=your-secure-token-here
```

### 认证方式

所有请求需要在查询参数中传递 token：

```
?token=your-secure-token-here
```

---

## API 端点

### 1. Batch Encoding 统计

统计 CreditCard、DebitCard、GiftCard、OfficialAccount 四个模型中每个 `batch_encoding` 值对应的记录数。

**端点**
```
GET /api/aggregation/v1/historical-data/batch-stats/?token=xxx
```

**统计范围**

| 模型 | 说明 |
|------|------|
| `CreditCard` | 信用卡 |
| `DebitCard` | 借记卡 |
| `GiftCard` | 礼品卡 |
| `OfficialAccount` | 官方账号 |

**HistoricalData 记录格式**

| 字段 | 值 |
|------|-----|
| model | 模型名（如 `CreditCard`） |
| slug | `batch:{batch_encoding_value}` |
| value | 该 batch_encoding 对应的记录数 |

**请求示例**
```http
GET /api/aggregation/v1/historical-data/batch-stats/?token=your-token
```

**响应示例 - 成功**
```json
{
    "status": "success",
    "data": {
        "CreditCard": {
            "batch_2024_01": 15,
            "batch_2024_02": 8
        },
        "DebitCard": {
            "batch_2024_01": 5
        },
        "GiftCard": {
            "batch_2024_01": 20,
            "batch_2024_03": 12
        },
        "OfficialAccount": {
            "batch_2024_01": 50,
            "batch_2024_02": 30
        }
    },
    "historical_records_created": 7
}
```

**响应示例 - 无数据**
```json
{
    "status": "success",
    "data": {
        "CreditCard": {},
        "DebitCard": {},
        "GiftCard": {},
        "OfficialAccount": {}
    },
    "historical_records_created": 0
}
```

---

### 2. Purchasing 阶段统计

统计 Purchasing 模型中不同处理阶段的记录数。

**端点**
```
GET /api/aggregation/v1/historical-data/purchasing-stats/?token=xxx
```

**统计的 6 种阶段**

| 阶段名 | 条件说明 |
|--------|----------|
| `confirmed_at_empty` | `confirmed_at` 为空，且 `shipped_at`、`estimated_website_arrival_date`、`tracking_number`、`estimated_delivery_date` 均为空 |
| `shipped_at_empty` | `shipped_at` 为空，且后续 3 个字段均为空，但 `confirmed_at` 不为空 |
| `estimated_website_arrival_date_empty` | `estimated_website_arrival_date` 为空，且后续 2 个字段均为空，但 `confirmed_at`、`shipped_at` 不为空 |
| `tracking_number_empty` | `tracking_number` 为空，且 `estimated_delivery_date` 为空，但前 3 个字段不为空 |
| `estimated_delivery_date_empty` | `estimated_delivery_date` 为空，但其他 4 个字段不为空 |
| `other` | 不符合以上任何条件的记录 |

**空值判断规则**

| 字段类型 | 空值判断 |
|----------|----------|
| DateTimeField / DateField | `NULL` |
| CharField (`tracking_number`) | `NULL` 或空字符串 `''` |

**HistoricalData 记录格式**

| 字段 | 值 |
|------|-----|
| model | `Purchasing` |
| slug | `stage:{stage_name}` |
| value | 该阶段的记录数 |

**请求示例**
```http
GET /api/aggregation/v1/historical-data/purchasing-stats/?token=your-token
```

**响应示例 - 成功**
```json
{
    "status": "success",
    "data": {
        "confirmed_at_empty": 10,
        "shipped_at_empty": 5,
        "estimated_website_arrival_date_empty": 3,
        "tracking_number_empty": 2,
        "estimated_delivery_date_empty": 1,
        "other": 29
    },
    "total": 50,
    "historical_records_created": 6
}
```

---

## HistoricalData 模型

统计结果会自动记录到 `HistoricalData` 模型中，便于追踪历史变化。

### 模型结构

| 字段 | 类型 | 说明 |
|------|------|------|
| `model` | CharField(100) | 被统计的模型名 |
| `slug` | CharField(255) | 条件标识符 |
| `value` | IntegerField | 统计值 |
| `created_at` | DateTimeField | 记录创建时间（自动生成） |

### Slug 命名约定

| API | Slug 格式 | 示例 |
|-----|-----------|------|
| batch-stats | `batch:{batch_encoding_value}` | `batch:batch_2024_01` |
| purchasing-stats | `stage:{stage_name}` | `stage:confirmed_at_empty` |

---

## 使用示例

### Python (requests)

```python
import requests

base_url = "http://your-domain.com/api/aggregation/v1/historical-data"
token = "your-secure-token"

# 1. 获取 Batch Encoding 统计
response = requests.get(
    f"{base_url}/batch-stats/",
    params={"token": token}
)
batch_stats = response.json()
print(f"Batch 统计: {batch_stats['data']}")
print(f"创建了 {batch_stats['historical_records_created']} 条历史记录")

# 2. 获取 Purchasing 阶段统计
response = requests.get(
    f"{base_url}/purchasing-stats/",
    params={"token": token}
)
purchasing_stats = response.json()
print(f"Purchasing 统计: {purchasing_stats['data']}")
print(f"总记录数: {purchasing_stats['total']}")
```

### cURL

```bash
# Batch Encoding 统计
curl -X GET "http://your-domain.com/api/aggregation/v1/historical-data/batch-stats/?token=your-token"

# Purchasing 阶段统计
curl -X GET "http://your-domain.com/api/aggregation/v1/historical-data/purchasing-stats/?token=your-token"
```

### JavaScript (fetch)

```javascript
const baseUrl = 'http://your-domain.com/api/aggregation/v1/historical-data';
const token = 'your-secure-token';

// Batch Encoding 统计
async function getBatchStats() {
    const response = await fetch(`${baseUrl}/batch-stats/?token=${token}`);
    const data = await response.json();
    console.log('Batch 统计:', data.data);
    console.log('创建记录数:', data.historical_records_created);
    return data;
}

// Purchasing 阶段统计
async function getPurchasingStats() {
    const response = await fetch(`${baseUrl}/purchasing-stats/?token=${token}`);
    const data = await response.json();
    console.log('Purchasing 统计:', data.data);
    console.log('总记录数:', data.total);
    return data;
}

// 执行
getBatchStats();
getPurchasingStats();
```

---

## 状态码说明

| 状态码 | 说明 |
|--------|------|
| 200 | 请求成功 |
| 401 | 认证失败（Token 无效、缺失或未配置） |
| 500 | 服务器内部错误 |

---

## 错误响应

### Token 缺失
```json
{
    "detail": "Token is required"
}
```

### Token 无效
```json
{
    "detail": "Invalid token"
}
```

### Token 未配置
```json
{
    "detail": "API token not configured"
}
```

---

## 注意事项

1. **认证要求**: 所有请求都需要在查询参数中提供有效的 Token
2. **历史记录**: 每次调用 API 都会创建新的 `HistoricalData` 记录，请注意调用频率
3. **空值处理**: `batch_encoding` 为空或 NULL 的记录不会被统计
4. **数据一致性**: 统计和记录在同一事务中完成，确保数据一致性

---

## 相关文档

- [API 总览](./API_OVERVIEW.md)
- [Purchasing API](./API_PURCHASING.md)
- [Credit Card API](./API_CREDIT_CARD.md)
- [Debit Card API](./API_DEBIT_CARD.md)
- [Gift Card API](./API_GIFT_CARD.md)
- [Official Account API](./API_OFFICIAL_ACCOUNT.md)

---

## 更新日志

| 日期 | 版本 | 说明 |
|------|------|------|
| 2026-01-04 | 1.0 | 初始版本，包含 batch-stats 和 purchasing-stats 两个端点 |
