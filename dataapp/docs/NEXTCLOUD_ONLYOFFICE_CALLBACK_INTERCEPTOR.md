# Nextcloud OnlyOffice Callback Interceptor 开发者说明

本文面向开发者说明 `nextcloud_apps/onlyoffice_callback_interceptor` 插件的运行逻辑、主要组件与回调流转方式，便于理解它如何拦截 OnlyOffice 的回调并转发给 Django 后端。

## 插件目标与核心思路

该插件的核心目标是：

1. **在打开 OnlyOffice 编辑器时**，拦截并改写 `callbackUrl`，将回调先发往 Django 后端。
2. **在 OnlyOffice 回调触发时**，捕获回调请求并向 Django 发送通知，辅助数据处理或同步。
3. **在 OnlyOffice 保存文件时**，捕获 Nextcloud 的文件写入事件，并向 Django 发送文件更新通知。
4. **提供健康检查与可配置开关**，在后端不可用时自动跳过拦截。

## 运行时流程概览

```
用户打开 OnlyOffice 编辑器
  └─ Nextcloud 返回 editor config
      └─ CallbackInterceptorMiddleware 修改 callbackUrl -> Django
          └─ OnlyOffice 回调先到 Django
              └─ Django 再转发回 Nextcloud 的原始 callback

OnlyOffice 回调 /apps/onlyoffice/track
  └─ CallbackInterceptListener 侦测并通知 Django

Nextcloud 文件保存
  └─ FileWriteListener 监听文件写入事件并通知 Django
```

## 关键运行逻辑

### 1) App 启动与事件注册

入口位于：`lib/AppInfo/Application.php`。

- 在 `register()` 中注册文件写入事件监听：
  - `NodeWrittenEvent`
  - `NodeCreatedEvent`
  - `BeforeNodeWrittenEvent`
- 注册 HTTP 生命周期监听：`BeforeControllerEvent`（用于 OnlyOffice `/track` 回调）
- 注册中间件：`CallbackInterceptorMiddleware`
- 在 `boot()` 中记录启动日志，并对 `/apps/onlyoffice/track` 请求做一次早期探测。

### 2) OnlyOffice 编辑器配置拦截

拦截点：`lib/Middleware/CallbackInterceptorMiddleware.php`。

**触发条件**：
- Controller 为 `OCA\Onlyoffice\Controller\EditorApiController`
- 方法名为 `config`

**处理逻辑**：
1. 判断插件是否启用（`ConfigService::isEnabled()`）。
2. 若开启健康检查，按配置间隔执行 `HealthCheckService::checkIfNeeded()`。
3. 从 `JSONResponse` 中提取 `editorConfig.callbackUrl` 与文件路径。
4. 检查文件路径是否匹配过滤规则（`matchesPathFilter`）。
5. 构建新的 Django 回调 URL：
   - 追加 `nextcloud_callback`
   - 可选追加 `file_path`、`user_id`、`user_display_name`、`edit_start_time`
6. 如果 OnlyOffice Secret 已配置且响应包含 `token`，重新签名 JWT。

> 该中间件是 **主要拦截点**，确保用户打开编辑器时回调 URL 指向 Django。

### 3) OnlyOffice Track 回调监听

监听器：`lib/Listener/CallbackInterceptListener.php`。

**触发条件**：
- `BeforeControllerEvent` 且 Controller 为 `OCA\Onlyoffice\Controller\CallbackController::track`
- 或 URI 包含 `/apps/onlyoffice/track`

**处理逻辑**：
1. 判断插件是否启用。
2. 解析请求参数或 JSON Body。
3. 若包含 `doc` Token（JWT），解码获取文件信息。
4. 判断文件路径是否符合过滤规则。
5. 组装 metadata（文件、用户、回调状态等）。
6. 使用 `NotificationService::notifyDjango()` 向 Django 发送通知。

### 4) Nextcloud 文件保存事件

监听器：`lib/Listener/FileWriteListener.php`。

**触发条件**：
- 监听 `NodeWrittenEvent / NodeCreatedEvent / BeforeNodeWrittenEvent`

**处理逻辑**：
1. 确认事件是文件事件且为 `File` 类型。
2. 检查插件启用状态。
3. 获取文件路径并检查路径过滤规则。
4. 判断是否为 OnlyOffice 保存：
   - `User-Agent` 包含 `Node.js`
   - 或请求 URI 包含 `/apps/onlyoffice/track`
   - 或 `Referer` 包含 `onlyoffice`
5. 收集文件与用户元数据，通知 Django。

> 该监听器用于 **文件写入后补充通知**，用于数据落库或其他后端处理。

## 主要配置与服务

### ConfigService (`lib/Service/ConfigService.php`)

负责读取与保存插件配置，包含：

- `enabled`：是否启用拦截
- `django_callback_url`：后端回调地址
- `onlyoffice_secret`：JWT 签名密钥
- `path_filter`：路径过滤（默认 `/Data/`）
- `auth_token`：回调请求携带的认证 Token
- `health_check_url / health_check_interval / backend_healthy`
- `include_user_metadata / include_timestamp`

### HealthCheckService (`lib/Service/HealthCheckService.php`)

用于检查 Django 服务是否可用：

- 按 `health_check_interval` 执行
- 结果缓存于 `backend_healthy` 与 `last_health_check`
- 若不可用则跳过拦截

### NotificationService (`lib/Service/NotificationService.php`)

负责向 Django 发送通知请求：

- `POST` 请求
- `Content-Type: application/json`
- 可附带 `X-Auth-Token`
- 请求 URL 自动拼接 `file_path`、`user_id` 等 query 参数

## 关键 URL 参数格式

在改写 `callbackUrl` 时构造的参数：

- `nextcloud_callback`：原始 Nextcloud 回调 URL
- `file_path`：文件路径
- `user_id` / `user_display_name`
- `edit_start_time`（ISO 8601 时间戳）

示例：

```
http://example.com/api/onlyoffice/callback/?nextcloud_callback=...&file_path=/Data/...&user_id=admin
```

## 典型交互与排错建议

- **回调未被拦截**：
  - 确认 `enabled=true`
  - 检查 `path_filter` 是否匹配文件路径
  - 确认 Django 健康检查通过

- **OnlyOffice 回调未通知 Django**：
  - 检查 Nextcloud 日志（debug 模式）
  - 确认 `/apps/onlyoffice/track` 被触发
  - 确认 `django_callback_url` 配置正确

- **文件保存后未通知**：
  - 判断请求是否来自 OnlyOffice（User-Agent/Referer/URI）
  - 验证文件路径过滤逻辑

## 目录结构（快速定位）

```
onlyoffice_callback_interceptor/
├── appinfo/
├── lib/
│   ├── AppInfo/Application.php
│   ├── Listener/
│   │   ├── CallbackInterceptListener.php
│   │   └── FileWriteListener.php
│   ├── Middleware/CallbackInterceptorMiddleware.php
│   └── Service/
│       ├── ConfigService.php
│       ├── HealthCheckService.php
│       └── NotificationService.php
├── templates/
├── js/
├── css/
└── README.md
```

## 备注

- 如果 Django 后端不可用，`HealthCheckService` 会阻止回调 URL 的改写，避免造成编辑失败。
- 插件逻辑既包含 **配置拦截**，也包含 **保存事件监听** 与 **回调监听**，用于保证多场景下都能触发 Django 同步。
