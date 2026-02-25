# Email 邮件数据模型文档

## 概要

邮件数据聚合系统用于存储和管理来自 Gmail 等邮件提供商的邮件数据。支持邮件内容、标签、附件等完整信息的存储和查询。

## 数据模型关系图

```
OfficialAccount (官方账号) ←─── 1:1 ──→ MailAccount (邮箱账号)
                                              │
                                              ├──> MailThread (邮件会话线程)
                                              │       │
                                              │       └──> MailMessage (邮件消息) ──┐
                                              │                   │                  │
                                              │                   │                  │
                                              ├──> MailLabel (标签) <──────────────┤
                                              │                                      │
                                              └──> MailMessage (邮件消息) ──────────┘
                                                      │
                                                      ├──> MailMessageBody (邮件正文，1对1)
                                                      ├──> MailMessageLabel (邮件-标签关联，多对多)
                                                      └──> MailAttachment (附件，1对多)
```

---

## 模型详细说明

### 1. MailAccount (邮箱账号)

**表名**: `data_aggregation_mailaccount`

存储邮箱账号信息，每个邮箱地址对应一个账号记录。

| 字段 | 类型 | 必填 | 唯一 | 说明 | 示例 |
|------|------|------|------|------|------|
| `id` | BigInteger | 自动 | ✓ | 主键ID | `1` |
| `provider` | String(32) | ✓ | ✗ | 邮件提供商 | `gmail`, `imap` |
| `email_address` | Email(254) | ✓ | ✓ | 邮箱地址 | `user@example.com` |
| `official_account` | OneToOne | ✗ | ✗ | 关联的官方账号 | `OfficialAccount(1)` |
| `last_history_id` | String(64) | ✗ | ✗ | Gmail 历史ID（增量同步用） | `123456` |
| `created_at` | DateTime | 自动 | ✗ | 创建时间 | `2026-01-16T12:00:00Z` |
| `updated_at` | DateTime | 自动 | ✗ | 更新时间 | `2026-01-16T12:00:00Z` |

**关系**:
- 一对一: `official_account` → OfficialAccount (可选，用于关联用户账号信息)
- 一对多: `labels` → MailLabel
- 一对多: `threads` → MailThread
- 一对多: `messages` → MailMessage

**实例方法**:
- `link_or_create_official_account()`: 自动关联或创建 OfficialAccount
  - 如果已有关联，直接返回现有的 OfficialAccount
  - 如果存在相同邮箱的 OfficialAccount，则建立关联
  - 如果不存在，则创建新的 OfficialAccount 并建立关联
  - 返回值: 关联的 OfficialAccount 实例

**提供商选项**:
- `gmail` - Gmail
- `imap` - IMAP

---

### 2. MailThread (邮件会话线程)

**表名**: `data_aggregation_mailthread`

存储邮件会话线程信息，相同主题的邮件归属到同一线程。

| 字段 | 类型 | 必填 | 说明 | 示例 |
|------|------|------|------|------|
| `id` | BigInteger | 自动 | 主键ID | `1` |
| `account` | ForeignKey | ✓ | 所属账号 | `MailAccount(1)` |
| `provider_thread_id` | String(128) | ✓ | 提供商的线程ID | `19bc4da23fe37661` |
| `subject_norm` | String(512) | ✗ | 标准化主题 | `お客様の商品は配送中です` |
| `last_message_at` | DateTime | ✗ | 最后一封邮件时间 | `2026-01-16T03:29:44Z` |
| `created_at` | DateTime | 自动 | 创建时间 | `2026-01-16T12:00:00Z` |

**约束**:
- 唯一约束: `(account, provider_thread_id)`

**索引**:
- `(account, last_message_at)` - 按账号和时间查询

---

### 3. MailLabel (Gmail 标签)

**表名**: `data_aggregation_maillabel`

存储 Gmail 标签信息，包括系统标签（INBOX、SENT等）和用户自定义标签。

| 字段 | 类型 | 必填 | 说明 | 示例 |
|------|------|------|------|------|
| `id` | BigInteger | 自动 | 主键ID | `1` |
| `account` | ForeignKey | ✓ | 所属账号 | `MailAccount(1)` |
| `provider_label_id` | String(128) | ✓ | 提供商的标签ID | `INBOX`, `Label_1` |
| `name` | String(255) | ✗ | 标签名称 | `INBOX`, `重要` |
| `is_system` | Boolean | ✓ | 是否为系统标签 | `true` |
| `created_at` | DateTime | 自动 | 创建时间 | `2026-01-16T12:00:00Z` |

**约束**:
- 唯一约束: `(account, provider_label_id)`

**系统标签列表**:
- `INBOX` - 收件箱
- `SENT` - 已发送
- `DRAFT` - 草稿
- `TRASH` - 垃圾箱
- `SPAM` - 垃圾邮件
- `UNREAD` - 未读
- `STARRED` - 已加星标
- `IMPORTANT` - 重要

---

### 4. MailMessage (邮件消息)

**表名**: `data_aggregation_mailmessage`

存储邮件的核心信息，包括发件人、收件人、主题、时间等。

| 字段 | 类型 | 必填 | 说明 | 示例 |
|------|------|------|------|------|
| `id` | BigInteger | 自动 | 主键ID | `1` |
| `account` | ForeignKey | ✓ | 所属账号 | `MailAccount(1)` |
| `thread` | ForeignKey | ✗ | 所属线程 | `MailThread(1)` |
| `provider_message_id` | String(128) | ✓ | 提供商的消息ID | `19bc4da23fe37661` |
| `provider_thread_id` | String(128) | ✗ | 提供商的线程ID | `19bc4da23fe37661` |
| `rfc_message_id` | String(255) | ✗ | RFC 822 Message-ID | `<CB.C2.61222@...>` |
| `date_header_at` | DateTime | ✗ | 邮件头中的日期 | `2026-01-16T03:29:44Z` |
| `internal_at` | DateTime | ✗ | 内部接收时间 | `2026-01-16T12:00:00Z` |
| `subject` | Text | ✗ | 邮件主题 | `お客様の商品は配送中です` |
| `snippet` | Text | ✗ | 邮件摘要（前500字符） | `Apple Store...` |
| `size_estimate` | Integer | ✗ | 邮件大小估计（字节） | `85858` |
| `has_attachments` | Boolean | ✓ | 是否有附件 | `false` |
| `from_address` | Email(254) | ✗ | 发件人邮箱 | `shipping@orders.apple.com` |
| `from_name` | String(255) | ✗ | 发件人姓名 | `Apple Store` |
| `sender_domain` | String(255) | ✗ | 发件人域名 | `orders.apple.com` |
| `to_recipients` | JSON | ✗ | 收件人列表 | `[{"address": "..."}]` |
| `to_text` | Text | ✗ | 收件人文本 | `user@example.com` |
| `raw_headers` | JSON | ✗ | 原始邮件头 | `{"from": "...", ...}` |
| `ingested_at` | DateTime | 自动 | 导入时间 | `2026-01-16T12:00:00Z` |
| `is_extracted` | Boolean | ✓ | 是否已提取信息 | `false` |

**约束**:
- 唯一约束: `(account, provider_message_id)`

**索引**:
- `(account, -date_header_at)` - 按账号和时间倒序查询
- `(account, -internal_at)` - 按账号和内部时间倒序查询
- `(account, from_address)` - 按发件人查询
- `(account, sender_domain)` - 按域名查询
- `(account, provider_thread_id)` - 按线程查询

**关系**:
- 多对多: `labels` → MailLabel (通过 MailMessageLabel)

---

### 5. MailMessageBody (邮件正文)

**表名**: `data_aggregation_mailmessagebody`

存储邮件正文内容，与 MailMessage 是一对一关系。

| 字段 | 类型 | 必填 | 说明 | 示例 |
|------|------|------|------|------|
| `id` | BigInteger | 自动 | 主键ID | `1` |
| `message` | OneToOne | ✓ | 关联的邮件 | `MailMessage(1)` |
| `text_plain` | Text | ✗ | 纯文本内容 | `Apple Store\n\n...` |
| `text_html` | Text | ✗ | HTML 内容 | `<!DOCTYPE HTML>...` |
| `text_as_html` | Text | ✗ | 纯文本转HTML | `<p>Apple Store</p>...` |
| `text_normalized` | Text | ✗ | 标准化文本 | `Apple Store...` |
| `created_at` | DateTime | 自动 | 创建时间 | `2026-01-16T12:00:00Z` |

**注意**:
- `text_html` 和 `text_plain` 至少有一个应该有内容
- `text_normalized` 用于全文搜索和分析

---

### 6. MailMessageLabel (邮件-标签关联表)

**表名**: `data_aggregation_mailmessagelabel`

多对多关系的中间表，关联邮件和标签。

| 字段 | 类型 | 必填 | 说明 | 示例 |
|------|------|------|------|------|
| `id` | BigInteger | 自动 | 主键ID | `1` |
| `message` | ForeignKey | ✓ | 邮件 | `MailMessage(1)` |
| `label` | ForeignKey | ✓ | 标签 | `MailLabel(1)` |
| `created_at` | DateTime | 自动 | 创建时间 | `2026-01-16T12:00:00Z` |

**约束**:
- 唯一约束: `(message, label)` - 同一邮件的标签不能重复

**索引**:
- `(label, message)` - 按标签查询邮件
- `(message, label)` - 按邮件查询标签

---

### 7. MailAttachment (邮件附件)

**表名**: `data_aggregation_mailattachment`

存储邮件附件的元数据信息。

| 字段 | 类型 | 必填 | 说明 | 示例 |
|------|------|------|------|------|
| `id` | BigInteger | 自动 | 主键ID | `1` |
| `message` | ForeignKey | ✓ | 所属邮件 | `MailMessage(1)` |
| `provider_attachment_id` | String(255) | ✗ | 提供商的附件ID | `ANGjdJ...` |
| `filename` | String(512) | ✗ | 文件名 | `invoice.pdf` |
| `mime_type` | String(255) | ✗ | MIME类型 | `application/pdf` |
| `size_bytes` | Integer | ✗ | 文件大小（字节） | `102400` |
| `storage_key` | String(1024) | ✗ | 存储位置 | `s3://bucket/...` |
| `sha256` | String(64) | ✗ | SHA256哈希值 | `a1b2c3d4...` |
| `is_inline` | Boolean | ✓ | 是否为内联附件 | `false` |
| `created_at` | DateTime | 自动 | 创建时间 | `2026-01-16T12:00:00Z` |

**索引**:
- `(message)` - 按邮件查询附件
- `(mime_type)` - 按文件类型查询
- `(sha256)` - 去重查询

**注意**:
- `storage_key` 可以指向本地文件系统、S3、Nextcloud 等存储位置
- `sha256` 用于检测重复附件，实现去重存储

---

## 使用场景示例

### 场景 1: 查询某个账号的所有未读邮件

```python
from apps.data_aggregation.models import MailAccount, MailMessage

# 获取账号
account = MailAccount.objects.get(email_address='user@example.com')

# 查询未读邮件
unread_messages = MailMessage.objects.filter(
    account=account,
    labels__provider_label_id='UNREAD'
).order_by('-date_header_at')
```

### 场景 2: 查询特定发件人的所有邮件

```python
# 查询来自 Apple 的邮件
apple_emails = MailMessage.objects.filter(
    account=account,
    sender_domain='apple.com'
).select_related('body').order_by('-date_header_at')

for email in apple_emails:
    print(f"主题: {email.subject}")
    print(f"发件人: {email.from_name} <{email.from_address}>")
    print(f"正文: {email.body.text_plain[:100]}...")
```

### 场景 3: 统计邮件标签分布

```python
from django.db.models import Count

# 统计各标签的邮件数量
label_stats = MailLabel.objects.filter(
    account=account
).annotate(
    email_count=Count('messages')
).values('name', 'email_count').order_by('-email_count')

for stat in label_stats:
    print(f"{stat['name']}: {stat['email_count']} 封邮件")
```

### 场景 4: 查询带附件的邮件

```python
# 查询有附件的邮件
messages_with_attachments = MailMessage.objects.filter(
    account=account,
    has_attachments=True
).prefetch_related('attachments')

for msg in messages_with_attachments:
    print(f"主题: {msg.subject}")
    for att in msg.attachments.all():
        print(f"  - 附件: {att.filename} ({att.size_bytes} bytes)")
```

### 场景 5: 自动关联邮箱账号与官方账号

```python
from apps.data_aggregation.models import MailAccount, OfficialAccount

# 获取或创建邮箱账号
mail_account, created = MailAccount.objects.get_or_create(
    email_address='customer@example.com',
    defaults={'provider': 'gmail'}
)

# 自动关联或创建官方账号
official_account = mail_account.link_or_create_official_account()

print(f"邮箱账号: {mail_account.email_address}")
print(f"官方账号ID: {official_account.account_id}")
print(f"官方账号邮箱: {official_account.email}")
print(f"官方账号姓名: {official_account.name or '(未设置)'}")

# 也可以通过反向关系访问
if official_account.mail_account:
    print(f"该官方账号关联的邮箱: {official_account.mail_account.email_address}")

# 批量处理：为所有未关联的邮箱账号创建官方账号
unlinked_accounts = MailAccount.objects.filter(official_account__isnull=True)
for account in unlinked_accounts:
    official = account.link_or_create_official_account()
    print(f"已为 {account.email_address} 创建/关联官方账号")
```

---

## 数据保留策略建议

1. **邮件正文**: 建议保留 90-365 天
2. **邮件元数据**: 可长期保留（主题、发件人、时间等）
3. **附件**: 按需保留，大文件可考虑归档到冷存储

---

## 性能优化建议

1. **索引优化**: 已为常用查询场景添加了索引
2. **分区建议**: 对于大量邮件，可按时间分区存储
3. **查询优化**:
   - 使用 `select_related()` 预加载外键关系
   - 使用 `prefetch_related()` 预加载多对多关系
   - 避免 N+1 查询问题

4. **存储优化**:
   - 邮件正文可考虑压缩存储
   - 大附件建议使用对象存储（S3、Nextcloud等）

---

## 相关文档

- [邮件批量导入 API 文档](API_EMAIL_INGEST.md)
- [数据聚合系统架构](ARCHITECTURE.md)
