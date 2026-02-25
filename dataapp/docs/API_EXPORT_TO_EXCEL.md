# Export to Excel API 文档

## 概述

Export to Excel API 提供了将 data_aggregation 应用中的模型数据导出为 Excel 文件并上传到 Nextcloud 的功能。

**Base URL**: `/api/aggregation/export-to-excel/`

**认证方式**: `SimpleTokenAuthentication` (使用 `BATCH_STATS_API_TOKEN`)

---

## 核心特性

### 双版本导出机制

此 API 支持同时导出两种版本的 Excel 文件：

| 版本类型 | 文件名格式 | 保存目录 | 说明 |
|----------|-----------|----------|------|
| **现在状态版本** | `{ModelName}_test.xlsx` | `No_aggregated_raw_data/` | 每次导出都会覆盖，只保留最新状态 |
| **历史追溯版本** | `{ModelName}_test_{timestamp}.xlsx` | `data_platform/` | 带时间戳，可用于历史追溯和数据回滚 |

### 配置选项

在 `settings.py` 中配置导出行为：

```python
# 是否启用历史追溯版本
ENABLE_EXCEL_HISTORICAL_TRACKING = True  # True: 同时导出两个版本, False: 只导出现在状态版本

# 历史追溯目录（带时间戳的版本）
EXCEL_OUTPUT_PATH = 'data_platform/'

# 非历史追溯目录（当前状态版本，覆盖式）
EXCEL_OUTPUT_PATH_NO_HISTORY = 'No_aggregated_raw_data/'

# Nextcloud WebDAV 配置
NEXTCLOUD_CONFIG = {
    'webdav_login': 'your_username',
    'webdav_password': 'your_password',
    'webdav_hostname': 'https://your-nextcloud-server.com/remote.php/dav/files/username/'
}
```

---

## 支持的模型

当前支持导出以下 18 个模型：

### 产品模型
| 模型名 | 说明 |
|--------|------|
| `iPhone` | iPhone 产品信息 |
| `iPad` | iPad 产品信息 |

### 库存与采购
| 模型名 | 说明 |
|--------|------|
| `Inventory` | 库存管理 |
| `Purchasing` | 采购订单 |
| `OfficialAccount` | 官方账号 |

### 采购来源渠道
| 模型名 | 说明 |
|--------|------|
| `EcSite` | 电商网站订单 (source1) |
| `LegalPersonOffline` | 法人线下采购 (source3) |
| `TemporaryChannel` | 临时渠道 (source4) |

### 支付方式
| 模型名 | 说明 |
|--------|------|
| `GiftCard` | 礼品卡 |
| `GiftCardPayment` | 礼品卡支付记录 |
| `DebitCard` | 借记卡 |
| `DebitCardPayment` | 借记卡支付记录 |
| `CreditCard` | 信用卡 |
| `CreditCardPayment` | 信用卡支付记录 |
| `OtherPayment` | 其他支付方式 |

### 数据聚合
| 模型名 | 说明 |
|--------|------|
| `AggregationSource` | 数据聚合源 |
| `AggregatedData` | 聚合后的数据 |
| `AggregationTask` | 聚合任务 |

---

## API 端点

### 1. 获取可用模型列表

获取所有可导出的模型名称。

**请求**
```http
GET /api/aggregation/export-to-excel/
Authorization: Bearer <BATCH_STATS_API_TOKEN>
```

**响应示例**
```json
{
    "status": "success",
    "available_models": [
        "iPhone",
        "iPad",
        "Inventory",
        "Purchasing",
        "OfficialAccount",
        "TemporaryChannel",
        "LegalPersonOffline",
        "EcSite",
        "GiftCard",
        "GiftCardPayment",
        "DebitCard",
        "DebitCardPayment",
        "CreditCard",
        "CreditCardPayment",
        "OtherPayment",
        "AggregationSource",
        "AggregatedData",
        "AggregationTask"
    ],
    "message": "Found 18 models available for export"
}
```

---

### 2. 导出模型数据到 Excel

将指定模型的数据导出为 Excel 文件并上传到 Nextcloud。

**请求**
```http
POST /api/aggregation/export-to-excel/
Authorization: Bearer <BATCH_STATS_API_TOKEN>
Content-Type: application/json
```

**请求体**

```json
{
    "models": ["iPhone", "iPad", "Inventory"]
}
```

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `models` | Array | 否 | 要导出的模型名称列表。如果不提供，将导出所有模型 |

**响应示例 - 成功**
```json
{
    "status": "success",
    "message": "Exported 3 model(s) successfully",
    "results": [
        {
            "model": "iPhone",
            "non_historical_file": "iPhone_test.xlsx",
            "historical_file": "iPhone_test_20260103_143052.xlsx",
            "upload_status": "success",
            "non_historical_upload": {
                "status": "success",
                "message": "File uploaded successfully to https://nextcloud.example.com/.../No_aggregated_raw_data/iPhone_test.xlsx",
                "url": "https://nextcloud.example.com/.../No_aggregated_raw_data/iPhone_test.xlsx"
            },
            "historical_upload": {
                "status": "success",
                "message": "File uploaded successfully to https://nextcloud.example.com/.../data_platform/iPhone_test_20260103_143052.xlsx",
                "url": "https://nextcloud.example.com/.../data_platform/iPhone_test_20260103_143052.xlsx"
            }
        },
        {
            "model": "iPad",
            "non_historical_file": "iPad_test.xlsx",
            "historical_file": "iPad_test_20260103_143052.xlsx",
            "upload_status": "success",
            "non_historical_upload": {
                "status": "success",
                "message": "File uploaded successfully...",
                "url": "..."
            },
            "historical_upload": {
                "status": "success",
                "message": "File uploaded successfully...",
                "url": "..."
            }
        },
        {
            "model": "Inventory",
            "non_historical_file": "Inventory_test.xlsx",
            "historical_file": "Inventory_test_20260103_143053.xlsx",
            "upload_status": "success",
            "non_historical_upload": {
                "status": "success",
                "message": "File uploaded successfully...",
                "url": "..."
            },
            "historical_upload": {
                "status": "success",
                "message": "File uploaded successfully...",
                "url": "..."
            }
        }
    ]
}
```

**响应示例 - 历史追溯关闭时**

当 `ENABLE_EXCEL_HISTORICAL_TRACKING = False` 时：

```json
{
    "status": "success",
    "message": "Exported 1 model(s) successfully",
    "results": [
        {
            "model": "iPhone",
            "non_historical_file": "iPhone_test.xlsx",
            "upload_status": "success",
            "non_historical_upload": {
                "status": "success",
                "message": "File uploaded successfully...",
                "url": "..."
            },
            "historical_upload": {
                "status": "skipped",
                "message": "Historical tracking is disabled"
            }
        }
    ]
}
```

**响应示例 - 部分成功**
```json
{
    "status": "partial_success",
    "message": "Exported 2 model(s) successfully",
    "results": [
        {
            "model": "iPhone",
            "non_historical_file": "iPhone_test.xlsx",
            "upload_status": "success",
            "non_historical_upload": {...},
            "historical_upload": {...}
        },
        {
            "model": "iPad",
            "non_historical_file": "iPad_test.xlsx",
            "upload_status": "success",
            "non_historical_upload": {...},
            "historical_upload": {...}
        }
    ],
    "errors": [
        {
            "model": "InvalidModel",
            "error": "No exporter found for model 'InvalidModel'"
        }
    ]
}
```

**响应示例 - 请求错误**
```json
{
    "status": "error",
    "message": "models must be a list of model names"
}
```

---

## 导出字段说明

每个模型的导出字段如下：

### iPhone / iPad
| 字段 | 表头名称 |
|------|----------|
| id | ID |
| part_number | Part Number |
| model_name | Model Name |
| capacity_gb | Capacity (GB) |
| color | Color |
| release_date | Release Date |
| jan | JAN Code |
| created_at | Created At |
| updated_at | Updated At |

### Inventory
| 字段 | 表头名称 |
|------|----------|
| id | ID |
| uuid | UUID |
| flag | Flag |
| iphone | iPhone Product |
| ipad | iPad Product |
| source1 | Source 1 (EC Site) |
| source2 | Source 2 (Purchasing) |
| source3 | Source 3 (Legal Person Offline) |
| source4 | Source 4 (Temporary Channel) |
| transaction_confirmed_at | Transaction Confirmed At |
| scheduled_arrival_at | Scheduled Arrival At |
| checked_arrival_at_1 | Checked Arrival Time 1 |
| checked_arrival_at_2 | Checked Arrival Time 2 |
| actual_arrival_at | Actual Arrival At |
| status | Status |
| created_at | Created At |
| updated_at | Updated At |

### Purchasing
| 字段 | 表头名称 |
|------|----------|
| id | ID |
| uuid | UUID |
| order_number | Order Number |
| official_account | Official Account |
| created_at | Created At |
| confirmed_at | Confirmed At |
| shipped_at | Shipped At |
| estimated_website_arrival_date | Estimated Website Arrival Date |
| tracking_number | Tracking Number |
| estimated_delivery_date | Estimated Delivery Date |
| delivery_status | Delivery Status |
| last_info_updated_at | Last Info Updated At |
| account_used | Account Used |
| payment_method | Payment Method |
| is_locked | Is Locked |
| locked_at | Locked At |
| locked_by_worker | Locked By Worker |
| updated_at | Updated At |

### OfficialAccount
| 字段 | 表头名称 |
|------|----------|
| id | ID |
| uuid | UUID |
| account_id | Account ID |
| email | Email |
| name | Name |
| postal_code | Postal Code |
| address_line_1 | Address Line 1 |
| address_line_2 | Address Line 2 |
| address_line_3 | Address Line 3 |
| passkey | Passkey |
| batch_encoding | Batch Encoding |
| created_at | Created At |
| updated_at | Updated At |

### GiftCard
| 字段 | 表头名称 |
|------|----------|
| id | ID |
| card_number | Card Number |
| alternative_name | Alternative Name |
| passkey1 | Passkey 1 |
| passkey2 | Passkey 2 |
| balance | Balance |
| batch_encoding | Batch Encoding |
| created_at | Created At |
| updated_at | Updated At |

### DebitCard
| 字段 | 表头名称 |
|------|----------|
| id | ID |
| card_number | Card Number |
| alternative_name | Alternative Name |
| expiry_month | Expiry Month |
| expiry_year | Expiry Year |
| passkey | Passkey |
| last_balance_update | Last Balance Update |
| balance | Balance |
| batch_encoding | Batch Encoding |
| created_at | Created At |
| updated_at | Updated At |

### CreditCard
| 字段 | 表头名称 |
|------|----------|
| id | ID |
| card_number | Card Number |
| alternative_name | Alternative Name |
| expiry_month | Expiry Month |
| expiry_year | Expiry Year |
| passkey | Passkey |
| last_balance_update | Last Balance Update |
| credit_limit | Credit Limit |
| batch_encoding | Batch Encoding |
| created_at | Created At |
| updated_at | Updated At |

### GiftCardPayment / DebitCardPayment / CreditCardPayment
| 字段 | 表头名称 |
|------|----------|
| id | ID |
| gift_card / debit_card / credit_card | Gift Card / Debit Card / Credit Card |
| purchasing | Purchasing Order |
| payment_amount | Payment Amount |
| payment_time | Payment Time |
| payment_status | Payment Status |
| created_at | Created At |
| updated_at | Updated At |

### OtherPayment
| 字段 | 表头名称 |
|------|----------|
| id | ID |
| purchasing | Purchasing Order |
| payment_info | Payment Info |
| payment_amount | Payment Amount |
| payment_time | Payment Time |
| payment_status | Payment Status |
| created_at | Created At |
| updated_at | Updated At |

---

## 使用示例

### Python (requests)

```python
import requests

base_url = "http://your-domain.com/api/aggregation/export-to-excel/"
headers = {
    "Authorization": "Token your_token_here",
    "Content-Type": "application/json"
}

# 1. 获取可用模型列表
response = requests.get(base_url, headers=headers)
available_models = response.json()
print(f"可用模型: {available_models['available_models']}")

# 2. 导出指定模型
export_data = {
    "models": ["iPhone", "iPad", "Inventory"]
}
response = requests.post(base_url, json=export_data, headers=headers)
result = response.json()

# 检查导出结果
if result['status'] == 'success':
    print(f"成功导出 {len(result['results'])} 个模型")
    for item in result['results']:
        print(f"  - {item['model']}: {item['non_historical_file']}")
        if 'historical_file' in item:
            print(f"    历史版本: {item['historical_file']}")
else:
    print(f"导出状态: {result['status']}")
    if 'errors' in result:
        for error in result['errors']:
            print(f"  错误: {error['model']} - {error['error']}")

# 3. 导出所有模型（不指定 models 参数）
response = requests.post(base_url, json={}, headers=headers)
result = response.json()
print(f"导出所有模型: {result['message']}")
```

### cURL

```bash
# 获取可用模型列表
curl -X GET "https://your-domain.com/api/aggregation/export-to-excel/" \
  -H "Authorization: Bearer <BATCH_STATS_API_TOKEN>"

# 导出指定模型
curl -X POST "https://your-domain.com/api/aggregation/export-to-excel/" \
  -H "Authorization: Bearer <BATCH_STATS_API_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"models": ["iPhone", "iPad", "Inventory"]}'

# 导出所有模型
curl -X POST "https://your-domain.com/api/aggregation/export-to-excel/" \
  -H "Authorization: Bearer <BATCH_STATS_API_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{}'
```

### JavaScript (fetch)

```javascript
const baseUrl = 'https://your-domain.com/api/aggregation/export-to-excel/';
const headers = {
    'Authorization': 'Token your_token_here',
    'Content-Type': 'application/json'
};

// 获取可用模型列表
async function getAvailableModels() {
    const response = await fetch(baseUrl, { headers });
    const data = await response.json();
    console.log('可用模型:', data.available_models);
    return data;
}

// 导出指定模型
async function exportModels(models) {
    const response = await fetch(baseUrl, {
        method: 'POST',
        headers,
        body: JSON.stringify({ models })
    });
    const data = await response.json();

    if (data.status === 'success') {
        console.log(`成功导出 ${data.results.length} 个模型`);
        data.results.forEach(item => {
            console.log(`  - ${item.model}: ${item.non_historical_file}`);
        });
    }
    return data;
}

// 使用示例
getAvailableModels();
exportModels(['iPhone', 'iPad', 'Inventory']);
```

---

## 文件存储结构

导出后的文件在 Nextcloud 中的存储结构如下：

```
Nextcloud Root/
├── No_aggregated_raw_data/           # 非历史追溯目录（当前状态）
│   ├── iPhone_test.xlsx              # 最新的 iPhone 数据
│   ├── iPad_test.xlsx                # 最新的 iPad 数据
│   ├── Inventory_test.xlsx           # 最新的库存数据
│   ├── Purchasing_test.xlsx          # 最新的采购订单数据
│   └── ...                           # 其他模型
│
└── data_platform/                    # 历史追溯目录（带时间戳）
    ├── iPhone_test_20260101_120000.xlsx
    ├── iPhone_test_20260102_120000.xlsx
    ├── iPhone_test_20260103_143052.xlsx
    ├── iPad_test_20260101_120000.xlsx
    ├── iPad_test_20260102_120000.xlsx
    └── ...                           # 历史版本文件
```

---

## 状态码说明

| 状态码 | 说明 |
|--------|------|
| 200 | 请求成功（GET 和 POST） |
| 400 | 请求参数错误（如 models 不是数组） |
| 401 | 认证失败（Token 无效或缺失） |
| 500 | 服务器内部错误 |

---

## 响应状态说明

| status 值 | 说明 |
|-----------|------|
| `success` | 所有请求的模型都成功导出 |
| `partial_success` | 部分模型导出成功，部分失败（查看 errors 字段） |
| `error` | 所有模型导出失败或请求参数错误 |

### upload_status 值

| upload_status 值 | 说明 |
|------------------|------|
| `success` | 两个版本都上传成功 |
| `partial_success` | 只有一个版本上传成功 |
| `error` | 两个版本都上传失败 |

### historical_upload.status 值

| status 值 | 说明 |
|-----------|------|
| `success` | 历史版本上传成功 |
| `error` | 历史版本上传失败 |
| `skipped` | 历史追溯功能已禁用 |

---

## 注意事项

1. **认证要求**: 所有请求都需要在 Header 中提供有效的 Token
2. **大数据集**: 对于数据量大的模型，导出可能需要较长时间
3. **网络依赖**: 此 API 依赖 Nextcloud 服务器的可用性
4. **时间戳格式**: 历史版本文件名中的时间戳格式为 `YYYYMMDD_HHMMSS`
5. **覆盖行为**: 非历史版本文件会覆盖同名文件，确保只保留最新状态
6. **敏感数据**: 导出的 Excel 文件可能包含敏感信息（如 passkey），请注意数据安全

---

## 错误处理

### 常见错误及解决方法

| 错误信息 | 原因 | 解决方法 |
|----------|------|----------|
| `No exporter found for model 'XXX'` | 指定的模型名称不存在 | 检查模型名称拼写，使用 GET 请求获取可用模型列表 |
| `models must be a list of model names` | models 参数格式错误 | 确保 models 是一个字符串数组 |
| `Failed to create or access directory` | Nextcloud 目录创建失败 | 检查 Nextcloud 配置和权限 |
| `Upload failed with status code XXX` | 文件上传失败 | 检查 Nextcloud 服务器状态和网络连接 |

---

## 相关文档

- [Excel Exporters 架构](../apps/data_aggregation/excel_exporters/README.md)
- [API 总览](./API_OVERVIEW.md)
- [Purchasing API](./API_PURCHASING.md)
- [Inventory API](./API_INVENTORY.md)

---

## 更新日志

| 日期 | 版本 | 说明 |
|------|------|------|
| 2026-01-03 | 1.1 | 新增 GiftCardPayment 和 OtherPayment 导出器 |
| 2026-01-03 | 1.1 | 更新导出器字段（batch_encoding, alternative_name, lock 字段等） |
| 2025-01-01 | 1.0 | 初始版本，支持双版本导出机制 |
