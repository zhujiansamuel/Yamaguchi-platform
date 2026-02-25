# iPhone Inventory Dashboard Excel 导出功能

## 概述

本功能实现了将 iPhone 库存数据导出到 Nextcloud 的 `Data_Dashboard` 文件夹中的 Excel 文件。

## API 端点

```
POST /api/aggregation/export-iphone-inventory-dashboard/
```

### 认证

使用 `BATCH_STATS_API_TOKEN` 通过 Authorization header 认证：
```
Authorization: Bearer <BATCH_STATS_API_TOKEN>
```

### 响应示例

```json
{
    "status": "success",
    "message": "Successfully exported iPhone inventory to iPhone inventory.xlsx",
    "filename": "iPhone inventory.xlsx",
    "url": "http://nextcloud-web/remote.php/dav/files/Data-Platform/Data_Dashboard/iPhone inventory.xlsx",
    "file_existed": false
}
```

## Excel 文件规格

### 文件结构
- **第1行**: 变量名（隐藏）
- **第2行**: 日文表头
- **第3行起**: 数据

### 单元格保护
- 工作表密码保护：`Xdb73008762`
- 只有 `batch_level_1`、`batch_level_2`、`batch_level_3` 三列可编辑
- 其他所有列都被锁定

### 文件命名
- 默认文件名：`iPhone inventory.xlsx`
- 支持任意后缀名（如 `.xlsm` 用于带宏的版本）
- 系统会自动查找以 "iPhone inventory" 开头的文件

## 导出字段列表

### 基础 Inventory 字段（16个）

| 变量名 | 日文表头 | 说明 |
|--------|----------|------|
| iphone | iPhone機種 | iPhone 组合信息（如 "iPhone 16 Pro 256GB ブラック"） |
| imei | IMEI | IMEI 号 |
| batch_level_1 | バッチレベル1 | 批次1（**可编辑**） |
| batch_level_2 | バッチレベル2 | 批次2（**可编辑**） |
| batch_level_3 | バッチレベル3 | 批次3（**可编辑**） |
| source1 | ソース1 | EcSite 来源（有值显示 ✓） |
| source2 | ソース2 | Purchasing 来源（有值显示 ✓） |
| source3 | ソース3 | LegalPersonOffline 来源（有值显示 ✓） |
| source4 | ソース4 | TemporaryChannel 来源（有值显示 ✓） |
| transaction_confirmed_at | 取引確認日時 | 交易确认时间 |
| scheduled_arrival_at | 到着予定日時 | 计划到达时间 |
| checked_arrival_at_1 | 確認到着日時1 | 检查到达时间1 |
| checked_arrival_at_2 | 確認到着日時2 | 检查到达时间2 |
| actual_arrival_at | 実際到着日時 | 实际到达时间 |
| status | ステータス | 状态 |
| updated_at | 更新日時 | 更新时间 |

### EcSite (source1) 关联字段（8个）

| 变量名 | 日文表头 | 说明 |
|--------|----------|------|
| ecsite_reservation_number | 予約番号 | 预约号 |
| ecsite_username | ECサイトユーザー名 | EC站点用户名 |
| ecsite_method | 方法 | 方式 |
| ecsite_reservation_time | 予約日時 | 预约时间 |
| ecsite_visit_time | 訪問日時 | 访问时间 |
| ecsite_order_created_at | 注文作成日時 | 订单创建时间 |
| ecsite_info_updated_at | 情報更新日時 | 信息更新时间 |
| ecsite_order_detail_url | 注文詳細URL | 订单详情URL |

### Purchasing (source2) 关联字段（18个）

| 变量名 | 日文表头 | 说明 |
|--------|----------|------|
| purchasing_order_number | 注文番号 | 订单号 |
| purchasing_official_account | 公式アカウント | 官方账号（有值显示 ✓） |
| purchasing_confirmed_at | 確認日時 | 确认时间 |
| purchasing_shipped_at | 発送日時 | 发货时间 |
| purchasing_estimated_website_arrival_date | 公式サイト到着予定日 | 官网预计到达日期 |
| purchasing_estimated_website_arrival_date_2 | 公式サイト到着予定日2 | 官网预计到达日期2 |
| purchasing_tracking_number | 追跡番号 | 追踪号 |
| purchasing_estimated_delivery_date | 配達予定日 | 配送预定日 |
| purchasing_latest_delivery_status | 最新配達状況 | 最新配送状态 |
| purchasing_delivery_status_query_time | 配送状況照会日時 | 配送状态查询时间 |
| purchasing_delivery_status_query_source | 配送状況照会元 | 配送状态查询来源 |
| purchasing_official_query_url | 公式照会URL | 官方查询URL |
| purchasing_shipping_method | 配送方法 | 配送方式 |
| purchasing_last_info_updated_at | 最終情報更新日時 | 最后信息更新时间 |
| purchasing_payment_method | 支払方法 | 支付方式 |
| purchasing_account_used | 使用アカウント | 使用账号 |
| purchasing_updated_at | 購入更新日時 | 采购更新时间 |
| purchasing_creation_source | 作成元 | 创建来源 |

### OfficialAccount 关联字段（6个）

| 变量名 | 日文表头 | 说明 |
|--------|----------|------|
| official_account_email | メールアドレス | 邮箱地址 |
| official_account_name | 名前 | 名称 |
| official_account_postal_code | 郵便番号 | 邮政编码 |
| official_account_address_line_1 | 住所1 | 地址1 |
| official_account_address_line_2 | 住所2 | 地址2 |
| official_account_address_line_3 | 住所3 | 地址3 |

### Payment 关联字段（1个）

| 变量名 | 日文表头 | 说明 |
|--------|----------|------|
| card_numbers | カード番号 | 关联卡号（多个用 ｜ 分隔） |

### LegalPersonOffline (source3) 关联字段（4个）

| 变量名 | 日文表头 | 说明 |
|--------|----------|------|
| legal_person_username | 法人ユーザー名 | 法人用户名 |
| legal_person_appointment_time | 予約日時 | 预约时间 |
| legal_person_visit_time | 法人訪問日時 | 法人访问时间 |
| legal_person_updated_at | 法人更新日時 | 法人更新时间 |

### TemporaryChannel (source4) 关联字段（4个）

| 变量名 | 日文表头 | 说明 |
|--------|----------|------|
| temp_channel_created_time | 一時チャネル作成日時 | 临时渠道创建时间 |
| temp_channel_expected_time | 入庫予定日時 | 入库预定时间 |
| temp_channel_record | 記録 | 记录 |
| temp_channel_last_updated | 一時チャネル更新日時 | 临时渠道更新时间 |

## 数据格式说明

### iPhone 组合信息格式
- 格式：`{model_name} {capacity} {color}`
- 示例：`iPhone 16 Pro 256GB ブラック`
- 1024GB 显示为 1T

### 日期时间格式
- 格式：`YYYY-MM-DD HH:MM:SS`
- 示例：`2025-01-11 10:30:00`

### 日期格式
- 格式：`YYYY-MM-DD`
- 示例：`2025-01-11`

### Source 指示符
- 有值：`✓`
- 无值：空

### 卡号格式
- 多个卡号用全角 `｜` 分隔
- 示例：`1234567890｜9876543210`

## 文件修改列表

### 新增文件
1. `apps/data_aggregation/excel_exporters/iphone_inventory_dashboard_exporter.py`
   - iPhone 库存 Dashboard 导出器类

### 修改文件
1. `apps/data_aggregation/excel_exporters/__init__.py`
   - 添加 `iPhoneInventoryDashboardExporter` 导入
   - 添加 `DASHBOARD_EXPORTER_REGISTRY`
   - 添加 `get_dashboard_exporter()` 函数

2. `apps/data_aggregation/utils.py`
   - 添加 `download_from_nextcloud()` 函数
   - 添加 `find_file_in_nextcloud()` 函数
   - 添加 `export_iphone_inventory_dashboard()` 函数

3. `apps/data_aggregation/views.py`
   - 添加 `export_iphone_inventory_dashboard()` API 视图

4. `apps/data_aggregation/urls.py`
   - 添加 `/export-iphone-inventory-dashboard/` 路由

5. `config/settings/base.py`
   - 添加 `EXCEL_OUTPUT_PATH_DASHBOARD = 'Data_Dashboard/'` 配置

## 使用示例

### cURL 请求
```bash
curl -X POST \
  'http://your-server/api/aggregation/export-iphone-inventory-dashboard/' \
  -H 'Authorization: Bearer YOUR_BATCH_STATS_API_TOKEN' \
  -H 'Content-Type: application/json'
```

### Python 请求
```python
import requests

response = requests.post(
    'http://your-server/api/aggregation/export-iphone-inventory-dashboard/',
    headers={
        'Authorization': 'Bearer YOUR_BATCH_STATS_API_TOKEN',
        'Content-Type': 'application/json'
    }
)

print(response.json())
```
