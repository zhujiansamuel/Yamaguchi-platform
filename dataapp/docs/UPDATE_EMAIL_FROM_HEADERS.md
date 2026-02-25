# 更新邮件发件人信息 - Management Command

## 概述

`update_email_from_headers` 是一个 Django management command，用于批量更新数据库中所有 `MailMessage` 实例的 `from_address` 和 `from_name` 字段。

此命令从 `raw_headers['from']` 中重新提取发件人信息，确保使用最准确的原始邮件头数据。

---

## 使用方法

### Docker 环境

如果使用 Docker 部署，通过以下命令运行：

```bash
# 预览模式（不实际更新数据库）
docker-compose exec django python manage.py update_email_from_headers --dry-run

# 实际更新所有邮件
docker-compose exec django python manage.py update_email_from_headers

# 批量更新，每批 500 条
docker-compose exec django python manage.py update_email_from_headers --batch-size 500

# 测试前 10 条记录
docker-compose exec django python manage.py update_email_from_headers --dry-run --limit 10 -v 2
```

### 本地环境

如果在本地虚拟环境中运行：

```bash
# 激活虚拟环境
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows

# 预览模式
python manage.py update_email_from_headers --dry-run

# 实际更新
python manage.py update_email_from_headers
```

---

## 命令参数

### `--dry-run`

**说明**: 预览模式，显示将要进行的更改但不实际保存到数据库

**用法**: `--dry-run`

**示例**:
```bash
docker-compose exec django python manage.py update_email_from_headers --dry-run
```

**建议**: 在首次运行实际更新前，先使用此选项预览更改

---

### `--batch-size N`

**说明**: 每批处理的记录数（默认: 100）

**用法**: `--batch-size N`

**示例**:
```bash
# 每批处理 500 条记录
docker-compose exec django python manage.py update_email_from_headers --batch-size 500
```

**建议**:
- 小数据量: 使用默认值 100
- 大数据量 (>10000): 使用 500-1000
- 超大数据量 (>100000): 使用 1000-2000

---

### `--limit N`

**说明**: 限制处理的邮件总数（用于测试）

**用法**: `--limit N`

**示例**:
```bash
# 仅处理前 10 条记录
docker-compose exec django python manage.py update_email_from_headers --limit 10
```

**用途**: 在全量更新前测试命令是否正常工作

---

### `-v, --verbosity {0,1,2,3}`

**说明**: 控制输出详细程度

**用法**: `-v N` 或 `--verbosity N`

**级别**:
- `0`: 仅显示错误
- `1`: 显示基本信息（默认）
- `2`: 显示详细信息（每条记录的更新详情）
- `3`: 显示调试信息

**示例**:
```bash
# 显示详细的更新信息
docker-compose exec django python manage.py update_email_from_headers -v 2

# 静默模式
docker-compose exec django python manage.py update_email_from_headers -v 0
```

---

## 工作原理

### 提取逻辑

1. **从 raw_headers 提取**：
   - 读取 `raw_headers['from']` 字段
   - 示例: `"From: Apple Store <order_acknowledgment@orders.apple.com>"`

2. **解析邮件头**：
   - 移除 `"From: "` 前缀
   - 使用 Python `email.utils.parseaddr()` 解析
   - 提取 email 地址: `order_acknowledgment@orders.apple.com`
   - 提取发件人姓名: `Apple Store`

3. **更新字段**：
   - `from_address`: 邮箱地址
   - `from_name`: 发件人姓名
   - `sender_domain`: 发件人域名（自动从 email 地址提取）

### 处理规则

- ✅ **跳过**: 如果 `raw_headers['from']` 为空，跳过该记录
- ✅ **不变**: 如果新值与现有值相同，标记为"未更改"
- ✅ **回退**: 如果解析失败，保持现有值不变
- ✅ **错误处理**: 单条记录错误不影响其他记录处理

---

## 输出说明

### 示例输出

```
DRY RUN MODE - No changes will be saved

Total MailMessage records: 1523
Processing: 1523 messages
Batch size: 100

Processing batch 1 (100 messages)...
  [DRY RUN] Would update message 45:
    Address: "shipping@orders.apple.com" → "shipping_notification_jp@orders.apple.com"
    Name: "" → "Apple Store"
  [DRY RUN] Would update message 46:
    Address: "no-reply@amazon.com" → "auto-confirm@amazon.co.jp"
    Name: "Amazon" → "Amazon.co.jp"
Progress: 100/1523 messages processed

...

================================================================================
Update Complete!
================================================================================
Total processed:  1523
Updated:          856
Unchanged:        542
Skipped:          125 (no valid from in raw_headers)
Errors:           0
================================================================================

This was a DRY RUN - no changes were saved to the database.
Run without --dry-run to apply these changes.
```

### 统计字段说明

| 字段 | 说明 |
|------|------|
| **Total processed** | 处理的邮件总数 |
| **Updated** | 成功更新的邮件数 |
| **Unchanged** | 新值与旧值相同，未更新的邮件数 |
| **Skipped** | raw_headers 中没有有效 from 字段，跳过的邮件数 |
| **Errors** | 处理过程中发生错误的邮件数 |

---

## 使用场景

### 场景 1: 首次部署后更新历史数据

在部署新的提取逻辑后，更新所有历史邮件：

```bash
# 1. 预览更改
docker-compose exec django python manage.py update_email_from_headers --dry-run

# 2. 确认无误后执行
docker-compose exec django python manage.py update_email_from_headers
```

### 场景 2: 测试更新逻辑

在小范围测试更新逻辑：

```bash
# 测试前 10 条，显示详细信息
docker-compose exec django python manage.py update_email_from_headers --dry-run --limit 10 -v 2
```

### 场景 3: 大批量数据更新

处理超过 10 万条邮件：

```bash
# 使用较大的批次大小
docker-compose exec django python manage.py update_email_from_headers --batch-size 1000
```

---

## 注意事项

### ⚠️ 数据备份

在执行实际更新前，建议备份数据库：

```bash
# Docker 环境备份
docker-compose exec postgres pg_dump -U postgres data_platform > backup_$(date +%Y%m%d_%H%M%S).sql
```

### ⚠️ 性能影响

- 大批量更新可能需要较长时间
- 建议在低峰期执行
- 使用 `--batch-size` 控制内存使用

### ⚠️ 幂等性

- 此命令可以安全地多次运行
- 重复运行会跳过已更新且值未变的记录

---

## 故障排除

### 问题: 大量记录被跳过

**原因**: `raw_headers['from']` 为空或格式不正确

**解决方案**:
1. 检查邮件导入时是否正确保存了 `raw_headers`
2. 确认 n8n 工作流正确提取了邮件头信息

### 问题: 更新速度慢

**原因**: 批次大小太小或数据量太大

**解决方案**:
```bash
# 增加批次大小
docker-compose exec django python manage.py update_email_from_headers --batch-size 1000
```

### 问题: 内存不足

**原因**: 批次大小太大

**解决方案**:
```bash
# 减小批次大小
docker-compose exec django python manage.py update_email_from_headers --batch-size 50
```

---

## 相关文档

- [邮件批量导入 API](API_EMAIL_INGEST.md)
- [邮件数据模型](MODEL_EMAIL.md)

---

## 技术细节

### 使用的 Python 标准库

```python
from email.utils import parseaddr
```

`parseaddr()` 函数能够正确解析 RFC 822 标准的邮件地址格式：
- `"Name" <email@example.com>`
- `Name <email@example.com>`
- `<email@example.com>`
- `email@example.com`

### 数据库更新

使用 Django ORM 的 `save(update_fields=[...])` 方法：
- 仅更新指定字段
- 避免触发其他字段的更新逻辑
- 保持其他字段的时间戳不变

---

## 版本历史

- **v1.0** (2026-01-17): 初始版本
  - 支持从 raw_headers 提取 from_address 和 from_name
  - 支持 dry-run 模式
  - 支持批量处理
  - 完整的错误处理和统计信息
