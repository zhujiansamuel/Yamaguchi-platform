# Nextcloud + OnlyOffice 同步与回调说明

## 概述

系统通过 Nextcloud Webhook 与 OnlyOffice Callback 两条链路，实现 Excel 文件与 Django 数据库的同步，以及 OnlyOffice 保存事件的代理转发。整体行为以代码实现为准，以下内容基于当前项目代码整理。

## 架构概览

```
Nextcloud (文件变更)
    ↓ Webhook
Django /api/acquisition/webhook/nextcloud/
    ↓ Celery 异步任务
SyncHandler (WebDAV 下载 → 解析 DATA sheet → DB 写入 → 回写 __id)

OnlyOffice (文档保存)
    ↓ Callback
Django /api/acquisition/onlyoffice/callback/
    ├─ 记录 SyncLog
    ├─ status=2 时触发:
    │    ├─ 追踪任务（按路径前缀匹配）或
    │    └─ 下载文档并同步到数据库
    └─ 转发回调到 Nextcloud（确保文件落盘）
```

## 关键端点

| 功能 | URL | 方法 | 说明 |
| --- | --- | --- | --- |
| Nextcloud Webhook | `/api/acquisition/webhook/nextcloud/` | POST | Nextcloud 文件变更通知入口。 |
| OnlyOffice Callback | `/api/acquisition/onlyoffice/callback/` | GET/POST | OnlyOffice 回调入口，GET 用于健康检查。 |

> 路由定义见 `apps/data_acquisition/urls.py` 与 `config/urls.py`。

## Nextcloud Webhook（文件变更）

### 请求格式

**Headers**
- `X-Nextcloud-Webhook-Token: <token>`

**Body (JSON)**
```json
{
  "event": "file_changed",
  "path": "/Data/Purchasing_abc123.xlsx",
  "user": "admin"
}
```

> 注意：代码中使用 `path` 字段，不是 `file_path`。

### 响应
- 成功触发任务：`{"status":"success","message":"Task dispatched"}`
- Token 错误：HTTP 401

### 处理逻辑
- 通过 `X-Nextcloud-Webhook-Token` 校验请求。
- 触发 Celery 任务 `sync_nextcloud_excel(file_path, user)`。

## Nextcloud Excel 同步规则

### 支持的模型
- `Purchasing`
- `OfficialAccount`
- `GiftCard`
- `DebitCard`
- `CreditCard`
- `TemporaryChannel`

> 见 `apps/data_acquisition/sync_handler.py` 中 `MODEL_APP_MAP`。

### 文件命名与路径
- 文件路径示例：`/Data/Purchasing_abc123.xlsx`
- 文件名中下划线前的片段作为模型名（例如 `Purchasing`）。

### DATA Sheet 格式
Excel 必须包含名为 `DATA` 的 sheet，字段示例如下：

| __id | __version | __op | field1 | field2 | ... |
|------|-----------|------|--------|--------|-----|
| 123  | 2025-01-15 10:30:00 | UPDATE | value1 | value2 | ... |
|      | 2025-01-15 10:35:00 |        | value1 | value2 | ... |
| 456  | 2025-01-15 10:40:00 | DELETE |        |        | ... |

### 特殊列说明
- `__id`: Django 主键。为空时视为新建并回写。
- `__version`: 版本时间戳，用于冲突检测。
- `__op`: `UPDATE` / `DELETE` / 空值（空值时按是否有 `__id` 判断新建/更新）。

### 同步过程
1. WebDAV 下载 Excel
2. 解析 `DATA` sheet
3. 写入数据库并执行冲突检测
4. 回写新建记录的 `__id`

## OnlyOffice Callback（文档保存）

### URL Query 参数
OnlyOffice 由 Nextcloud 插件转发到 Django，并附带参数：

| 参数 | 说明 |
| --- | --- |
| `nextcloud_callback` | 原始 Nextcloud callback URL（URL-encoded）。 |
| `file_path` | 文件路径（URL-encoded）。 |
| `user_id` | Nextcloud 用户 ID（可选）。 |
| `user_display_name` | 用户显示名（可选）。 |
| `edit_start_time` | ISO 8601 时间戳（可选）。 |

### 请求体
OnlyOffice 使用 JSON 发送回调，字段以官方文档为准，常用字段示例：

```json
{
  "status": 2,
  "key": "Qw1234567890abcdef",
  "url": "http://onlyoffice/cache/files/Qw1234567890abcdef/output.xlsx",
  "users": ["admin"],
  "lastsave": "2025-01-01T10:35:00.000Z",
  "notmodified": false
}
```

### 状态码处理
- **仅处理 `status=2`（Ready for saving）**。
- 其他状态码会记录日志并直接转发回 Nextcloud。

### 处理流程（status=2）
1. **写入日志**：`SyncLog` 记录完整 callback 数据。
2. **任务触发优先级**：
   - 若文件路径匹配追踪任务配置（`TRACKING_TASK_CONFIGS`），触发对应异步任务。
   - 否则使用 `url` 下载文件并同步到数据库。
   - 若 `url` 缺失但 `file_path` 存在，尝试 WebDAV 回退下载。
3. **回调转发**：若存在 `nextcloud_callback` 参数，转发原始 callback 给 Nextcloud。

### 追踪任务触发规则（摘要）
- 通过 `file_path` 包含的 `path_keyword` 与文件名 `filename_prefix` 匹配。
- 配置在 `apps/data_acquisition/tasks.py` 的 `TRACKING_TASK_CONFIGS` 中。

## OnlyOffice Excel 导入规则

### 支持的模型
OnlyOffice 导入仅针对以下模型（`ONLYOFFICE_IMPORT_MODELS`）：

- `iPhone`
- `iPad`
- `Inventory`
- `EcSite`
- `LegalPersonOffline`
- `TemporaryChannel`
- `OfficialAccount`
- `Purchasing`
- `GiftCard`
- `GiftCardPayment`
- `DebitCard`
- `DebitCardPayment`
- `CreditCard`
- `CreditCardPayment`

### 文件命名要求
- `get_onlyoffice_model_name()` 支持：`{ModelName}_test.xlsx` 或 `{ModelName}_test_YYYYMMDD_HHMMSS.xlsx`。

### 解析规则
- 读取第一张 sheet 的表头行。
- 表头根据导出器 `get_header_names()` 映射到模型字段。
- 空行跳过，关键字段用于 `update_or_create`。

## 配置项（环境变量）

主要配置位于 `config/settings/base.py`：

```env
NEXTCLOUD_WEBDAV_URL=http://nextcloud-web/remote.php/dav/files/admin/
NEXTCLOUD_USERNAME=admin
NEXTCLOUD_PASSWORD=your-password
NEXTCLOUD_WEBHOOK_TOKEN=your-secure-token

# OnlyOffice callback IP 白名单
ALLOWED_CALLBACK_IPS=172.18.0.0/16
```

## 日志与监控

- `SyncLog`：记录 Nextcloud 同步、OnlyOffice 回调和任务触发等操作。
- `SyncConflict`：记录版本冲突。
- `NextcloudSyncState`：记录文件 ETag 状态。

可在 Django Admin 中查看：`/admin/`。

## 常见问题排查

### 1. Webhook 返回 401
- 检查 `NEXTCLOUD_WEBHOOK_TOKEN` 与请求 header 是否一致。

### 2. OnlyOffice callback 被拒绝
- 检查 `ALLOWED_CALLBACK_IPS` 是否包含 OnlyOffice 服务器 IP 或 CIDR。

### 3. 回调转发失败
- 确认 `nextcloud_callback` URL 是否可访问。

### 4. OnlyOffice 保存未触发同步
- 仅处理 `status=2`。
- 确认 callback JSON 内含 `status=2` 与 `url`。

## 参考文件

- Django 回调与同步逻辑：`apps/data_acquisition/views.py`
- Nextcloud 同步任务：`apps/data_acquisition/tasks.py`
- 同步处理器：`apps/data_acquisition/sync_handler.py`
- Nextcloud 回调拦截插件：`nextcloud_apps/onlyoffice_callback_interceptor/`
