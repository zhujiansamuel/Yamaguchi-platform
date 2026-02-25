# Send Notification Email 任务说明

> 基于当前代码实现整理：`apps/data_acquisition/EmailParsing/` 相关逻辑。

## 任务入口与队列

- Celery 任务：`apps.data_acquisition.EmailParsing.tasks_send_notification_email.process_email`。
- Worker 类：`SendNotificationEmailWorker`。
- 队列：`send_notification_email_queue`。

## 触发条件（由 Email Content Analysis Worker 判定）

当邮件满足以下条件时，会被归类为 *Shipping Notification* 并触发本任务：

- 主题包含 **「お客様の商品は配送中です」**
- 发件人地址为 **`shipping_notification_jp@orders.apple.com`**
- HTML 内容存在

解析函数：`extract_fields_from_html(html_content)`，由 Email Content Analysis Worker 调用并将结果作为 `email_data` 传入任务。

## 输入字段（来自 `extract_fields_from_html`）

解析函数会输出下列主要字段（部分字段用于兼容旧逻辑）：

- 订单与查询信息
  - `order_number`
  - `official_query_url`
  - `confirmed_at`
- 商品与配送
  - `line_items`（包含 `product_name` / `quantity` / `delivery`）
  - `iphone_product_names`（兼容字段，来自第一件商品）
  - `quantity`（兼容字段）
  - `estimated_website_arrival_date`
- 收件信息
  - `name`
  - `postal_code`
  - `address_line_1`
  - `address_line_2`
  - `email`
- 物流信息
  - `tracking_number`
  - `tracking_href`
  - `carrier_name`
- 元数据（Email Content Analysis Worker 补充）
  - `email_id`
  - `email_subject`
  - `email_date`

## 核心处理流程（Worker）

1. 从 `task_data` 读取 `email_data`。
2. 校验 `order_number`，缺失则返回 `status=skip` 并停止处理。
3. 根据 `order_number` 查询 Purchasing 记录：
   - 找到记录 → 调用 `update_fields()` 更新。
   - 未找到记录 → 调用 `Purchasing.create_with_inventory()` 创建并补全字段。
4. 返回处理结果，并补充 `email_id`。

> 备注：Worker 内部提供 `acquire_record_lock` / `release_record_lock` 方法，但 `execute()` 中未调用锁逻辑。

## 更新逻辑（update_fields）

当存在对应 Purchasing 记录时，更新字段由 `_prepare_update_fields_kwargs()` 生成：

- OfficialAccount 相关字段：`email` / `name` / `postal_code` / `address_line_1` / `address_line_2`
- Purchasing 字段：
  - `official_query_url`
  - `confirmed_at`（字符串 → datetime）
  - `tracking_number`
  - `shipping_method`（由 `carrier_name` 转换）
  - `estimated_delivery_date`（由 `estimated_website_arrival_date` 转换）
  - `iphone_type_names`（最多 2 个）

商品相关处理细节：

- 若存在 `line_items`：
  - 使用 `_normalize_iphone_type_name()` 归一化产品名。
  - 支持数量扩展：按 `quantity` 展开 `iphone_type_names`。
  - 写入时限制最多 2 个型号（`iphone_type_names[:2]`）。
- 若无 `line_items`：
  - 回退使用 `iphone_product_names` 字段。

## 新建逻辑（create_with_inventory）

当未找到 Purchasing 记录时：

- 使用 `Purchasing.create_with_inventory()` 创建数据
  - `creation_source` 固定为 **`Send Notification Email`**
  - 同步写入：`order_number` / `email` / `official_query_url` / `confirmed_at`
  - 物流字段：`tracking_number` / `shipping_method` / `estimated_delivery_date`
  - 支持 `line_items` → `iphone_type_names`
  - 兼容旧字段：`iphone_product_names` / `quantity`
    - 无 `line_items` 时使用 `iphone_product_names` → `iphone_type_name`
    - `quantity` 转为 `inventory_count`
- 创建后再用 `update_fields()` 写入收件人信息：
  - `email` / `name` / `postal_code` / `address_line_1` / `address_line_2`

## 失败与重试

- Celery 任务配置：`max_retries=3`、`default_retry_delay=60` 秒。
- 若 Worker 返回 `status=error` 会触发重试；异常会继续抛出以保证 Celery 重试流程。
