# EcSite 模型说明文档

## 概述

EcSite 模型用于记录电商网站（EC Site）的订单/预约信息，包含预约号、用户信息、访问时间、订单详情链接等字段。该模型支持历史记录、软删除，并按创建时间倒序展示。

**文件位置**: `apps/data_aggregation/models.py:697-747`

## 数据库表

- **表名**: `ec_site`
- **历史记录**: 支持（使用 `HistoricalRecordsWithSource`）
- **软删除**: 支持（`is_deleted` 字段）

## 主要字段

### 订单与用户信息字段
- **reservation_number** (CharField, 最大长度50, 唯一)
  - 预约号/订单号

- **username** (CharField, 最大长度50)
  - 下单用户

- **method** (CharField, 最大长度50)
  - 下单或预约方式（如渠道/方法标识）

- **reservation_time** (DateTimeField, 可选)
  - 预约时间

- **visit_time** (DateTimeField, 可选)
  - 访问时间

- **order_detail_url** (CharField, 最大长度255)
  - 订单详情页 URL

### 时间字段
- **order_created_at** (DateTimeField, 自动)
  - 订单创建时间

- **info_updated_at** (DateTimeField, 自动)
  - 订单信息更新时间

- **created_at** (DateTimeField, 自动)
  - 记录创建时间

- **updated_at** (DateTimeField, 自动)
  - 记录更新时间

### 标识与删除字段
- **uuid** (CharField, 最大长度59, 唯一)
  - 48字符全局唯一标识符
  - 由 `generate_uuid()` 自动生成

- **is_deleted** (BooleanField)
  - 软删除标记
  - 默认值: False

## 索引与排序

- **默认排序**: `order_created_at` 倒序
- **索引字段**:
  - `reservation_number`
  - `order_created_at`
  - `visit_time`

## 模型方法

### __str__
```python
def __str__(self):
    date_str = self.order_created_at.strftime('%Y-%m-%d') if self.order_created_at else 'N/A'
    return f"{self.reservation_number} - {self.username} ({date_str})"
```
- **返回**: `"<reservation_number> - <username> (<YYYY-MM-DD>)"`
- **用途**: 后台展示、日志输出等场景的可读字符串
