# iPhone Inventory Dashboard JSON API

## 概述

本功能提供 iPhone 库存数据的 JSON 格式 API，使用与 Excel 导出功能相同的数据汇总逻辑。该 API 可用于前端展示、数据集成或其他需要获取库存数据的场景。

## API 端点

```
GET /api/aggregation/iphone-inventory-dashboard-data/
```

### 认证

使用 `BATCH_STATS_API_TOKEN` 通过 Authorization header 认证：
```
Authorization: Bearer <BATCH_STATS_API_TOKEN>
```

### 响应格式

#### 成功响应 (200 OK)

```json
{
    "status": "success",
    "data": [
        {
            "iphone": "iPhone 16 Pro 256GB ブラック",
            "imei": "123456789012345",
            "batch_level_1": "2024-01",
            "batch_level_2": "A",
            "batch_level_3": "001",
            "source1": "✓",
            "source2": "✓",
            "source3": "",
            "source4": "",
            "transaction_confirmed_at": "2025-01-10 15:30:00",
            "scheduled_arrival_at": "2025-01-15 10:00:00",
            "checked_arrival_at_1": "",
            "checked_arrival_at_2": "",
            "actual_arrival_at": "",
            "status": "pending",
            "updated_at": "2025-01-11 08:20:00",
            "ecsite_reservation_number": "EC20250110-001",
            "ecsite_username": "user@example.com",
            "ecsite_method": "pickup",
            "ecsite_reservation_time": "2025-01-10 14:00:00",
            "ecsite_visit_time": "",
            "ecsite_order_created_at": "2025-01-10 14:05:00",
            "ecsite_info_updated_at": "2025-01-11 08:00:00",
            "ecsite_order_detail_url": "https://example.com/orders/12345",
            "purchasing_order_number": "PO-2025-001",
            "purchasing_official_account": "✓",
            "purchasing_confirmed_at": "2025-01-10 16:00:00",
            "purchasing_shipped_at": "2025-01-11 09:00:00",
            "purchasing_estimated_website_arrival_date": "2025-01-15",
            "purchasing_estimated_website_arrival_date_2": "",
            "purchasing_tracking_number": "1234567890",
            "purchasing_estimated_delivery_date": "2025-01-15",
            "purchasing_latest_delivery_status": "in_transit",
            "purchasing_delivery_status_query_time": "2025-01-11 11:30:00",
            "purchasing_delivery_status_query_source": "tracking_site",
            "purchasing_official_query_url": "https://track.example.com/1234567890",
            "purchasing_shipping_method": "Express",
            "purchasing_last_info_updated_at": "2025-01-11 12:00:00",
            "purchasing_payment_method": "credit_card",
            "purchasing_account_used": "official@example.com",
            "purchasing_updated_at": "2025-01-11 12:05:00",
            "purchasing_creation_source": "API",
            "official_account_email": "official@example.com",
            "official_account_name": "山田太郎",
            "official_account_postal_code": "100-0001",
            "official_account_address_line_1": "東京都千代田区",
            "official_account_address_line_2": "丸の内1-1-1",
            "official_account_address_line_3": "ビル101号室",
            "card_numbers": "1234567890｜9876543210",
            "legal_person_username": "",
            "legal_person_appointment_time": "",
            "legal_person_visit_time": "",
            "legal_person_updated_at": "",
            "temp_channel_created_time": "",
            "temp_channel_expected_time": "",
            "temp_channel_record": "",
            "temp_channel_last_updated": ""
        },
        ...更多记录...
    ],
    "count": 150,
    "field_headers": {
        "iphone": "iPhone機種",
        "imei": "IMEI",
        "batch_level_1": "バッチレベル1",
        "batch_level_2": "バッチレベル2",
        "batch_level_3": "バッチレベル3",
        "source1": "ソース1",
        "source2": "ソース2",
        "source3": "ソース3",
        "source4": "ソース4",
        ...更多字段映射...
    }
}
```

#### 错误响应 (500 Internal Server Error)

```json
{
    "status": "error",
    "message": "Unexpected error: ..."
}
```

### 响应字段说明

| 字段名 | 类型 | 说明 |
|--------|------|------|
| status | string | 响应状态：success 或 error |
| data | array | 库存数据列表，每项包含所有字段 |
| count | integer | 返回的记录总数 |
| field_headers | object | 字段名到日文表头的映射字典 |

## 数据字段详细说明

本 API 返回的数据字段与 Excel 导出功能完全相同。详细字段列表请参考：
- [iphone_inventory_dashboard_export.md - 导出字段列表](./iphone_inventory_dashboard_export.md#导出字段列表)

### 字段总览

- **基础 Inventory 字段**: 16个
- **EcSite (source1) 关联字段**: 8个
- **Purchasing (source2) 关联字段**: 18个
- **OfficialAccount 关联字段**: 6个
- **Payment 关联字段**: 1个
- **LegalPersonOffline (source3) 关联字段**: 4个
- **TemporaryChannel (source4) 关联字段**: 4个

**总计**: 57个字段

## 数据格式说明

### iPhone 组合信息格式
- 格式：`{model_name} {capacity} {color}`
- 示例：`iPhone 16 Pro 256GB ブラック`
- 1024GB 显示为 1T

### 日期时间格式
- 格式：`YYYY-MM-DD HH:MM:SS`
- 示例：`2025-01-11 10:30:00`
- 空值显示为空字符串 `""`

### 日期格式
- 格式：`YYYY-MM-DD`
- 示例：`2025-01-11`
- 空值显示为空字符串 `""`

### Source 指示符
- 有值：`"✓"`
- 无值：`""`（空字符串）

### 卡号格式
- 多个卡号用全角 `｜` 分隔
- 示例：`"1234567890｜9876543210"`
- 无卡号时为空字符串 `""`

## 使用示例

### cURL 请求

```bash
curl -X GET \
  'http://your-server/api/aggregation/iphone-inventory-dashboard-data/' \
  -H 'Authorization: Bearer YOUR_BATCH_STATS_API_TOKEN' \
  -H 'Accept: application/json'
```

### Python 请求

```python
import requests

url = 'http://your-server/api/aggregation/iphone-inventory-dashboard-data/'
headers = {
    'Authorization': 'Bearer YOUR_BATCH_STATS_API_TOKEN',
    'Accept': 'application/json'
}

response = requests.get(url, headers=headers)

if response.status_code == 200:
    result = response.json()
    print(f"成功获取 {result['count']} 条记录")

    # 访问数据
    for record in result['data']:
        print(f"IMEI: {record['imei']}, iPhone: {record['iphone']}")

    # 访问字段表头
    headers_map = result['field_headers']
    print(f"IMEI 的日文表头: {headers_map['imei']}")
else:
    print(f"请求失败: {response.status_code}")
    print(response.json())
```

### JavaScript/TypeScript 请求

```javascript
const url = 'http://your-server/api/aggregation/iphone-inventory-dashboard-data/';
const headers = {
    'Authorization': 'Bearer YOUR_BATCH_STATS_API_TOKEN',
    'Accept': 'application/json'
};

fetch(url, { headers })
    .then(response => response.json())
    .then(result => {
        if (result.status === 'success') {
            console.log(`成功获取 ${result.count} 条记录`);

            // 访问数据
            result.data.forEach(record => {
                console.log(`IMEI: ${record.imei}, iPhone: ${record.iphone}`);
            });

            // 访问字段表头
            console.log(`IMEI 的日文表头: ${result.field_headers.imei}`);
        } else {
            console.error('请求失败:', result.message);
        }
    })
    .catch(error => console.error('网络错误:', error));
```

## 与 Excel 导出 API 的关系

本 JSON API 与 Excel 导出 API 使用**完全相同的数据汇总逻辑**：

| 特性 | Excel 导出 API | JSON API |
|------|---------------|----------|
| 端点 | `POST /api/aggregation/export-iphone-inventory-dashboard/` | `GET /api/aggregation/iphone-inventory-dashboard-data/` |
| 认证 | BATCH_STATS_API_TOKEN | BATCH_STATS_API_TOKEN |
| 数据源 | `iPhoneInventoryDashboardExporter.prepare_data()` | `iPhoneInventoryDashboardExporter.prepare_data()` |
| 数据字段 | 50个字段 | 50个字段（完全相同） |
| 输出格式 | Excel 文件（上传到 Nextcloud） | JSON 响应 |
| 用途 | Dashboard 可视化（Excel） | 前端展示、数据集成 |

## 实现架构

### 代码重用设计

```
┌─────────────────────────────────────────────────────┐
│  iPhoneInventoryDashboardExporter                   │
│                                                       │
│  ┌───────────────────────────────────────────────┐  │
│  │ prepare_data()                                 │  │
│  │ - 查询数据库                                    │  │
│  │ - 关联查询 (select_related, prefetch_related)  │  │
│  │ - 格式化所有字段                                │  │
│  │ - 返回字典列表                                  │  │
│  └────────────────┬──────────────────────────────┘  │
└────────────────────┼────────────────────────────────┘
                     │
         ┌───────────┴───────────┐
         │                       │
         ▼                       ▼
┌────────────────────┐  ┌───────────────────────┐
│ export()           │  │ JSON API              │
│ - 调用 prepare_data│  │ - 调用 prepare_data   │
│ - 写入 Excel       │  │ - 返回 JSON           │
│ - 上传到 Nextcloud │  │                       │
└────────────────────┘  └───────────────────────┘
```

### 核心方法

**prepare_data()** - 数据准备方法
- 位置：`apps/data_aggregation/excel_exporters/iphone_inventory_dashboard_exporter.py:205`
- 功能：收集并格式化所有 iPhone 库存数据
- 返回：`list[dict]` - 字典列表，每个字典代表一条库存记录

## 性能考虑

### 查询优化
- 使用 `select_related()` 预加载外键关联
- 使用 `prefetch_related()` 预加载多对多关联
- 单次查询获取所有必要的关联数据

### 数据量
- 根据实际库存数量，响应数据可能较大
- 建议在前端实现分页或虚拟滚动
- 考虑添加缓存机制（如有需要）

## 文件修改列表

### 修改的文件
1. `apps/data_aggregation/excel_exporters/iphone_inventory_dashboard_exporter.py`
   - 添加 `prepare_data()` 方法（第205行）

2. `apps/data_aggregation/views.py`
   - 添加 `get_iphone_inventory_dashboard_data()` API 视图（第1462行）

3. `apps/data_aggregation/urls.py`
   - 添加导入 `get_iphone_inventory_dashboard_data`
   - 添加 `/iphone-inventory-dashboard-data/` 路由

### 文档文件
- 本文档：`docs/iphone_inventory_dashboard_json_api.md`

## 常见问题

### Q: JSON API 和 Excel 导出 API 的数据一致吗？
**A**: 是的，完全一致。两个 API 使用相同的 `prepare_data()` 方法获取和格式化数据。

### Q: 如何使用 field_headers 字段？
**A**: `field_headers` 提供了字段名到日文表头的映射，可用于：
- 动态生成表格列标题
- 显示用户友好的字段名称
- 国际化支持

示例：
```python
headers = result['field_headers']
print(headers['imei'])  # 输出: "IMEI"
print(headers['iphone'])  # 输出: "iPhone機種"
```

### Q: 返回的数据是否包含已删除的记录？
**A**: 不包含。查询条件中包含 `is_deleted=False`，只返回未删除的记录。

### Q: 如何只获取特定条件的数据？
**A**: 当前 API 返回所有符合条件的 iPhone 库存数据。如需筛选，可以：
1. 在客户端进行数据过滤
2. 根据需求扩展 API，添加查询参数支持

### Q: API 有速率限制吗？
**A**: API 使用 token 认证，请根据实际负载情况合理调用。如需高频访问，建议实现客户端缓存。

## 相关文档

- [iPhone Inventory Dashboard Excel 导出功能](./iphone_inventory_dashboard_export.md) - Excel 导出 API 详细文档
- [API_IPHONE.md](./API_IPHONE.md) - iPhone 相关 API 总览

## 更新历史

- **2025-01-12**: 首次创建文档，添加 JSON API 说明
