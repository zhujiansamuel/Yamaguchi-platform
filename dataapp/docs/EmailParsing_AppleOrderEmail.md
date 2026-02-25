# Email Content Analysis Worker - Apple订单邮件解析

## 概述

Email Content Analysis Worker 已实现对 Apple 订单确认邮件与配送通知邮件的自动解析功能。该 worker 会从数据库中批量获取未处理的邮件，解析 HTML 内容并提取关键订单信息，随后触发对应的任务处理流程。

## 功能说明

### 邮件筛选条件

Worker 从 `MailMessage` 表中筛选符合以下条件的邮件：

1. `MailMessage.body` 关联存在（`body__isnull=False`）
2. `is_extracted` 不为 True（避免重复处理已提取的邮件）
3. 按 `date_header_at` 从旧到新排序，最多取 10 封邮件

> 备注：当前只检查 `body` 关联是否存在，不校验 `text_html` 是否为空；`html_content` 为空时会在处理阶段被跳过。

### 处理流程

1. **获取邮件**：从数据库中获取最多 10 封未处理邮件
2. **预先标记**：批量将这些邮件的 `is_extracted` 字段设置为 True，避免重复处理
3. **类型判定**：根据邮件主题与发件人区分订单确认/配送通知
4. **解析 HTML**：
   - 订单确认 → `parse_apple_order_email(html_content)`
   - 配送通知 → `extract_fields_from_html(html_content)`
5. **触发任务**：将提取的数据传递给对应的任务（订单确认或配送通知）

### 邮件类型判定规则

- **订单确认邮件**:
  - Subject 包含 `ご注文ありがとうございます`
  - From address 为 `order_acknowledgment@orders.apple.com`
- **配送通知邮件**:
  - Subject 包含 `お客様の商品は配送中です`
  - From address 为 `shipping_notification_jp@orders.apple.com`

### 提取的数据字段

从邮件 HTML 内容中提取以下字段（按邮件类型区分）：

**订单确认邮件（ご注文ありがとうございます）**

| 字段名 | 说明 | 数据类型 |
|--------|------|----------|
| `official_query_url` | 订单查询 URL | String |
| `order_number` | 订单号 | String |
| `confirmed_at` | 订单确认日期 | String (YYYY/MM/DD) |
| `estimated_website_arrival_date` | 预计到达日期（开始） | String (YYYY/MM/DD) |
| `estimated_website_arrival_date_2` | 预计到达日期（结束，可选） | String (YYYY/MM/DD) |
| `line_items` | 商品列表（含交付日期） | List |
| `iphone_product_names` | 产品名称（向后兼容第一个商品） | String |
| `quantities` | 数量（向后兼容第一个商品） | Integer |
| `email` | 邮箱地址 | String |
| `name` | 收件人姓名 | String |
| `postal_code` | 邮编 | String |
| `address_line_1` | 地址行 1（都道府县） | String |
| `address_line_2` | 地址行 2（详细地址） | String |

**配送通知邮件（お客様の商品は配送中です）**

| 字段名 | 说明 | 数据类型 |
|--------|------|----------|
| `official_query_url` | 订单查询 URL | String |
| `order_number` | 订单号 | String |
| `confirmed_at` | 订单日期 | String (YYYY/MM/DD) |
| `estimated_website_arrival_date` | 预计到达日期 | String (YYYY/MM/DD) |
| `line_items` | 商品列表（含交付日期） | List |
| `iphone_product_names` | 产品名称（向后兼容第一个商品） | String |
| `quantity` | 数量（向后兼容第一个商品） | Integer |
| `email` | 邮箱地址 | String |
| `name` | 收件人姓名 | String |
| `postal_code` | 邮编 | String |
| `address_line_1` | 地址行 1（都道府县） | String |
| `address_line_2` | 地址行 2（详细地址） | String |
| `tracking_number` | 运单号 | String |
| `tracking_href` | 运单查询链接 | String |
| `carrier_name` | 配送业者名 | String |

**line_items 结构说明**

每个 `line_items` 元素包含：
- `product_name`: 商品名称
- `quantity`: 数量
- `delivery`: 配送日期信息（`type` 为 `single` 或 `range`，并包含 `date`/`start_date`/`end_date` 字段）

### 额外的元数据字段

解析结果中还会包含以下元数据：

- `email_id`: 邮件在数据库中的 ID
- `email_subject`: 邮件主题
- `email_date`: 邮件日期

## 实现细节

### 核心函数

#### 1. `extract_delivery_dates(tree)`

提取配送日期信息，支持两种格式：
- **日期区间**: `2024/01/20 - 2024/01/25`
- **单个日期**: `2024/01/20`

返回格式：
```python
# 日期区间
{
    "type": "range",
    "start_date": "2024/01/20",
    "end_date": "2024/01/25",
    "full_text": "2024/01/20 - 2024/01/25"
}

# 单个日期
{
    "type": "single",
    "date": "2024/01/20",
    "full_text": "2024/01/20"
}
```

#### 2. `parse_apple_order_email(html_content)`

解析 Apple 订单确认邮件的完整 HTML 内容，提取所有订单信息。

要点：
- 订单号与查询 URL 从 `aapl-link` 且包含 `vieworder` 的链接提取。
- `confirmed_at` 从 `div.order-num` 内带 `/` 的文本提取。
- 商品列表通过 `extract_line_items_from_order_email` 解析，兼容「お届け予定日 N」分组模板与非分组模板。
- 若地址行不足 4 行，则姓名与地址字段均返回 `None`。
- 邮箱从包含 `@` 的文本节点中提取首个匹配值。

#### 3. `extract_fields_from_html(html_text)`

解析配送通知邮件的 HTML 内容，提取订单、配送以及运单信息。

要点：
- `order_number`/`official_query_url`/`confirmed_at` 基于 `ご注文番号:`/`ご注文日:` 的 XPath 提取。
- `estimated_website_arrival_date` 从 `お届け予定日` 文本中解析单日日期。
- 商品列表基于 `product-name-td` 与 `数量` 文本提取，数量不足时填充 `None` 或扩展为多商品共享。
- 配送地址从「配送先住所」后续 `div` 行解析（邮编/都道府县+市区/详细地址/收件人）。
- 物流信息从「配達伝票番号」「配送業者名」区块提取。

#### 4. `EmailContentAnalysisWorker`

Worker 类的主要方法：

- `fetch_emails_from_database()`: 从数据库查询符合条件的邮件（最多 10 封）
- `analyze_email_content()`: 使用 `parse_apple_order_email` 解析邮件并补充元数据（当前未在 `execute()` 中使用）
- `execute()`: 执行完整的邮件处理流程

## 使用方法

### 1. 通过 Celery 任务调用

```python
from apps.data_acquisition.EmailParsing.tasks_email_content_analysis import process_email

# 处理单个邮件
result = process_email.delay()
print(f"Task ID: {result.id}")

# 批量处理
from apps.data_acquisition.EmailParsing.tasks_email_content_analysis import process_batch
result = process_batch.delay(count=10)
```

### 2. 直接调用 Worker

```python
from apps.data_acquisition.EmailParsing.email_content_analysis import EmailContentAnalysisWorker

worker = EmailContentAnalysisWorker()
result = worker.run({})

if result['status'] == 'success':
    extracted_data = result['result']['processed_emails']
    print(f"Processed Count: {result['result']['processed_count']}")
```

### 3. 测试命令

#### 测试 HTML 解析功能

使用 Django management command 测试 HTML 解析函数：

```bash
# 在 Docker 容器内执行
python manage.py test_email_parsing
```

测试命令会：
1. 使用示例 HTML 测试解析函数
2. 从数据库中获取真实邮件并测试完整流程
3. 显示提取的所有字段

#### 运行完整的邮件处理流程

使用此命令处理一封真实的邮件：

```bash
# 在 Docker 容器内执行
python manage.py run_email_content_analysis
```

此命令会：
1. 从数据库获取最多 10 封未处理邮件
2. 解析并提取订单或配送信息
3. 触发 `initial_order_confirmation_email` 或 `send_notification_email` 任务
4. 将邮件标记为已处理（`is_extracted=True`）
5. 显示提取的数据和任务 ID

## 任务集成

### 与 Initial Order Confirmation Email / Send Notification Email Worker 的集成

Email Content Analysis Worker 处理完邮件后，会自动触发 `initial_order_confirmation_email` 或 `send_notification_email` 任务：

```python
from apps.data_acquisition.EmailParsing.tasks_initial_order_confirmation_email import process_email
from apps.data_acquisition.EmailParsing.tasks_send_notification_email import process_email

# 根据邮件类型触发不同任务，传递提取的数据
task_result = process_email.delay(email_data=extracted_data)
logger.info(f"Task triggered, task_id={task_result.id}")
```

## 输出示例

### 成功处理

```python
{
    'status': 'success',
    'processed_count': 1,
    'skipped_count': 0,
    'processed_emails': [
        {
            'email_id': 123,
            'type': 'initial_order_confirmation',
            'task_id': 'abc123-def456-ghi789',
            'order_number': 'W1234567890'
        }
    ],
    'message': 'Processed 1 emails, skipped 0'
}
```

### 无匹配邮件

```python
{
    'status': 'no_email',
    'message': 'No unprocessed emails found',
    'processed_count': 0
}
```

### 解析失败 / 未匹配

```python
{
    'status': 'success',
    'processed_count': 0,
    'skipped_count': 1,
    'processed_emails': [],
    'message': 'Processed 0 emails, skipped 1'
}
```

## 技术栈

- **HTML 解析**: lxml
- **正则表达式**: re (用于日期提取)
- **数据库**: Django ORM
- **队列**: Celery

## 注意事项

1. **HTML 结构依赖**: 解析逻辑依赖于 Apple 邮件的特定 HTML 结构（CSS 类名、XPath 路径等）。如果 Apple 更改邮件模板，可能需要更新 XPath 选择器。

2. **字符编码**: 确保 HTML 内容使用 UTF-8 编码，以正确处理日文字符。

3. **空值处理**: 所有提取的字段都可能为 `None`，使用时需要进行空值检查。

4. **日期格式**: 提取的日期为字符串格式（YYYY/MM/DD），需要根据实际需求转换为日期对象。

5. **数量与商品列表**: `line_items` 提供多商品列表；`iphone_product_names`/`quantities`/`quantity` 为向后兼容字段。

## 后续扩展

可以考虑的后续功能：

1. **多产品支持**: 已支持 `line_items` 多商品解析，可继续优化模板识别
2. **数据持久化**: 将提取的数据自动保存到 `Purchasing` 和 `Inventory` 模型
3. **邮件处理标记**: 添加标签或状态字段标记已处理的邮件，避免重复处理
4. **错误通知**: 解析失败时发送通知或创建错误日志
5. **模板版本检测**: 自动检测 Apple 邮件模板版本并使用相应的解析逻辑

## 文件清单

- `apps/data_acquisition/EmailParsing/email_content_analysis.py`: Worker 实现
- `apps/data_acquisition/EmailParsing/tasks_email_content_analysis.py`: Celery 任务定义
- `apps/data_acquisition/management/commands/test_email_parsing.py`: 测试命令
- `docs/EmailParsing_AppleOrderEmail.md`: 本文档

## 维护历史

### 2026-01-17 (v1.3)
- 更新文档描述以对齐当前邮件筛选、解析与任务触发逻辑
- 补充商品列表解析与回退字段说明

### 2026-01-17 (v1.2)
- 支持订单确认与配送通知两类邮件
- 增加 `line_items` 多商品解析与兼容字段输出
- 增加运单号、承运商等配送信息解析
- 批量标记已提取邮件（is_extracted=True）

### 2026-01-17 (v1.1)
- 添加 `is_extracted` 过滤条件，避免重复处理
- 实现任务触发机制，自动调用 `initial_order_confirmation_email` 任务
- 成功处理后自动标记邮件为已提取（is_extracted=True）
- 添加 `run_email_content_analysis` 测试命令

### 2026-01-17 (v1.0)
- 实现 Apple 订单确认邮件解析功能
- 添加 HTML 解析辅助函数
- 实现数据库邮件查询
- 创建测试命令

---

**最后更新**: 2026-01-17
**维护者**: Data Acquisition Team
**版本**: v1.3
