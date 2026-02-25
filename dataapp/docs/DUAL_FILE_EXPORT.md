# Excel 双文件导出系统

## 概述

Excel 导出系统现在支持双文件导出模式，每次导出会生成两个文件：

1. **最新版本文件**（非历史追溯）- 总是覆盖，保持最新
2. **历史版本文件**（历史追溯）- 带时间戳，可选开启

## 文件存储位置

### 1. 非历史追溯文件
- **目录**: `No_aggregated_raw_data/`
- **文件名格式**: `{模型名}_test.xlsx`
- **示例**: `iPhone_test.xlsx`, `iPad_test.xlsx`
- **行为**: 每次导出覆盖已存在的文件
- **用途**: 快速访问最新数据，无需查找时间戳

### 2. 历史追溯文件
- **目录**: `data_platform/`
- **文件名格式**: `{模型名}_test_{时间戳}.xlsx`
- **示例**: `iPhone_test_20250101_120000.xlsx`
- **行为**: 每次导出创建新文件
- **用途**: 保存历史记录，支持版本回溯和审计

## 配置说明

### 配置文件位置
`config/settings/base.py`

### 可用配置项

```python
# 历史追溯文件目录（带时间戳）
EXCEL_OUTPUT_PATH = 'data_platform/'

# 非历史追溯文件目录（不带时间戳，覆盖式）
EXCEL_OUTPUT_PATH_NO_HISTORY = 'No_aggregated_raw_data/'

# 是否启用历史追溯功能
ENABLE_EXCEL_HISTORICAL_TRACKING = True  # 默认启用
```

### 通过环境变量控制

在 `.env` 文件中添加：

```bash
# 启用历史追溯（默认）
ENABLE_EXCEL_HISTORICAL_TRACKING=True

# 禁用历史追溯（仅保留最新版本）
ENABLE_EXCEL_HISTORICAL_TRACKING=False
```

## 工作流程

### 启用历史追溯时（默认）

```
导出请求
    ↓
生成 Excel 文件
    ↓
上传到两个位置:
    ├─→ No_aggregated_raw_data/iPhone_test.xlsx (覆盖)
    └─→ data_platform/iPhone_test_20250101_120000.xlsx (新建)
```

### 禁用历史追溯时

```
导出请求
    ↓
生成 Excel 文件
    ↓
仅上传到一个位置:
    └─→ No_aggregated_raw_data/iPhone_test.xlsx (覆盖)
```

## API 使用示例

### 请求

```bash
POST /api/aggregation/export-to-excel/
Content-Type: application/json
Authorization: Token your-token-here

{
    "models": ["iPhone", "iPad"]
}
```

### 响应（启用历史追溯时）

```json
{
    "status": "success",
    "message": "Exported 2 model(s) successfully",
    "results": [
        {
            "model": "iPhone",
            "non_historical_file": "iPhone_test.xlsx",
            "historical_file": "iPhone_test_20250101_120000.xlsx",
            "upload_status": "success",
            "non_historical_upload": {
                "status": "success",
                "message": "File uploaded successfully to ...",
                "url": "http://..."
            },
            "historical_upload": {
                "status": "success",
                "message": "File uploaded successfully to ...",
                "url": "http://..."
            }
        },
        {
            "model": "iPad",
            "non_historical_file": "iPad_test.xlsx",
            "historical_file": "iPad_test_20250101_120000.xlsx",
            "upload_status": "success",
            "non_historical_upload": {...},
            "historical_upload": {...}
        }
    ]
}
```

### 响应（禁用历史追溯时）

```json
{
    "status": "success",
    "message": "Exported 2 model(s) successfully",
    "results": [
        {
            "model": "iPhone",
            "non_historical_file": "iPhone_test.xlsx",
            "upload_status": "success",
            "non_historical_upload": {
                "status": "success",
                "message": "File uploaded successfully to ...",
                "url": "http://..."
            },
            "historical_upload": {
                "status": "skipped",
                "message": "Historical tracking is disabled"
            }
        }
    ]
}
```

## 文件命名规则

### 所有18个模型的文件名

#### 非历史追溯文件（覆盖式）
1. `iPhone_test.xlsx`
2. `iPad_test.xlsx`
3. `Inventory_test.xlsx`
4. `Purchasing_test.xlsx`
5. `OfficialAccount_test.xlsx`
6. `TemporaryChannel_test.xlsx`
7. `LegalPersonOffline_test.xlsx`
8. `EcSite_test.xlsx`
9. `GiftCard_test.xlsx`
10. `DebitCard_test.xlsx`
11. `DebitCardPayment_test.xlsx`
12. `CreditCard_test.xlsx`
13. `CreditCardPayment_test.xlsx`
14. `AggregationSource_test.xlsx`
15. `AggregatedData_test.xlsx`
16. `AggregationTask_test.xlsx`
17. `GiftCardPayment_test.xlsx`
18. `OtherPayment_test.xlsx`

#### 历史追溯文件（带时间戳）
格式：`{模型名}_test_{YYYYMMdd_HHmmss}.xlsx`

示例：
- `iPhone_test_20250101_120000.xlsx`
- `iPad_test_20250101_120005.xlsx`
- `Inventory_test_20250101_120010.xlsx`
- ...

## 导出字段说明

导出字段与各模型实际字段保持一致，字段顺序与 Excel 表头顺序一致。

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
| is_deleted | Is Deleted |

### Inventory
| 字段 | 表头名称 |
|------|----------|
| id | ID |
| uuid | UUID |
| flag | Flag |
| iphone | iPhone Product |
| ipad | iPad Product |
| imei | IMEI |
| batch_level_1 | Batch Level 1 |
| batch_level_2 | Batch Level 2 |
| batch_level_3 | Batch Level 3 |
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
| is_deleted | Is Deleted |

### Purchasing
| 字段 | 表头名称 |
|------|----------|
| id | ID |
| uuid | UUID |
| order_number | Order Number |
| official_account | Official Account |
| batch_encoding | Batch Encoding |
| batch_level_1 | Batch Level 1 |
| batch_level_2 | Batch Level 2 |
| batch_level_3 | Batch Level 3 |
| created_at | Created At |
| confirmed_at | Confirmed At |
| shipped_at | Shipped At |
| estimated_website_arrival_date | Estimated Website Arrival Date |
| estimated_website_arrival_date_2 | Estimated Website Arrival Date 2 |
| tracking_number | Tracking Number |
| estimated_delivery_date | Estimated Delivery Date |
| delivery_status | Delivery Status |
| latest_delivery_status | Latest Delivery Status |
| delivery_status_query_time | Delivery Status Query Time |
| delivery_status_query_source | Delivery Status Query Source |
| official_query_url | Official Query URL |
| shipping_method | Shipping Method |
| last_info_updated_at | Last Info Updated At |
| account_used | Account Used |
| payment_method | Payment Method |
| is_locked | Is Locked |
| locked_at | Locked At |
| locked_by_worker | Locked By Worker |
| updated_at | Updated At |
| is_deleted | Is Deleted |
| creation_source | Creation Source |

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
| is_deleted | Is Deleted |

### TemporaryChannel
| 字段 | 表头名称 |
|------|----------|
| id | ID |
| created_time | Created Time |
| expected_time | Expected Time |
| record | Record |
| last_updated | Last Updated |
| is_deleted | Is Deleted |

### LegalPersonOffline
| 字段 | 表头名称 |
|------|----------|
| id | ID |
| uuid | UUID |
| username | Username |
| appointment_time | Appointment Time |
| visit_time | Visit Time |
| order_created_at | Order Created At |
| updated_at | Updated At |
| is_deleted | Is Deleted |
| creation_source | Creation Source |

### EcSite
| 字段 | 表头名称 |
|------|----------|
| id | ID |
| reservation_number | Reservation Number |
| username | Username |
| method | Method |
| reservation_time | Reservation Time |
| visit_time | Visit Time |
| order_created_at | Order Created At |
| info_updated_at | Info Updated At |
| order_detail_url | Order Detail URL |
| created_at | Created At |
| updated_at | Updated At |
| is_deleted | Is Deleted |

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
| is_deleted | Is Deleted |

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
| is_deleted | Is Deleted |

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
| is_deleted | Is Deleted |

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
| is_deleted | Is Deleted |

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

### AggregationSource
| 字段 | 表头名称 |
|------|----------|
| id | ID |
| name | Source Name |
| description | Description |
| status | Status |
| config | Configuration |
| created_at | Created At |
| updated_at | Updated At |

### AggregatedData
| 字段 | 表头名称 |
|------|----------|
| id | ID |
| source | Aggregation Source |
| data | Aggregated Data |
| metadata | Metadata |
| aggregated_at | Aggregated At |
| created_at | Created At |

### AggregationTask
| 字段 | 表头名称 |
|------|----------|
| id | ID |
| task_id | Celery Task ID |
| source | Aggregation Source |
| status | Status |
| result | Task Result |
| error_message | Error Message |
| started_at | Started At |
| completed_at | Completed At |
| created_at | Created At |

## 使用场景

### 场景 1: 日常数据查看
**需求**: 快速访问最新数据，无需关心历史

**配置**: 保持默认或设置 `ENABLE_EXCEL_HISTORICAL_TRACKING=False`

**操作**: 直接访问 `No_aggregated_raw_data/` 目录下的文件

### 场景 2: 数据审计
**需求**: 需要查看某个时间点的数据快照

**配置**: `ENABLE_EXCEL_HISTORICAL_TRACKING=True`

**操作**: 访问 `data_platform/` 目录，根据时间戳选择文件

### 场景 3: 节省存储空间
**需求**: 只保留最新数据，不保存历史

**配置**: `ENABLE_EXCEL_HISTORICAL_TRACKING=False`

**效果**: 只在 `No_aggregated_raw_data/` 中保存18个文件（每个模型一个）

### 场景 4: 完整历史记录
**需求**: 保留所有导出历史，用于审计和追溯

**配置**: `ENABLE_EXCEL_HISTORICAL_TRACKING=True`

**效果**:
- `No_aggregated_raw_data/`: 18个最新文件
- `data_platform/`: 所有历史版本文件

## 优势

1. **灵活性**: 可以根据需求开启或关闭历史追溯
2. **便利性**: 最新版本文件命名简洁，易于访问
3. **可审计性**: 历史版本带时间戳，便于追溯
4. **空间管理**: 可通过配置控制存储空间使用
5. **向后兼容**: 默认行为与之前相同（保留历史）

## 技术实现

### 核心函数

#### `upload_excel_files(file_content, model_name, timestamp=None)`
位于 `apps/data_aggregation/utils.py`

```python
# 总是上传到非历史追溯目录
upload_to_nextcloud(
    file_content,
    f"{model_name}_test.xlsx",
    directory_path='No_aggregated_raw_data/'
)

# 如果启用历史追溯，也上传到历史目录
if ENABLE_EXCEL_HISTORICAL_TRACKING:
    upload_to_nextcloud(
        file_content,
        f"{model_name}_test_{timestamp}.xlsx",
        directory_path='data_platform/'
    )
```

### 状态码说明

- `success`: 所有上传都成功
- `partial_success`: 部分上传成功
- `error`: 所有上传都失败
- `skipped`: 历史追溯被禁用

## 迁移说明

### 从旧系统迁移

旧系统只生成历史追溯文件（带时间戳）。新系统默认行为相同，但额外提供了最新版本文件。

**无需任何操作即可升级**，新系统向后兼容。

### 清理历史文件

如果要清理旧的历史文件以节省空间：

```bash
# 进入 data_platform 目录
cd data_platform/

# 列出所有历史文件
ls -lt *_test_*.xlsx

# 删除某个日期之前的文件（示例：删除2024年的文件）
rm *_test_2024*.xlsx
```

## 常见问题

### Q: 可以只生成历史文件吗？
A: 不可以。非历史文件（最新版本）总是会生成。这是为了保证用户始终能快速访问最新数据。

### Q: 两个文件的内容一样吗？
A: 是的。在同一次导出中，两个文件的内容完全相同，只是存储位置和文件名不同。

### Q: 禁用历史追溯后，旧的历史文件会被删除吗？
A: 不会。禁用历史追溯只是停止生成新的历史文件，已存在的历史文件不会受影响。

### Q: 如何恢复到旧版本数据？
A: 从 `data_platform/` 目录中找到对应时间戳的文件，复制到 `No_aggregated_raw_data/` 并重命名（去掉时间戳）即可。

### Q: 文件上传失败怎么办？
A: API 响应会包含详细的错误信息。常见原因：
- Nextcloud 连接问题
- 权限不足
- 磁盘空间不足

检查 `non_historical_upload` 和 `historical_upload` 字段的错误详情。

## 维护建议

1. **定期清理历史文件**: 如果启用历史追溯，建议定期清理旧文件
2. **监控磁盘空间**: 历史文件会累积，需要监控存储空间
3. **备份策略**: 建议定期备份 `No_aggregated_raw_data/` 目录
4. **审计策略**: 确定历史文件的保留期限（如：保留90天）

## 总结

双文件导出系统为用户提供了：
- ✅ 快速访问最新数据的便利性
- ✅ 保留历史记录的可选能力
- ✅ 灵活的配置选项
- ✅ 向后兼容的设计

这使得系统既能满足日常使用需求，又能支持审计和追溯场景。
