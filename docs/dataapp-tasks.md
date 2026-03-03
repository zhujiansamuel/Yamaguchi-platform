# dataapp 任务列表

> 文档目的：为 dashboard 事件 API 设计提供参考。记录 dataapp 中所有可观测的后台任务。
>
> 最后更新：2026-03-02

---

## 项目概览

**dataapp** 是基于 Django 5.2 + Celery 的数据整合平台，负责从多个来源采集数据、处理后写入 PostgreSQL，并与 Nextcloud / OnlyOffice 双向同步。

核心分为两个 Django App：

| App | 职责 | Celery Worker Redis DB |
|---|---|---|
| `data_acquisition` | 数据采集（WebDAV、追踪、邮件） | DB 1（主队列） |
| `data_aggregation` | 数据聚合、REST API、Excel 导出 | DB 0 |

---

## 一、Nextcloud Excel 双向同步

**队列**：`acquisition_queue`（Redis DB 1）

| 任务 | 触发方式 | 关键逻辑 |
|---|---|---|
| `sync_nextcloud_excel` | Nextcloud webhook（文件变更）/ 手动 | WebDAV 拉取 Excel → 解析（含 `__id`/`__version`/`__op` 控制列）→ DB CRUD → 回写 ID；含 ETag 去重、版本冲突检测 |

**相关模型**：`NextcloudSyncState`、`SyncConflict`、`SyncLog`

**相关文件**：
- `apps/data_acquisition/tasks.py`
- `apps/data_acquisition/sync_handler.py`
- `apps/data_acquisition/webdav_client.py`
- `apps/data_acquisition/excel_parser.py`、`excel_writer.py`

**同步的数据模型**：Purchasing、OfficialAccount、GiftCard、DebitCard、CreditCard、TemporaryChannel

---

## 二、快递追踪

追踪系统分为两条独立管道，但结果端共用同一套 `TrackingBatch / TrackingJob` 模型。

### 2-A  Excel 驱动（用户上传 Excel）

**数据流**：用户上传 Excel 到 Nextcloud → 提取追踪 URL → 调用 Web Scraper API → 解析结果 → 回写 Excel / 写入 DB

| 任务名（task_name） | 简称 | 说明 |
|---|---|---|
| `yamato_tracking_only` | YTO | Yamato 运输单件直查 |
| `yamato_tracking_10` | YT10 | Yamato 10件批量（一次 URL 含 10 单） |
| `japan_post_tracking_only` | JPTO | 日本郵便单件直查 |
| `japan_post_tracking_10` | JPT10 | 日本郵便 10件批量 |
| `official_website_redirect_to_yamato_tracking` | OWRYT | Apple Store 官网 → 转跳 Yamato |
| `redirect_to_japan_post_tracking` | RTJPT | Apple Store 官网 → 转跳日本郵便 |
| `official_website_tracking` | OWT | Apple Store 官网直接追踪 |

**TrackingBatch `file_path`**：对应实际上传的 Excel 文件路径（如 `JPT10-20260301.xlsx`）

### 2-B  数据库驱动（查询 Purchasing 表中缺失字段的记录）

**数据流**：管理命令 / Celery 任务触发 → 查询 Purchasing 表 → 动态构建 URL → 创建虚拟 TrackingBatch → 调用 Web Scraper API → 更新 DB

**TrackingBatch `file_path`**：虚拟路径，格式为 `purchasing_query_<worker>_<uuid_short>`

| Worker | Redis DB | 查询条件 | 追踪类型 | 状态 |
|---|---|---|---|---|
| `tracking_number_empty` | DB 5 | 订单号以 `w` 开头；`tracking_number` 为空；有关联 `official_account.email` | Apple Store 官网（OWRYT） | **活跃** |
| `japan_post_tracking_10_tracking_number` | DB 6 | `shipping_method` 为日本郵便；`tracking_number` 为 12 位数字；未完成配送 | 日本郵便 10件批量（JPT10） | **活跃** |
| `confirmed_at_empty` | DB 2 | 所有关键字段均为空（最早阶段） | Playwright（开发中） | 占位 |
| `shipped_at_empty` | DB 3 | 有 `confirmed_at`，`shipped_at` 为空 | Playwright（开发中） | 占位 |
| `estimated_website_arrival_date_empty` | DB 4 | 有 `confirmed_at`/`shipped_at`，无预计到达日 | Playwright（开发中） | 占位 |
| `temporary_flexible_capture` | DB 7 | 自定义过滤条件（catch-all） | 按 filter 参数决定 | 按需 |

**防重复机制**：`last_info_updated_at` 字段 + 可配置间隔（默认 6 小时）；同时使用 `is_locked` / `locked_at` / `locked_by_worker` 做行级锁（5 分钟超时自动释放）

**管理命令**：
```bash
python manage.py run_tracking_number_empty
python manage.py run_japan_post_tracking_10_tracking_number
python manage.py run_temporary_flexible_capture --filter '{"confirmed_at": "notnull"}'
```

---

## 三、邮件处理

**队列**：`email_parsing`（Redis DB 10），4 个独立 Worker

| 任务 | 说明 |
|---|---|
| `email_content_analysis` | 解析邮件头/正文，提取订单号、商品名、日期、收件人等结构化数据 |
| `initial_order_confirmation_email` | 创建/更新 Purchasing 记录，关联 OfficialAccount，更新 iPhone/iPad 库存 |
| `order_confirmation_notification_email` | 更新已有 Purchasing 记录状态 |
| `send_notification_email` | 向用户发出通知邮件 |

**相关文件**：`apps/data_acquisition/EmailParsing/`

---

## 四、数据聚合与 Excel 导出

**队列**：`aggregation_queue`（Redis DB 0）

| 任务 / 接口 | 说明 |
|---|---|
| `POST /api/aggregation/email-ingest/batch/` | 批量邮件摄入 |
| Excel 导出（15+ 种） | iPhone、iPad、Purchasing、GiftCard、DebitCard、CreditCard、OtherPayment、Inventory、EcSite、OfficialAccount、TemporaryChannel 等 |

---

## 五、Webhook / 外部回调

| 来源 | 接口 | 说明 |
|---|---|---|
| Nextcloud | `POST /api/acquisition/webhook/nextcloud/` | 文件变更时触发，HMAC Token 验证，分发 `sync_nextcloud_excel` 任务 |
| OnlyOffice | `POST /api/acquisition/onlyoffice_callback/` | 文档编辑完成回调，IP 白名单验证，解析变更后转发至 Nextcloud |

---

## 六、任务总数汇总

| 分组 | 任务数 |
|---|---|
| Nextcloud 同步 | 1 |
| 快递追踪（Excel 驱动） | 7 |
| 快递追踪（DB 驱动） | 6 |
| 邮件处理 | 4 |
| 数据聚合 / 导出 | ~15（按导出类型计） |

核心可观测任务约 **18 个**（同步 1 + 追踪 13 + 邮件 4）。

---

## 七、关键数据模型

| 模型 | 位置 | 用途 |
|---|---|---|
| `TrackingBatch` | `data_acquisition` | 追踪批次（含 Excel 驱动和 DB 驱动） |
| `TrackingJob` | `data_acquisition` | 单条追踪任务 |
| `SyncLog` | `data_acquisition` | 所有操作审计日志 |
| `NextcloudSyncState` | `data_acquisition` | 每个文件的同步状态（含 ETag） |
| `SyncConflict` | `data_acquisition` | 版本冲突记录 |
| `Purchasing` | `data_aggregation` | 采购订单（含锁字段、追踪字段） |
| `AcquisitionTask` | `data_acquisition` | 任务执行历史 |
