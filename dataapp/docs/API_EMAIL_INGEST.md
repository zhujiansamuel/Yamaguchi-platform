# Email Batch Ingest API 邮件批量导入 API

## 概要

邮件批量导入 API 用于将 n8n Gmail 工作流提取的邮件数据批量导入到数据库。支持自动账号识别、幂等性更新、错误容错等特性。

---

## 认证

所有 API 请求需要使用 `BATCH_STATS_API_TOKEN` 进行认证。

### 认证方式

在请求头中添加 Authorization：

```http
Authorization: Bearer <BATCH_STATS_API_TOKEN>
```

### 配置 Token

在 `.env` 文件或环境变量中配置：

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

### 基础信息

```
POST /api/data-aggregation/emails/ingest/
Content-Type: application/json
```

### 功能特性

- ✅ **批量导入**: 一次请求可导入多封邮件
- ✅ **自动账号识别**: 从邮件的 `to` 字段自动识别并创建/关联邮箱账号
- ✅ **幂等性**: 相同 `id` (provider_message_id) 的邮件会更新而非重复创建
- ✅ **错误容错**: 单封邮件导入失败不影响其他邮件的处理
- ✅ **完整日志**: 每封邮件的处理结果都会返回详细信息
- ✅ **自动标签管理**: 自动创建和关联 Gmail 标签

---

## 请求格式

### 请求体结构

```json
{
  "emails": [
    {
      "id": "string (required)",
      "threadId": "string (optional)",
      "labelIds": ["string"] (optional),
      "sizeEstimate": integer (optional),
      "headers": {} (optional),
      "html": "string (optional)",
      "text": "string (optional)",
      "textAsHtml": "string (optional)",
      "subject": "string (optional)",
      "date": "ISO 8601 datetime (optional)",
      "messageId": "string (optional)",
      "from": {
        "value": [
          {
            "address": "email (required)",
            "name": "string (optional)"
          }
        ]
      },
      "to": {
        "value": [
          {
            "address": "email (required)",
            "name": "string (optional)"
          }
        ]
      }
    }
  ]
}
```

### 字段说明

| 字段路径 | 类型 | 必填 | 说明 | 示例 |
|---------|------|------|------|------|
| `emails` | Array | ✓ | 邮件数组 | `[...]` |
| `emails[].id` | String | ✓ | Gmail 消息 ID | `19bc4da23fe37661` |
| `emails[].threadId` | String | ✗ | Gmail 线程 ID | `19bc4da23fe37661` |
| `emails[].labelIds` | Array | ✗ | 标签 ID 列表 | `["INBOX", "UNREAD"]` |
| `emails[].sizeEstimate` | Integer | ✗ | 邮件大小估计（字节） | `85858` |
| `emails[].headers` | Object | ✗ | 原始邮件头 | `{"from": "...", ...}` |
| `emails[].html` | String | ✗ | HTML 正文 | `<!DOCTYPE HTML>...` |
| `emails[].text` | String | ✗ | 纯文本正文 | `Apple Store\n\n...` |
| `emails[].textAsHtml` | String | ✗ | 纯文本转 HTML | `<p>Apple Store</p>` |
| `emails[].subject` | String | ✗ | 邮件主题 | `お客様の商品は配送中です` |
| `emails[].date` | DateTime | ✗ | 邮件日期 | `2026-01-16T03:29:44.000Z` |
| `emails[].messageId` | String | ✗ | RFC 822 Message-ID | `<CB.C2.61222@...>` |
| `emails[].from.value[].address` | Email | ✓ | 发件人邮箱 | `shipping@orders.apple.com` |
| `emails[].from.value[].name` | String | ✗ | 发件人姓名 | `Apple Store` |
| `emails[].to.value[].address` | Email | ✓ | 收件人邮箱 | `user@example.com` |
| `emails[].to.value[].name` | String | ✗ | 收件人姓名 | `User Name` |

---

## 响应格式

### 成功响应 (200 OK)

```json
{
  "status": "success",
  "message": "Processed 2 emails: 2 successful, 0 failed",
  "total": 2,
  "successful": 2,
  "failed": 0,
  "results": [
    {
      "email_id": "19bc4da23fe37661",
      "status": "success",
      "message_db_id": 123
    },
    {
      "email_id": "19bc4da22a835035",
      "status": "success",
      "message_db_id": 124
    }
  ]
}
```

### 部分成功响应 (200 OK)

```json
{
  "status": "partial",
  "message": "Processed 3 emails: 2 successful, 1 failed",
  "total": 3,
  "successful": 2,
  "failed": 1,
  "results": [
    {
      "email_id": "19bc4da23fe37661",
      "status": "success",
      "message_db_id": 123
    },
    {
      "email_id": "invalid-email-id",
      "status": "error",
      "error": "Missing or invalid 'to' field"
    },
    {
      "email_id": "19bc4da22a835035",
      "status": "success",
      "message_db_id": 124
    }
  ]
}
```

### 请求验证失败 (400 Bad Request)

```json
{
  "status": "error",
  "message": "Invalid request data",
  "total": 0,
  "successful": 0,
  "failed": 0,
  "results": [],
  "errors": {
    "emails": [
      "This field is required."
    ]
  }
}
```

### 响应字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `status` | String | 整体状态：`success`（全部成功）、`partial`（部分成功）、`error`（全部失败） |
| `message` | String | 处理结果描述 |
| `total` | Integer | 总邮件数 |
| `successful` | Integer | 成功导入的邮件数 |
| `failed` | Integer | 导入失败的邮件数 |
| `results` | Array | 每封邮件的详细结果 |
| `results[].email_id` | String | 邮件 ID |
| `results[].status` | String | 单封邮件状态：`success` 或 `error` |
| `results[].message_db_id` | Integer | 数据库中的邮件 ID（仅成功时） |
| `results[].error` | String | 错误信息（仅失败时） |

---

## 完整请求示例

### cURL 示例

```bash
curl -X POST "http://localhost:8000/api/data-aggregation/emails/ingest/" \
  -H "Authorization: Bearer your-token-here" \
  -H "Content-Type: application/json" \
  -d '{
    "emails": [
      {
        "id": "19bc4da23fe37661",
        "threadId": "19bc4da23fe37661",
        "labelIds": ["UNREAD", "Label_1", "INBOX"],
        "sizeEstimate": 85858,
        "headers": {
          "delivered-to": "Delivered-To: khl602@yamaguchishoji.com",
          "from": "From: Apple Store <shipping_notification_jp@orders.apple.com>",
          "subject": "Subject: お客様の商品は配送中です"
        },
        "html": "<!DOCTYPE HTML>...",
        "text": "Apple Store\n\nご注文番号: W1667146438...",
        "textAsHtml": "<p>Apple Store</p>...",
        "subject": "お客様の商品は配送中です。ご注文番号: W1667146438",
        "date": "2026-01-16T03:29:44.000Z",
        "messageId": "<CB.C2.61222.8A0B9696@mr29p01nt-txnmsbadger004.ise.apple.com>",
        "from": {
          "value": [
            {
              "address": "shipping_notification_jp@orders.apple.com",
              "name": "Apple Store"
            }
          ],
          "text": "\"Apple Store\" <shipping_notification_jp@orders.apple.com>",
          "html": "<span>Apple Store</span> &lt;shipping_notification_jp@orders.apple.com&gt;"
        },
        "to": {
          "value": [
            {
              "address": "khl602@yamaguchishoji.com",
              "name": ""
            }
          ],
          "text": "khl602@yamaguchishoji.com",
          "html": "<a href=\"mailto:khl602@yamaguchishoji.com\">khl602@yamaguchishoji.com</a>"
        }
      }
    ]
  }'
```

---

## Python 代码示例

### 示例 1: 从 JSON 文件批量导入邮件

```python
import json
import requests
from typing import List, Dict

# 配置
API_URL = "http://localhost:8000/api/data-aggregation/emails/ingest/"
API_TOKEN = "your-batch-stats-api-token-here"

def load_emails_from_json(filepath: str) -> List[Dict]:
    """
    从 JSON 文件加载邮件数据

    Args:
        filepath: JSON 文件路径

    Returns:
        邮件数组
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 如果文件是邮件数组
    if isinstance(data, list):
        return data

    # 如果文件是单个邮件对象
    if isinstance(data, dict):
        return [data]

    raise ValueError("Invalid JSON format: expected list or dict")


def batch_ingest_emails(emails: List[Dict]) -> Dict:
    """
    批量导入邮件到数据库

    Args:
        emails: 邮件数据列表

    Returns:
        API 响应结果
    """
    headers = {
        "Authorization": f"Bearer {API_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {
        "emails": emails
    }

    response = requests.post(API_URL, json=payload, headers=headers)
    response.raise_for_status()

    return response.json()


def main():
    """主函数：从文件导入邮件"""
    # 1. 从 JSON 文件加载邮件
    emails = load_emails_from_json("emails_export.json")
    print(f"从文件加载了 {len(emails)} 封邮件")

    # 2. 批量导入到数据库
    result = batch_ingest_emails(emails)

    # 3. 打印结果
    print(f"\n导入结果:")
    print(f"  状态: {result['status']}")
    print(f"  总计: {result['total']} 封")
    print(f"  成功: {result['successful']} 封")
    print(f"  失败: {result['failed']} 封")

    # 4. 打印详细结果
    if result.get('results'):
        print(f"\n详细结果:")
        for item in result['results']:
            if item['status'] == 'success':
                print(f"  ✓ {item['email_id']} -> DB ID: {item['message_db_id']}")
            else:
                print(f"  ✗ {item['email_id']} -> Error: {item.get('error', 'Unknown')}")


if __name__ == "__main__":
    main()
```

**使用方法**:
```bash
# 准备邮件数据文件 emails_export.json
# 运行脚本
python import_emails.py
```

---

### 示例 2: 分批处理大量邮件

```python
import json
import requests
import time
from typing import List, Dict, Iterator

API_URL = "http://localhost:8000/api/data-aggregation/emails/ingest/"
API_TOKEN = "your-batch-stats-api-token-here"
BATCH_SIZE = 50  # 每批处理 50 封邮件


def chunk_list(data: List, chunk_size: int) -> Iterator[List]:
    """将列表分批"""
    for i in range(0, len(data), chunk_size):
        yield data[i:i + chunk_size]


def ingest_email_batch(emails: List[Dict]) -> Dict:
    """导入一批邮件"""
    headers = {
        "Authorization": f"Bearer {API_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {"emails": emails}

    response = requests.post(API_URL, json=payload, headers=headers)
    response.raise_for_status()

    return response.json()


def import_emails_in_batches(filepath: str, batch_size: int = BATCH_SIZE):
    """分批导入邮件"""
    # 1. 加载所有邮件
    with open(filepath, 'r', encoding='utf-8') as f:
        all_emails = json.load(f)

    if isinstance(all_emails, dict):
        all_emails = [all_emails]

    total_emails = len(all_emails)
    print(f"总计 {total_emails} 封邮件，将分 {(total_emails + batch_size - 1) // batch_size} 批处理")

    # 2. 分批处理
    total_successful = 0
    total_failed = 0
    batch_num = 0

    for batch in chunk_list(all_emails, batch_size):
        batch_num += 1
        print(f"\n处理第 {batch_num} 批 ({len(batch)} 封邮件)...")

        try:
            result = ingest_email_batch(batch)

            total_successful += result['successful']
            total_failed += result['failed']

            print(f"  成功: {result['successful']}, 失败: {result['failed']}")

            # 显示错误详情
            for item in result.get('results', []):
                if item['status'] == 'error':
                    print(f"    ✗ {item['email_id']}: {item.get('error', 'Unknown error')}")

        except requests.exceptions.RequestException as e:
            print(f"  批次处理失败: {e}")
            total_failed += len(batch)

        # 短暂延迟，避免过载
        if batch_num < (total_emails + batch_size - 1) // batch_size:
            time.sleep(0.5)

    # 3. 总结
    print(f"\n" + "="*50)
    print(f"导入完成!")
    print(f"  总计: {total_emails} 封")
    print(f"  成功: {total_successful} 封")
    print(f"  失败: {total_failed} 封")
    print(f"  成功率: {total_successful / total_emails * 100:.1f}%")


if __name__ == "__main__":
    import_emails_in_batches("large_email_export.json", batch_size=50)
```

---

### 示例 3: 从多个文件导入邮件

```python
import json
import requests
import os
from pathlib import Path
from typing import List, Dict

API_URL = "http://localhost:8000/api/data-aggregation/emails/ingest/"
API_TOKEN = "your-batch-stats-api-token-here"


def import_from_directory(directory: str, pattern: str = "*.json"):
    """
    从目录中的所有 JSON 文件导入邮件

    Args:
        directory: 目录路径
        pattern: 文件匹配模式
    """
    directory_path = Path(directory)
    json_files = list(directory_path.glob(pattern))

    print(f"在目录 {directory} 中找到 {len(json_files)} 个文件")

    total_emails = 0
    total_successful = 0
    total_failed = 0

    for json_file in json_files:
        print(f"\n处理文件: {json_file.name}")

        try:
            # 读取文件
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # 转换为邮件列表
            emails = data if isinstance(data, list) else [data]
            total_emails += len(emails)

            # 导入邮件
            headers = {
                "Authorization": f"Bearer {API_TOKEN}",
                "Content-Type": "application/json"
            }

            response = requests.post(
                API_URL,
                json={"emails": emails},
                headers=headers
            )
            response.raise_for_status()

            result = response.json()
            total_successful += result['successful']
            total_failed += result['failed']

            print(f"  成功: {result['successful']}, 失败: {result['failed']}")

        except Exception as e:
            print(f"  处理文件失败: {e}")
            total_failed += len(emails) if 'emails' in locals() else 0

    # 总结
    print(f"\n" + "="*60)
    print(f"所有文件处理完成!")
    print(f"  文件数: {len(json_files)}")
    print(f"  总邮件数: {total_emails}")
    print(f"  成功导入: {total_successful}")
    print(f"  导入失败: {total_failed}")


if __name__ == "__main__":
    # 导入 emails 目录下的所有 JSON 文件
    import_from_directory("./emails", pattern="*.json")
```

---

### 示例 4: 带重试机制的导入

```python
import json
import requests
import time
from typing import List, Dict, Optional

API_URL = "http://localhost:8000/api/data-aggregation/emails/ingest/"
API_TOKEN = "your-batch-stats-api-token-here"


def ingest_with_retry(
    emails: List[Dict],
    max_retries: int = 3,
    retry_delay: float = 2.0
) -> Optional[Dict]:
    """
    带重试机制的邮件导入

    Args:
        emails: 邮件列表
        max_retries: 最大重试次数
        retry_delay: 重试延迟（秒）

    Returns:
        API 响应结果，或 None（如果全部失败）
    """
    headers = {
        "Authorization": f"Bearer {API_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {"emails": emails}

    for attempt in range(max_retries):
        try:
            response = requests.post(
                API_URL,
                json=payload,
                headers=headers,
                timeout=30
            )
            response.raise_for_status()
            return response.json()

        except requests.exceptions.Timeout:
            print(f"  请求超时 (尝试 {attempt + 1}/{max_retries})")

        except requests.exceptions.ConnectionError:
            print(f"  连接错误 (尝试 {attempt + 1}/{max_retries})")

        except requests.exceptions.RequestException as e:
            print(f"  请求失败: {e} (尝试 {attempt + 1}/{max_retries})")

        # 等待后重试
        if attempt < max_retries - 1:
            time.sleep(retry_delay * (attempt + 1))  # 指数退避

    print(f"  重试 {max_retries} 次后仍然失败")
    return None


def main():
    """主函数"""
    # 加载邮件
    with open("emails.json", 'r', encoding='utf-8') as f:
        emails = json.load(f)

    if isinstance(emails, dict):
        emails = [emails]

    print(f"准备导入 {len(emails)} 封邮件")

    # 带重试的导入
    result = ingest_with_retry(emails, max_retries=3)

    if result:
        print(f"\n导入成功!")
        print(f"  成功: {result['successful']}")
        print(f"  失败: {result['failed']}")
    else:
        print(f"\n导入失败: 所有重试都失败了")


if __name__ == "__main__":
    main()
```

---

## 常见错误及解决方案

### 1. 认证失败

**错误信息**:
```json
{
  "detail": "Invalid token"
}
```

**解决方案**:
- 检查环境变量 `BATCH_STATS_API_TOKEN` 是否正确配置
- 确认请求头中的 Token 格式正确：`Bearer <token>`

---

### 2. 缺少必填字段

**错误信息**:
```json
{
  "status": "error",
  "errors": {
    "emails": ["This field is required."]
  }
}
```

**解决方案**:
- 确保请求体包含 `emails` 数组
- 确保每封邮件包含 `id` 和 `to` 字段

---

### 3. 邮件格式错误

**错误信息**:
```json
{
  "email_id": "xxx",
  "status": "error",
  "error": "Missing or invalid 'to' field"
}
```

**解决方案**:
- 检查 `to.value` 是否为数组且包含至少一个邮箱地址
- 确认邮箱地址格式正确

---

### 4. 数据库连接失败

**错误信息**:
```json
{
  "status": "error",
  "message": "Database connection error"
}
```

**解决方案**:
- 检查数据库服务是否运行
- 确认数据库迁移已执行：`python manage.py migrate`

---

## 性能建议

1. **批量大小**: 建议每批 20-100 封邮件
2. **并发请求**: 避免同时发送多个请求，建议串行处理
3. **重试策略**: 使用指数退避策略处理临时错误
4. **超时设置**: 建议设置 30-60 秒的请求超时时间

---

## 相关文档

- [邮件数据模型文档](MODEL_EMAIL.md)
- [API 概览](API_OVERVIEW.md)
- [认证说明](API_OVERVIEW.md#认证)
