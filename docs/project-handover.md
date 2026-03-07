# 项目交接文档

> **项目名称**: Yamaguchi Platform
> **开发周期**: 2024年9月 ~ 2025年2月
> **交接日期**: 2025年2月
> **文档版本**: v1.0

---

## 目录

1. [项目总览](#1-项目总览)
2. [系统架构](#2-系统架构)
3. [各项目详细说明](#3-各项目详细说明)
4. [部署架构](#4-部署架构)
5. [技术栈汇总](#5-技术栈汇总)
6. [开发工作总结](#6-开发工作总结)
7. [已知问题与待办事项](#7-已知问题与待办事项)
8. [附录：仓库管理](#8-附录仓库管理)

---

## 1. 项目总览

Yamaguchi Platform 是一个面向二手 iPhone 买取业务的综合管理平台，涵盖电商网站、价格监控、库存管理、数据整合、自动化脚本、日志监控和任务看板等多个子系统。

| 子项目 | 类型 | 定位 | 来源 |
|--------|------|------|------|
| **ecsite** | Web 应用 | 二手手机买取电商网站 (mobile-zone.jp) | 外部购买（FastAdmin + ThinkPHP），二次开发 |
| **webapp** | Web 应用 | iPhone 买取价格监控与分析系统 | 自建 |
| **dataapp** | Web 应用 | 数据整合平台（采集、聚合、同步） | 自建 |
| **auto** | 自动化脚本 | 定期执行的价格抓取、翻译、数据同步等脚本 | 自建 |
| **desktopapp** | 桌面应用 | iPhone 库存管理（扫码入库） | 自建 |
| **dedktoptools** | 桌面工具 | PDF 批量重命名工具 | 自建 |
| **n8n-auto** | 自动化脚本 | 配合 n8n 平台的自动化脚本 | 自建 |
| **dev** | 基础设施 | ELK 集中日志平台 | 自建 |
| **dashboard** | Web 应用 | 统一任务监控仪表盘 | 自建 |

---

## 2. 系统架构

### 2.1 整体架构图

```
                        ┌──────────────────────────────────┐
                        │          用户 / 客户端            │
                        └──────┬───────────┬───────────────┘
                               │           │
                     ┌─────────▼──┐   ┌────▼────────────┐
                     │  ecsite    │   │  desktopapp     │
                     │ (电商网站)  │   │ (Windows 桌面端) │
                     │ ThinkPHP   │   │  C++ / Qt6      │
                     └─────┬──────┘   └──────┬──────────┘
                           │                 │ API
                           │                 │
┌──────────┐         ┌─────▼─────────────────▼──────┐        ┌──────────────┐
│ webapp   │◄────────│          dataapp              │◄───────│    auto      │
│(价格监控) │  API    │       (数据整合平台)            │ 脚本调用 │ (系统服务)   │
│ Django   │────────►│   Django + Celery + Redis     │        │ Python 脚本  │
└──────────┘         └──────────┬───────────────────-┘        └──────────────┘
                                │
              ┌─────────────────┼─────────────────┐
              │                 │                 │
      ┌───────▼──────┐  ┌──────▼──────┐  ┌───────▼──────┐
      │  dashboard   │  │  n8n-auto   │  │     dev      │
      │ (任务看板)    │  │ (n8n 集成)   │  │ (ELK 日志)   │
      │ Vue3+FastAPI │  │ FastAPI     │  │ Docker       │
      └──────────────┘  └─────────────┘  └──────────────┘
```

### 2.2 项目间交互关系

| 源项目 | 目标项目 | 交互方式 | 说明 |
|--------|----------|----------|------|
| desktopapp | dataapp | REST API | 库存登录、商品查询、IMEI 验证 |
| auto | dataapp | 脚本调用 | 价格数据写入、翻译结果同步 |
| auto | 外部网站 | 爬虫抓取 | iphonekaitori.tokyo 等价格源 |
| n8n-auto | dataapp | REST API | 配合 n8n 进行自动化价格同步 |
| dashboard | dataapp | REST API (SSE) | 监控 Nextcloud 同步、Tracking、Email 任务 |
| dashboard | webapp | REST API (SSE) | 监控价格抓取任务状态 |
| webapp | ecsite | REST API | 价格同步（计划中，尚未实现） |
| dev (ELK) | 全部 Docker 服务 | 日志采集 | Filebeat 收集容器日志 |

---

## 3. 各项目详细说明

### 3.1 ecsite — 二手手机买取电商网站

**用途**: 面向客户的二手 iPhone 买取（收购）电商网站，域名为 mobile-zone.jp。

**技术栈**:
- 后端: PHP 8.0+ / ThinkPHP 6 框架
- 前端模板引擎: ThinkPHP 模板
- 管理后台: FastAdmin (基于 ThinkPHP)
- 数据库: MySQL
- 缓存: Redis
- Web 服务器: nginx
- 容器化: Docker Compose

**核心功能**:
- 商品展示与分类管理
- 在线买取申请流程
- 用户注册与认证
- 管理后台（商品管理、订单管理、用户管理）
- 多语言支持（日语为主）
- API 接口（供外部系统调用）
  - `GET /api/goodsprice/list` — 商品价格列表
  - `POST /api/goodsprice/update` — 价格更新
  - Token 认证机制

**项目结构**:
```
ecsite/
├── application/          # ThinkPHP 应用代码
│   ├── admin/            # 管理后台
│   ├── api/              # API 接口
│   ├── index/            # 前台页面
│   └── common/           # 公共模块
├── public/               # Web 根目录
│   ├── assets/           # 静态资源
│   └── index.php         # 入口文件
├── config/               # 配置文件
├── runtime/              # 运行时缓存
├── docker-compose.yml    # 容器编排
├── Dockerfile            # PHP 容器定义
└── nginx.conf            # nginx 配置
```

**来源说明**: 该项目是外部购买的 FastAdmin + ThinkPHP 商城系统，在此基础上进行了二次开发定制，包括添加 API 接口、适配买取业务流程、定制前台页面等。

---

### 3.2 webapp — iPhone 买取价格监控与分析系统

**用途**: 从多个竞品网站抓取 iPhone 买取价格数据，进行统计指标计算、趋势分析和因果推断，辅助定价决策。

**技术栈**:
- 后端: Python 3.11+ / Django 4.2+ / Django REST Framework
- 异步任务: Celery + Redis
- 数据库: PostgreSQL（业务数据）+ ClickHouse（分析数据仓库）
- 计算引擎: PyTorch（向量化特征计算）+ CuPy（GPU 加速，可选）
- 统计建模: statsmodels 0.14.4（VAR 模型、Granger 因果检验）
- 前端: Django 模板 + Chart.js（价格趋势图）
- 浏览器自动化: Playwright（爬虫使用）
- 容器化: Docker Compose
- Web 服务器: Daphne (ASGI)

**核心功能**:

1. **价格爬虫**: 定时抓取多个竞品网站的 iPhone 买取价格，存入 PostgreSQL

2. **数据管道 (ETL Pipeline)**:
   - `engine/pipeline.py` — 编排完整流程: 读取 → 对齐 → 聚合 → 特征计算 → Cohort → 写入 ClickHouse
   - `engine/reader.py` — 从 PostgreSQL 读取原始价格记录
   - `engine/align.py` — 将价格数据对齐到 15 分钟时间桶（Bucket），取每个 (shop, iphone, bucket) 最近记录
   - 支持 CPU / GPU 设备选择，支持按天分批处理

3. **统计指标计算**:
   - `engine/aggregate.py` — 构建 3D 价格张量 (iphones × shops × buckets)，跨店铺聚合计算:
     - **均值 (mean)**、**中位数 (median)**、**标准差 (std)**、**离散系数 (dispersion)**
     - 店铺计数 (shop_count)，支持最低法定人数验证
   - `engine/features.py` — PyTorch 向量化特征计算，三个时间窗口 (120min / 900min / 1800min):
     - **EMA** (指数移动平均): α = 2/(window+1)
     - **SMA** (简单移动平均): F.conv1d 向量化
     - **WMA** (加权移动平均): 线性权重
     - **Bollinger Bands** (布林带): Mid (SMA) ± k×std，含 upper/lower/width
     - 共计 **32 个特征列**
   - `engine/cohorts.py` — Cohort（群组）加权聚合:
     - 定义 Cohort 成员和店铺权重
     - 加权计算群组级别 mean/median/std
     - 在群组均值基础上重新计算所有特征

4. **因果推断 (AutoML Causal Analysis)** — 三阶段自动化因果分析管道:
   - **Stage 1 - 预处理 (Preprocessing-Rapid)**:
     - 计算 log_price → dlog_price（对数收益率）→ z_dlog_price（标准化）
     - 支持 CuPy GPU 加速，自动回退到 CPU
     - 存入 `AutomlPreprocessedSeries` 表
   - **Stage 2 - VAR 模型拟合 (Cause-and-Effect-Testing)**:
     - 向量自回归模型 (Vector AutoRegression)，statsmodels 实现
     - 面板数据构建: (time × shops) 的 z_dlog_price 矩阵
     - 数据质量检查: 前向填充、低覆盖行剔除、常量列/高相关列移除
     - AIC 自动选择最优滞后阶数（最大 12 阶）
     - 存入 `AutomlVarModel` 表（系数、AIC、BIC、样本量）
   - **Stage 3 - 因果影响量化 (Quantification-of-Impact)**:
     - **Granger 因果检验**: 检验所有店铺对之间的因果关系
     - F-test 多滞后阶（最大 5 阶），提取最小 p 值和最优滞后
     - 显著性判断: min_pvalue < 0.05
     - 因果权重: VAR 系数绝对值之和
     - 置信度: max(0, min(1, 1 - min_pvalue))
     - 存入 `AutomlGrangerResult`（全部检验结果）和 `AutomlCausalEdge`（显著因果关系）

5. **趋势分析**:
   - `api/trends/core.py` — 多线均线趋势计算:
     - **A-line**: 原始最近邻重采样
     - **B-line**: 时间窗口移动平均（默认 60 分钟）
     - **C-line**: 时间窗口移动平均（默认 240 分钟）
   - 支持跨颜色合并、按颜色分拆、降采样
   - 并行数据库 I/O (ThreadPoolExecutor)

6. **Dashboard API**: 向 dashboard 系统提供爬虫任务状态接口
   - `GET /api/dashboard/scraper-events/` — 爬虫事件流

**ClickHouse 数据仓库**:

两张核心分析表（`clickhouse/init.sql`）:

| 表 | 用途 | 分区 |
|---|---|---|
| `price_aligned` | 对齐后的价格记录 (shop_id, iphone_id, bucket, prices) | (run_id, toYYYYMM(bucket)) |
| `features_wide` | 计算后的特征值 (32列统计指标 + scope维度) | (run_id, toYYYYMM(bucket)) |

ClickHouse 服务层 (`services/clickhouse_service.py`):
- 批量插入、分区查询、run 管理（list/promote/drop）
- 惰性客户端初始化，连接池管理

**AutoML 数据模型** (PostgreSQL):

| 模型 | 用途 |
|------|------|
| `AutomlCausalJob` | 分析作业主表（三阶段状态跟踪） |
| `AutomlPreprocessedSeries` | 预处理后的时间序列 |
| `AutomlVarModel` | VAR 模型参数（系数、AIC、BIC） |
| `AutomlGrangerResult` | Granger 检验结果（p 值、滞后阶） |
| `AutomlCausalEdge` | 显著因果关系（权重、置信度） |

**AutoML API 端点** (`api/api_automl.py`):

| 端点 | 功能 |
|------|------|
| `TriggerPreprocessingRapidView` | 触发预处理任务 |
| `TriggerCauseAndEffectTestingView` | 触发 VAR 建模 |
| `TriggerQuantificationOfImpactView` | 触发 Granger 检验 |
| `ScheduleAutoMLJobsView` | 批量调度所有活跃 iPhone 的分析作业 |
| `SlidingWindowAnalysisView` | 滑动窗口分析任务 |
| `AutoMLJobStatusView` | 查询作业状态 |
| `AutoMLJobResultView` | 获取因果分析结果 |
| `CompletedJobsListView` | 按 iPhone 列出已完成作业 |

**项目结构**:
```
webapp/
├── AppleStockChecker/
│   ├── engine/               # 计算引擎
│   │   ├── pipeline.py       # ETL 编排
│   │   ├── reader.py         # PG 数据读取
│   │   ├── align.py          # 时间桶对齐
│   │   ├── aggregate.py      # 跨店铺聚合 (3D 张量)
│   │   ├── features.py       # 特征计算 (EMA/SMA/WMA/Bollinger)
│   │   ├── cohorts.py        # Cohort 加权聚合
│   │   └── config.py         # 管道配置
│   ├── services/
│   │   └── clickhouse_service.py  # ClickHouse 读写服务
│   ├── clickhouse/
│   │   └── init.sql          # ClickHouse 建表 DDL
│   ├── tasks/
│   │   └── automl_tasks.py   # 三阶段因果分析 Celery 任务
│   ├── api/
│   │   ├── api_automl.py     # AutoML REST API
│   │   └── trends/           # 趋势分析 API
│   │       ├── core.py       # 趋势计算核心
│   │       ├── model_colors.py   # 完整趋势（含店铺明细）
│   │       ├── avg_only.py       # 仅均线（轻量）
│   │       └── color_std.py      # 按颜色标准差
│   ├── utils/
│   │   └── automl_tasks/
│   │       └── gpu_utils.py  # GPU (CuPy) 加速工具
│   ├── models.py             # Django ORM 模型
│   └── management/commands/  # 管理命令
│       ├── run_pipeline.py   # 执行数据管道
│       ├── promote_run.py    # 提升 run 到生产
│       └── drop_run.py       # 删除 ClickHouse run
├── YamagotiProjects/
│   └── settings.py           # ClickHouse 连接配置、GPU 设备设置
├── docker-compose.yml        # 容器编排
├── Dockerfile                # 应用容器
└── requirements.txt          # 依赖 (statsmodels, cupy, torch, pandas, etc.)
```

**关键依赖**:
- `statsmodels == 0.14.4` — VAR 模型、Granger 因果检验
- `cupy-cuda13x == 13.6.0` — GPU 加速（可选，自动回退 CPU）
- `torch` — PyTorch 向量化特征计算
- `clickhouse-driver` — ClickHouse 客户端
- `pandas == 2.3.2` / `numpy == 2.2.6` — 数据处理

**部署**: 独立部署在 Proxmox 虚拟机中。

---

### 3.3 dataapp — 数据整合平台

**用途**: 平台的数据中枢，负责库存收集与分类管理、快递追踪与到货状态自动更新、Nextcloud 数据同步、邮件处理等核心业务。

**技术栈**:
- 后端: Python 3.11+ / Django 4.2+ / Django REST Framework
- 异步任务: Celery + Redis + Celery Beat（多队列: default, tracking_webhook_queue 等）
- 数据库: PostgreSQL
- 文件同步: Nextcloud WebDAV + OnlyOffice 回调拦截
- 外部爬虫服务: WebScraper API（快递页面数据采集）
- 邮件处理: IMAP
- 容器化: Docker Compose
- Web 服务器: Gunicorn / Daphne
- Excel 处理: openpyxl（读写回写）

**核心功能**:

#### 3.3.1 库存收集与分类管理

**数据模型层级**:

```
商品主数据 (Product Master)
├── iPhone (继承 ElectronicProduct)  ─── part_number, model_name, capacity_gb, color, jan
├── iPad   (继承 ElectronicProduct)  ─── 同上
└── ElectronicProduct (抽象基类)

库存 (Inventory)
├── 状态: planned → in_transit → arrived → out_of_stock / abnormal
├── 商品关联: iphone FK / ipad FK（多态，通过 JAN 码匹配）
├── 设备标识: IMEI（最长 17 位）
├── 三级批次分类: batch_level_1 / batch_level_2 / batch_level_3
├── 时间追踪:
│   ├── transaction_confirmed_at   — 交易确认时间
│   ├── scheduled_arrival_at       — 预定到达时间
│   ├── checked_arrival_at_1       — 第一次确认到达时间
│   ├── checked_arrival_at_2       — 第二次确认到达时间
│   └── actual_arrival_at          — 实际到达时间
└── 四种来源 (source):
    ├── source1 → EcSite（电商平台订单）
    ├── source2 → Purchasing（采购订单）
    ├── source3 → LegalPersonOffline（法人线下店取）
    └── source4 → TemporaryChannel（临时渠道）
```

**库存来源分类**:

| 来源 | 模型 | 说明 | 创建方式 |
|------|------|------|----------|
| **Purchasing** | 采购订单 | 线上采购订单，含官方账号、快递追踪、支付信息 | Nextcloud Excel 同步 / API / 爬虫自动创建 |
| **LegalPersonOffline** | 法人线下 | 线下店面客户到店取货 | desktopapp API 调用 `create_with_inventory` |
| **EcSite** | 电商订单 | 来自 mobile-zone.jp 的预约订单 | Nextcloud Excel 同步 |
| **TemporaryChannel** | 临时渠道 | 临时性库存来源 | Nextcloud Excel 同步 |

**库存创建流程**:
- `Purchasing.create_with_inventory(**kwargs)` — 创建采购订单并自动创建关联库存:
  - 通过 JAN 码或 iPhone 型号名匹配商品（支持日语型号名解析，如 `iPhone 17 Pro Max 256GB コズミックオレンジ`）
  - 自动关联 OfficialAccount（通过 email 查找或创建）
  - 支持多商品订单（iphone_type_names 列表）
  - 自动处理支付卡关联（GiftCard / DebitCard / CreditCard）
  - IMEI 重复检测，重复时记录到 `DuplicateProduct` 表
- `LegalPersonOffline.create_with_inventory(inventory_data, **fields)` — 法人线下创建:
  - 接受 (jan, imei) 列表
  - 支持 skip_on_error 模式，部分失败不影响整体
  - 三级批次管理字段传递

**采购订单阶段统计** (`purchasing_stats` API):

| 阶段 | 名称 | 含义 |
|------|------|------|
| Stage 1 | `confirmed_at_empty` | 等待确认（所有字段为空） |
| Stage 2 | `shipped_at_empty` | 已确认未发货 |
| Stage 3 | `estimated_website_arrival_date_empty` | 已发货，等待官网预计到达 |
| Stage 4 | `tracking_number_empty` | 有预计到达日，等待邮寄单号 |
| Stage 5 | `estimated_delivery_date_empty` | 有邮寄单号，等待邮寄送达预计 |
| Stage 6 | `other` | 信息已完整或其他状态 |

每个阶段有对应的 **Worker** 自动处理缺失数据（见下文快递追踪）。

#### 3.3.2 快递追踪与到货状态自动更新

**整体流程**:

```
Nextcloud Excel 保存 / Worker 定时扫描
         │
         ▼
  [阶段一] 文件/数据源识别 → 根据文件名前缀匹配任务类型
         │
         ▼
  [阶段二] 创建 TrackingBatch + TrackingJob → 调用 WebScraper API 发布爬虫任务
         │
         ▼
  [阶段三] WebScraper 执行网页爬取（快递公司官网）
         │
         ▼
  [阶段四] WebScraper 回调 webhook → dataapp 接收
         │
         ▼
  [阶段五] 解析爬取数据 → 更新 Purchasing 记录（追踪号、配送状态、预计到达时间）
         │
         ▼
  [阶段六] 批量回写 Excel（每 10 条 + 批次完成时）
```

**追踪任务类型**:

| 任务名 | 前缀 | 快递公司 | 说明 |
|--------|------|----------|------|
| `official_website_redirect_to_yamato_tracking` | OWRYT- | ヤマト運輸 | 从官网重定向到ヤマト追踪页面，提取配送状态 |
| `redirect_to_japan_post_tracking` | — | 日本郵便 | OWRYT 重定向逻辑：如果ヤマト页面无数据，自动重定向到日本郵便 |
| `official_website_tracking` | OWT- | — | 直接从官网提取追踪信息 |
| `yamato_tracking_only` | YTO- | ヤマト運輸 | 仅通过追踪号查询ヤマト |
| `japan_post_tracking_only` | JPTO- | 日本郵便 | 仅通过追踪号查询日本郵便 |
| `japan_post_tracking_10` | JPT10- | 日本郵便 | 批量10件日本郵便追踪 |
| `yamato_tracking_10` | YT10- | ヤマト運輸 | 批量10件ヤマト追踪（直接调用API，不使用WebScraper） |

**自动化 Worker**:

系统通过多个 Worker 自动扫描处于各阶段的 Purchasing 记录，补全缺失信息:

| Worker | 扫描条件 | 动作 |
|--------|----------|------|
| `confirmed_at_empty` | 确认时间为空 | 爬取官网获取订单确认信息 |
| `shipped_at_empty` | 发货时间为空（已确认） | 爬取官网获取发货信息 |
| `estimated_website_arrival_date_empty` | 预计到达为空（已发货） | 爬取官网获取预计到达日 |
| `tracking_number_empty` | 追踪号为空（有预计到达日） | 爬取官网提取邮寄单号 |
| `japan_post_tracking_10_tracking_number` | 有追踪号待查询 | 批量查询日本郵便配送状态 |
| `yamato_tracking_10_tracking_number` | 有追踪号待查询 | 批量查询ヤマト配送状态 |
| `temporary_flexible_capture` | 临时性灵活抓取 | 按需灵活抓取官网信息 |
| `playwright_apple_pickup` | Apple 到店取货 | Playwright 自动化抓取取货信息 |

**数据更新逻辑** (以 `official_website_redirect_to_yamato_tracking` 为例):

1. WebScraper 抓取官网 → 重定向到ヤマト追踪页面 → 返回 CSV 数据
2. 解析 CSV: 提取 order_number、tracking_number、latest_delivery_status、estimated_delivery_date 等
3. 通过 order_number 查找对应 Purchasing 记录
4. 如果 Purchasing 不存在 → 自动创建（含 OfficialAccount 和 Inventory）
5. 如果ヤマト页面无数据（Discriminant 列全空）→ 自动重定向到 `redirect_to_japan_post_tracking`
6. 更新字段时进行 **冲突检测**: tracking_number、email 等关键字段如果已有值且不同，记录到 `OrderConflict` 表而不覆盖
7. 更新完成后解锁记录 (is_locked = False)

**批量回写机制** (`TrackingBatch.update_progress`):
- 每完成 10 个 TrackingJob 自动触发一次 Excel 回写
- 批次全部完成时触发最后一次回写
- 回写到 Nextcloud Excel 文件（通过 WebDAV）

**追踪数据模型**:

| 模型 | 用途 |
|------|------|
| `TrackingBatch` | 追踪批次（batch_uuid, task_name, 进度统计, 回写状态） |
| `TrackingJob` | 单个追踪任务（关联 batch, custom_id, target_url, 状态, writeback_data） |
| `OrderConflict` | 订单冲突记录（字段级冲突检测与记录） |
| `OrderConflictField` | 冲突字段详情 |
| `DuplicateProduct` | IMEI 重复记录 |

#### 3.3.3 Nextcloud 数据同步

- **Webhook 驱动**: Nextcloud 文件保存 → OnlyOffice 回调拦截器 → dataapp webhook
- **双向同步**: Excel → DB（通过 __id, __version, __op 列实现版本控制）+ DB → Excel（ID 回写）
- **冲突处理**: ETag + 版本号双重检测，冲突记录到 `SyncConflict` 表
- **支持的同步模型**: Purchasing, OfficialAccount, GiftCard, DebitCard, CreditCard, TemporaryChannel

#### 3.3.4 邮件自动处理

- IMAP 邮箱监控（`MailAccount` 配置）
- 邮件线程管理（`MailThread`）
- 邮件内容解析: 提取配送日期、订单信息等
- 邮件标签管理（`MailLabel`, `MailMessageLabel`）
- 附件处理（`MailAttachment`）

#### 3.3.5 Dashboard API

向 dashboard 系统提供各任务状态接口:
- `GET /api/dashboard/nextcloud-events/` — Nextcloud 同步事件
- `GET /api/dashboard/tracking-batches/` — Tracking 批次事件
- `GET /api/dashboard/email-events/` — 邮件处理事件

**项目结构**:
```
dataapp/
├── apps/
│   ├── core/                    # 核心模块
│   │   └── history.py           # 历史记录追踪基类
│   ├── data_aggregation/        # 数据聚合（业务模型层）
│   │   ├── models.py            # 核心模型: iPhone, iPad, Inventory, Purchasing,
│   │   │                        #   OfficialAccount, LegalPersonOffline, EcSite,
│   │   │                        #   TemporaryChannel, GiftCard/DebitCard/CreditCard,
│   │   │                        #   OrderConflict, Mail*, HistoricalData
│   │   ├── views.py             # REST API + purchasing_stats + inventory dashboard
│   │   ├── serializers.py       # DRF 序列化器
│   │   ├── admin.py             # Django Admin 配置
│   │   ├── utils.py             # WebScraper 导出、Excel 导出等工具
│   │   └── excel_exporters/     # Excel 导出器
│   │       └── iphone_inventory_dashboard_exporter.py
│   └── data_acquisition/        # 数据采集（任务调度层）
│       ├── tasks.py             # Celery 任务: 同步、追踪、回写
│       ├── views.py             # Webhook 接收: OnlyOffice 回调、WebScraper 回调
│       ├── sync_handler.py      # Nextcloud Excel 双向同步处理器
│       ├── excel_writeback.py   # Excel 回写逻辑
│       ├── yamato_parser.py     # ヤマト追踪页面 HTML 解析
│       ├── trackers/            # 追踪器（各快递公司数据处理）
│       │   ├── registry_tracker.py                          # 追踪器注册与分发
│       │   ├── official_website_redirect_to_yamato_tracking.py  # 官网→ヤマト
│       │   ├── redirect_to_japan_post_tracking.py           # 重定向→日本郵便
│       │   ├── official_website_tracking.py                 # 官网直接追踪
│       │   ├── yamato_tracking_only.py                      # ヤマト单独追踪
│       │   ├── japan_post_tracking_only.py                  # 日本郵便单独追踪
│       │   └── japan_post_tracking_10.py                    # 日本郵便批量追踪
│       ├── workers/             # 自动化 Worker（定时扫描补全数据）
│       │   ├── base.py                                      # Worker 基类
│       │   ├── record_selector.py                           # 记录筛选器
│       │   ├── confirmed_at_empty.py                        # 确认时间补全
│       │   ├── shipped_at_empty.py                          # 发货时间补全
│       │   ├── estimated_website_arrival_date_empty.py      # 预计到达补全
│       │   ├── tracking_number_empty.py                     # 追踪号补全
│       │   ├── japan_post_tracking_10_tracking_number.py    # 日本郵便批量查询
│       │   ├── temporary_flexible_capture.py                # 临时灵活抓取
│       │   └── celery_*.py / tasks_*.py                     # 各 Worker 的 Celery 任务定义
│       └── EmailParsing/        # 邮件解析
│           └── email_content_analysis.py                    # 邮件内容分析（提取配送日期等）
├── nextcloud_apps/
│   └── onlyoffice_callback_interceptor/  # OnlyOffice 回调拦截器
├── docker-compose.yml
├── Dockerfile
└── requirements.txt
```

**部署**: Docker 容器运行在主服务器上。

---

### 3.4 auto — 自动化脚本集

**用途**: 以系统服务形式运行的定期脚本集，执行价格抓取、数据翻译、加密价格解码等自动化任务。

**技术栈**:
- 语言: Python 3
- Web 自动化: Playwright (async)
- 数据处理: pandas
- HTTP 客户端: requests / httpx
- 运行方式: systemd 系统服务（定期执行）

**核心脚本**:
1. **wiki-price.py**: 从 iphonekaitori.tokyo 抓取 iPhone 买取价格，通过 API 同步到 ecsite
2. **translate 相关脚本**: 商品信息自动翻译
3. **价格解码脚本**: 处理加密的价格数据

**运行方式**: 通过 systemd timer 或 cron 定期执行，不依赖 n8n。

**项目结构**:
```
auto/
├── wiki-price.py         # 价格抓取主脚本
├── *.ipynb               # Jupyter Notebook 开发/调试用
├── requirements.txt      # Python 依赖 (pandas, playwright, requests)
└── ...
```

**部署**: Docker 容器运行在主服务器上。

---

### 3.5 desktopapp — iPhone 库存管理桌面应用

**用途**: 面向仓库操作人员的 Windows 桌面应用，通过条码扫描枪完成 Apple 设备入库操作，支持 iPhone、iPad、Apple Watch、Magic Keyboard 等产品。

**技术栈**:
- 语言: C++ (C++17)
- GUI 框架: Qt 6.4+ (Widgets, SvgWidgets, Sql, Multimedia, Network)
- 构建系统: CMake 3.16+
- 本地数据库: SQLite (WAL 模式)
- Excel 库: QXlsx（作为子目录嵌入）
- 编译器: MSVC (Visual Studio 2019/2022)
- 平台: Windows (主要), Linux (支持)

**核心功能**:

#### Tab 1: iPhone（三种并行操作模式）

1. **入荷登録（库存入库登记）**:
   - 扫描 JAN 码（13位）→ 自动查找商品名 → 扫描 IMEI（15位）→ 存入数据库
   - 每扫 10 件自动重置计数并播放提示音
   - 实时显示商品名称和颜色标识（彩色圆点）
   - LCD 计数器显示已扫数量

2. **検索（搜索查询）**:
   - 通过 JAN 码或 IMEI 搜索已有库存
   - 搜索结果在列表中高亮显示

3. **仮登録（临时登记）**:
   - 先将商品存入临时缓冲区，可批量确认入库
   - 实时 IMEI 重复检测（红色高亮警告）
   - 支持批量提交到正式数据库

#### Tab 2: 批量数据导入/导出

- 粘贴 V3/V4 格式批量数据（JAN+IMEI 配对，支持全角/半角逗号分隔）
- 单条手动输入
- Excel 导出当前会话数据
- 导出后自动调用 API 上传至 dataapp

**条码扫描枪快捷码**:

| 快捷码 | 功能 |
|--------|------|
| `2222222222222` | 跳转到搜索模式 |
| `5555555555555` | 跳转到入库登记模式 |
| `3333333333333` | 跳转到临时登记模式 |
| `1111111111111` | 重置计数器 |
| `4444444444444` | 批量刷入临时登记到数据库 |
| `7777777777777` | 导出 Excel |
| `8888888888888` | 打开最近导出的文件 |

**音效提示**:

| 音效文件 | 触发场景 |
|----------|----------|
| `success.wav` | 操作成功 |
| `jan_error.wav` | JAN 码格式错误 |
| `jan_not_found.wav` | JAN 未找到对应商品 |
| `imei_error.wav` | IMEI 格式错误 |
| `imei_duplicate.wav` | IMEI 重复 |
| `count_reset.wav` | 计数器重置 |

**本地数据库** (SQLite: `iphone_stock.sqlite`):

| 表名 | 用途 | 关键字段 |
|------|------|----------|
| `inbound` | 库存主表 | session_id, kind(入荷登録/仮登録/検索), code13(JAN), imei15(IMEI) |
| `entry_log` | 操作审计日志 | session_id, type, left_code(JAN), right_code(IMEI) |
| `catalog` | 商品主数据 | part_number, model_name, capacity_gb, color, jan, color_hex |

**会话管理**:
- 使用 `QSettings` 持久化 session_id（Windows 注册表: `HKCU\Software\Syu\iPhoneStockManagementSystem`）
- Session ID 格式: ISO 8601 时间戳 (`yyyyMMddHHmmsszzz`)
- 启动时弹窗询问: 继续上次会话 / 开始新会话
- 支持断点续录

**商品目录**:
- 内置 43+ 种产品型号（硬编码数组 + CSV 文件）:
  - iPhone 17 / 17 Pro / 17 Pro Max / Air（全容量全颜色）
  - iPad / iPad mini / iPad Air / iPad Pro
  - Magic Keyboard（多型号）
  - Apple Watch Series 11 / SE 3 / Ultra 3
- 每种产品关联 JAN 码、型号名、容量、颜色、颜色 HEX 值
- 查找优先级: 其他产品 JAN 映射表 → catalog 表（iPhone）

**API 集成** (与 dataapp 通信):
- **端点**: `https://data.yamaguchi.lan/api/aggregation/legal-person-offline/create-with-inventory/`
- **认证**: Bearer Token（硬编码在 `mainwindow.cpp` 中）
- **SSL**: 自定义 CA 证书 (`caddy-ca-bundle.crt`)，追加到系统证书存储
- **请求体 (JSON)**:
  ```json
  {
    "username": "操作员名",
    "visit_time": "ISO 8601 时间戳",
    "inventory_data": [
      { "jan": "4549995XXXXXX", "imei": "35XXXXXXXXXXXXX" }
    ],
    "inventory_times": {
      "checked_arrival_at_1": "ISO 8601 时间戳"
    },
    "batch_level_1": "批次一级",
    "batch_level_2": "批次二级",
    "batch_level_3": "session_id"
  }
  ```
- **触发时机**: Excel 导出完成后自动 POST（fire-and-forget，无响应处理）
- 对应 dataapp 后端: `LegalPersonOffline.create_with_inventory()` 方法

**Excel 导出格式**:
- **Sheet "Exported_Items"**: 汇总表 + 明细表
  - 汇总: 商品名、数量、单价、合计金额（含 Excel 公式）
  - 明细: 每台设备的 JAN、商品名、IMEI
  - 日期/签名栏
- **Sheet "ws3"**: CSV 风格详细导出（11+ 列）

**输入验证**:
- JAN 码: `^\d{0,13}$`（正好 13 位数字）
- IMEI: `^\d{0,15}$`（正好 15 位数字）
- 使用 `QRegularExpressionValidator` 进行按键过滤
- 输入框获取焦点时绿色边框，出错时红色边框

**DPI 适配**:
- 自动检测屏幕 DPI，按 `screenDPI / 96` 比例缩放图标和 SVG

**构建与部署**:
```powershell
# 在 Visual Studio Developer Command Prompt 中执行
cd C:\path\to\desktopapp
powershell .\deploy_windows.ps1 -QtPath "C:\Qt\6.5.0\msvc2019_64"
```
- 使用 `windeployqt` 自动打包依赖 DLL
- 输出: `build-windows\deploy\iPhoneStockManagement.exe`
- 打包: `iPhoneStockManagement_v0.1.0_Windows_x64.zip`

**安全注意事项**:
- Bearer Token 硬编码在源码中（`mainwindow.cpp` 第 1339 行），建议迁移到配置文件
- 无用户身份验证机制，username 字段由操作员手动填写
- API 调用为 fire-and-forget，网络异常时数据可能丢失

**项目结构**:
```
desktopapp/
├── CMakeLists.txt                  # CMake 构建配置
├── main.cpp                        # 应用入口
├── mainwindow.h                    # 主窗口类声明
├── mainwindow.cpp                  # 主窗口实现（约 3500 行）
├── Mainwindow.ui                   # Qt Designer UI 布局文件
├── QXlsx-master/                   # Excel 读写库（嵌入式）
├── pic/                            # SVG/PNG 图标资源
│   ├── app.png                     # 应用图标
│   ├── Stock_Registration.svg      # 入库登记按钮
│   ├── Temporary_Registration.svg  # 临时登记按钮
│   ├── Search.svg                  # 搜索按钮
│   ├── Excel_Output.svg            # Excel 导出按钮
│   ├── View_Summary.svg            # 查看汇总按钮
│   └── Reset.svg                   # 重置按钮
├── sounds/                         # WAV 音效文件（6 种提示音）
├── Apple_iPad_JAN_full_JP_*.csv              # iPad 产品 JAN 目录
├── Magic_Keyboard_SKUs_JAN_partial_*.csv     # Magic Keyboard JAN 目录
├── apple_watch_jp_sku_jan_*.csv              # Apple Watch JAN 目录
├── deploy_windows.ps1              # Windows 自动化部署脚本
├── build_windows.bat               # Windows 构建批处理（备选）
├── WINDOWS_BUILD.md                # Windows 编译说明
└── app.rc                          # Windows 资源文件（应用图标）
```

---

### 3.6 dedktoptools — PDF 批量重命名工具

**用途**: GUI 工具，根据 Excel 映射表批量重命名 PDF 文件（用于订单文件整理）。

**技术栈**:
- 前端: C++ / Qt 6.5+ (Widgets)
- 后端逻辑: Python 3.9+
- PDF 处理: pdfplumber
- Excel 处理: openpyxl
- 构建系统: CMake 3.21+

**工作流程**:
1. 选择包含 PDF 文件的文件夹
2. 选择 Excel 映射表（注文番号 → 变更名前）
3. 从每个 PDF 中提取注文番号（ご注文番号: Wxxxxxxxxxx）
4. 根据 Excel 映射表重命名 PDF 文件
5. 显示处理进度和成功/错误日志

**项目结构**:
```
dedktoptools/
├── CMakeLists.txt        # Qt 6 构建配置
├── src/
│   ├── main.cpp          # 应用入口
│   └── widget.h/cpp      # 主界面
├── ui/
│   └── Widget.ui         # UI 布局
├── scripts/
│   ├── rename_by_excel.py    # 核心 Python 脚本
│   ├── widget.py             # Python 备选界面
│   └── requirements.txt      # Python 依赖
└── .qtcreator/           # Qt Creator 项目文件
```

---

### 3.7 n8n-auto — n8n 集成自动化脚本

**用途**: 以 FastAPI 形式提供 HTTP 接口，配合 n8n 自动化平台进行价格同步操作。

**与 auto 的区别**: auto 以系统服务形式独立运行定期脚本；n8n-auto 以 FastAPI 服务形式运行，由 n8n 平台的 workflow 通过 HTTP 触发调用，两者并行使用，覆盖不同的自动化场景。

**技术栈**:
- 语言: Python 3
- Web 框架: FastAPI（推断）
- Web 自动化: Playwright (async)
- 数据处理: pandas
- HTTP 客户端: requests

**核心功能**:
- 从外部网站抓取 iPhone 价格数据
- 通过 ecsite API 更新商品价格
- 支持 iPhone Air 等新机型价格管理
- 价格折减规则自动应用（如 -1000 日元折扣）

**项目结构**:
```
n8n-auto/
└── wiki-price.py         # 价格同步脚本
```

**部署**: Docker 容器运行在主服务器上，与 n8n 平台配合。

---

### 3.8 dev — ELK 集中日志平台

**用途**: 基于 ELK Stack 的集中日志收集、处理和可视化平台，用于监控所有 Docker 容器的运行日志。

**技术栈**:
- Elasticsearch 8.12.0（日志存储与检索）
- Kibana 8.12.0（可视化界面）
- Logstash 8.12.0（日志处理管道）
- Filebeat 8.12.0（容器日志采集）
- Docker Compose v3.8

**核心功能**:
1. **日志采集**: Filebeat 自动收集 Docker 容器日志
2. **日志解析**:
   - Django/Daphne HTTP 日志解析（IP、Method、Path、Status）
   - Celery Worker 日志解析（Task ID、Level）
   - JSON 结构化日志自动解析
3. **容器标识**: container_id → container_name 映射
4. **日志保留**: 30天自动清理（ILM 策略）
5. **可视化**: Kibana Dashboard

**常用查询**:
- 容器日志: `container_name: "ypa_web"`
- HTTP 错误: `http_status >= 500`
- Celery 错误: `log_level: "ERROR"`

**访问端口**:
- Kibana: 5601
- Elasticsearch: 9200
- Logstash: 5044

**项目结构**:
```
dev/
├── docker-compose.yml           # ELK 编排
├── filebeat/
│   └── filebeat.yml             # 日志收集配置
├── logstash/
│   ├── pipeline/
│   │   └── logstash.conf        # 日志处理规则
│   └── data/
│       └── container-mapping.yml   # 容器名映射
└── cleanup-old-logs.sh          # 日志清理脚本
```

---

### 3.9 dashboard — 统一任务监控仪表盘

**用途**: 聚合 dataapp 和 webapp 的任务状态数据，提供实时可视化监控面板，覆盖 Nextcloud 同步、快递追踪、邮件处理、价格爬虫四大任务类型。

**技术栈**:
- 前端: Vue 3.5 (Composition API) + Vite 6.1 + Ant Design Vue 4.2 + Pinia 2.3
- 后端: Python 3.11 / FastAPI + httpx (async HTTP)
- 实时推送: Server-Sent Events (SSE)
- 容器化: Docker Compose（nginx 1.27 + Python 3.11-slim）
- 构建: Node 22 Alpine (多阶段构建)

**核心功能**:

1. **实时任务监控** — 五大数据区块:
   - **Nextcloud 数据同步** (`nextcloud_sync`): 各模型的 Excel ↔ DB 同步事件
   - **追踪任务 — Excel 驱动** (`excel_tracking`): Excel 文件触发的快递追踪批次
   - **追踪任务 — DB 驱动** (`db_tracking`): Worker 自动扫描触发的快递追踪批次
   - **邮件处理** (`email`): 邮件相关任务批次
   - **价格抓取 — Webapp** (`webapp_scraper`): 价格爬虫执行状态

2. **双视图模式**:
   - **甘特图 (Gantt)** — 桌面端默认: 时间轴横向展示，可折叠/展开任务组
   - **卡片 (Card)** — 移动端默认: 垂直卡片列表，可折叠/展开任务组
   - 通过 Segmented 控件手动切换

3. **状态统计面板**: 总数、运行中、成功、异常四项实时计数

4. **响应式设计**: 桌面侧边栏（可折叠）+ 移动端抽屉导航（768px 断点）

#### 后端架构 (FastAPI)

**数据缓存机制**:
- 内存缓存 `_cache`（sections + timestamp + stale 标志）
- `asyncio.Lock` 保护并发更新
- 后台循环每 `FETCH_INTERVAL_S` 秒刷新一次（默认 30 秒）
- 使用 `asyncio.gather()` 并行拉取四个上游 API

**上游 API 端点**:

| 数据源 | 端点 | 认证方式 |
|--------|------|----------|
| Nextcloud 同步 | `{DATAAPP_API_URL}/api/acquisition/dashboard/nextcloud-sync/?days={N}` | Bearer Token |
| 追踪批次 | `{DATAAPP_API_URL}/api/acquisition/dashboard/tracking-batches/?days={N}` | Bearer Token |
| 邮件任务 | `{DATAAPP_API_URL}/api/aggregation/dashboard/email-tasks/?days={N}` | Bearer Token |
| 价格爬虫 | `{WEBAPP_API_URL}/api/dashboard/scraper-events/?days={N}` | Token (DRF) |

**API 路由**:

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/health` | GET | 健康检查，返回 `{"status": "ok", "timestamp": "..."}` |
| `/api/tasks` | GET | 当前快照，返回 `{"timestamp", "sections", "stale"}` |
| `/api/tasks/stream` | GET | SSE 流，每 10 秒推送一次完整快照 |

**SSE 实现**:
```python
# 每 10 秒推送一次缓存快照
async def event_generator():
    while True:
        payload = json.dumps(_snapshot(), ensure_ascii=False)
        yield f"data: {payload}\n\n"
        await asyncio.sleep(10)

return StreamingResponse(
    event_generator(),
    media_type="text/event-stream",
    headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
)
```

**错误处理**:
- 单个 API 拉取失败时返回 `None`，不阻塞其他 API
- 任一 API 失败时设置 `stale = True`，前端可据此显示警告
- 后台循环异常时记录日志并继续（不会崩溃）
- 无重试逻辑，依赖下次刷新间隔自动恢复

#### 前端架构 (Vue 3)

**状态管理** (Pinia: `stores/tasks.js`):
```javascript
// 核心状态
sections = ref([])           // 后端返回的区块数组
connected = ref(false)       // SSE 连接状态
lastUpdated = ref(null)      // 最后更新时间戳

// SSE 连接
startStream() → new EventSource('/api/tasks/stream')
  onopen    → connected = true
  onmessage → 解析 JSON, 更新 sections/lastUpdated
  onerror   → connected = false (浏览器自动重连)
```

**数据模型**:

```
Section {
  id: string            // "nextcloud_sync", "webapp_scraper", "excel_tracking", "db_tracking", "email"
  label: string         // 中文显示名
  task_groups: [{
    id: string          // "SYNC_CONTACTS", "WEBAPP_AMAZON" 等
    label: string       // 任务组名称
    pipeline: string    // "nextcloud" | "webapp" | "excel" | "db" | "email"
    events?: [{         // Nextcloud/Webapp 类型
      id, status, timestamp, direction?, record_count?, conflict_count?,
      trigger?, rows_received?, rows_inserted?, rows_updated?, ...
    }]
    batches?: [{        // Tracking/Email 类型
      id, status, source, created_at, completed_at,
      total_jobs, completed_jobs, failed_jobs, detail
    }]
  }]
}
```

**Pipeline 颜色映射**:

| Pipeline | 颜色 | Ant Design Tag |
|----------|------|----------------|
| excel | 绿色 | `green` |
| db | 极客蓝 | `geekblue` |
| email | 紫色 | `purple` |
| nextcloud | 青色 | `cyan` |
| webapp | 橙色 | `orange` |

**状态颜色**:

| 状态 | 颜色 | 中文标签 |
|------|------|----------|
| running | `#1677ff` (蓝) | 运行中 |
| success | `#52c41a` (绿) | 成功 |
| error | `#ff4d4f` (红) | 异常 |
| pending | `#bfbfbf` (灰) | 等待中 |

**甘特图实现** (`TaskTimeline.vue`):
- 时间范围: 收集所有事件时间戳，前后各加 5% padding（最少 5 分钟）
- 运行中任务自动延伸未来 10 分钟
- 时间刻度: 桌面 5 个标记 / 移动 3 个标记（MM-DD HH:MM 格式）
- L1 层（任务组行）: 可折叠，显示缩略时间条（8px 高度）或事件标记
- L2 层（展开详情）: 进度条（宽度 = completed_jobs/total_jobs）或事件标记线
- 动画: 进度条宽度 500ms 渐变，展开/折叠 200ms，运行中脉冲 1.5s 循环
- 标签列: 桌面 240px / 移动 120px，图表区域弹性填充

**卡片视图实现** (`TaskCards.vue`):
- 每个区块以分隔线划分
- 每个任务组为可折叠卡片
- Nextcloud 事件行: 方向箭头（▼写入/▲写出）+ 触发方式 tag + 状态 badge + 记录数/冲突数
- Webapp 事件行: 状态 badge + 写入/更新/接收/未匹配统计
- Tracking 批次行: 来源 tag + 状态 badge + 进度条 + 详情
- 点击任意项弹出详情 Modal（含阶段时间线、统计表、错误信息等）

**响应式设计** (`useIsMobile.js`):
- 断点: 768px（监听 window resize 事件，组件卸载时清理）
- 桌面: 侧边栏 + 甘特图默认 + 5 个时间刻度 + 240px 标签列
- 移动: 抽屉导航 + 卡片默认 + 3 个时间刻度 + 120px 标签列 + Modal 宽度 92vw
- 统计面板: xs=12 sm=6（移动 2 列，桌面 4 列）

**环境变量**:

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `DATAAPP_API_URL` | dataapp 地址 | `http://localhost:8000` |
| `DATAAPP_SERVICE_TOKEN` | dataapp Bearer Token | — |
| `WEBAPP_API_URL` | webapp 地址 | `http://localhost:8001` |
| `WEBAPP_SERVICE_TOKEN` | webapp Token (DRF 格式) | — |
| `FETCH_INTERVAL_S` | 后台刷新间隔 | 30 秒 |
| `FETCH_TIMEOUT_S` | 单次请求超时 | 10 秒 |
| `TIME_WINDOW_DAYS` | 历史数据窗口 | 2 天 |

**访问端口**: 前端 3080 → nginx:80, 后端 8002 → uvicorn:8001

**Docker 部署**:
- **后端**: `python:3.11-slim` + uvicorn，健康检查 `/api/health`（15s 间隔, 3 次重试）
- **前端**: 多阶段构建 `node:22-alpine`(构建) → `nginx:1.27-alpine`(运行)
- **nginx 配置**: SPA 路由回退 + `/api/` 反向代理到后端，SSE 特殊配置（`proxy_buffering off`, `proxy_read_timeout 86400s`, `Connection ''`）
- **网络**: 独立 bridge 网络 `dashboard-net`，前端通过 Docker DNS 名 `backend` 访问后端

**安全注意事项**:
- CORS 配置为 `allow_origins=["*"]`，生产环境应限制域名
- 无用户级认证（假定为内网仪表盘）
- 前端不接触上游 Token，全部由后端代理注入

**项目结构**:
```
dashboard/
├── docker-compose.yml                # 双服务编排（backend + frontend）
├── backend/
│   ├── main.py                       # FastAPI 应用（约 300 行）
│   │                                 #   后台刷新循环、4 个 section builder、
│   │                                 #   SSE 流、缓存管理
│   ├── requirements.txt              # fastapi, uvicorn, httpx
│   └── Dockerfile                    # python:3.11-slim + uvicorn
└── frontend/
    ├── src/
    │   ├── main.js                   # Vue 3 入口（注册 Pinia/Router/AntD）
    │   ├── App.vue                   # 根布局（侧边栏 + 头部连接状态 + 路由出口）
    │   ├── router/
    │   │   └── index.js              # 单路由: / → DashboardView
    │   ├── stores/
    │   │   └── tasks.js              # Pinia 状态管理（SSE EventSource 连接）
    │   ├── views/
    │   │   └── DashboardView.vue     # 主视图（统计面板 + 视图切换 + Gantt/Card）
    │   ├── components/
    │   │   ├── TaskTimeline.vue      # 甘特图视图（时间轴 + 进度条 + 事件标记）
    │   │   └── TaskCards.vue         # 卡片视图（折叠列表 + 详情 Modal）
    │   └── composables/
    │       └── useIsMobile.js        # 响应式断点检测（768px）
    ├── index.html                    # HTML 入口（lang="ja"）
    ├── vite.config.js                # Vite 配置（开发代理 /api → :8001）
    ├── package.json                  # 依赖（vue, pinia, ant-design-vue, vue-router）
    ├── nginx.conf                    # 生产 nginx（SPA 回退 + API 代理 + SSE 配置）
    └── Dockerfile                    # 多阶段构建（node:22-alpine → nginx:1.27-alpine）
```

---

## 4. 部署架构

### 4.1 网络拓扑

```
                    ┌──────────────┐
                    │   Internet   │
                    └──────┬───────┘
                           │
                    ┌──────▼───────┐
                    │    Caddy     │  ◄── 所有 Web 项目的反向代理
                    │ (HTTPS 自动) │      自动签发 Let's Encrypt 证书
                    └──────┬───────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
    ┌─────────▼──┐  ┌──────▼────┐  ┌───▼──────────┐
    │  主服务器   │  │ Proxmox VM│  │ 树莓派       │
    │            │  │           │  │              │
    │ • dataapp  │  │ • webapp  │  │ • DNS 服务器  │
    │ • n8n      │  │           │  │              │
    │ • n8n-auto │  │           │  │              │
    │ • auto     │  │           │  │              │
    │ • ecsite   │  │           │  │              │
    │ • dev(ELK) │  │           │  │              │
    │ • dashboard│  │           │  │              │
    └────────────┘  └───────────┘  └──────────────┘
```

### 4.2 部署方式汇总

| 项目 | 部署位置 | 运行方式 | 端口 |
|------|----------|----------|------|
| ecsite | 主服务器 | Docker Compose | nginx → PHP-FPM |
| dataapp | 主服务器 | Docker Compose | Gunicorn / Daphne |
| auto | 主服务器 | Docker + systemd | 定时脚本 |
| n8n-auto | 主服务器 | Docker (FastAPI) | 配合 n8n |
| n8n | 主服务器 | Docker | n8n 平台 |
| dev (ELK) | 主服务器 | Docker Compose | 5601, 9200, 5044 |
| dashboard | 主服务器 | Docker Compose | 3080 (前端), 8002 (后端) |
| webapp | Proxmox VM | Docker Compose | Daphne |
| desktopapp | Windows 桌面 | 本地应用 | — |
| dedktoptools | Windows 桌面 | 本地应用 | — |

### 4.3 反向代理 (Caddy)

所有需要外部访问的 Web 项目均通过 Caddy 进行反向代理：
- Caddy 自动管理 HTTPS 证书（Let's Encrypt）
- 局域网内由树莓派提供 DNS 解析
- 各服务操作系统均为 Ubuntu Server

### 4.4 已停用组件

- **GitHub Actions**: 曾用于 CI/CD，目前已不再使用
- **ngrok**: 曾用于开发调试时的内网穿透，目前已不再使用

---

## 5. 技术栈汇总

### 5.1 后端技术

| 技术 | 使用项目 | 用途 |
|------|----------|------|
| Python 3.11+ | webapp, dataapp, auto, n8n-auto, dashboard | 主要后端语言 |
| Django 4.2+ | webapp, dataapp | Web 框架 |
| Django REST Framework | webapp, dataapp | API 开发 |
| FastAPI | dashboard, n8n-auto | 轻量 API 服务 |
| Celery + Redis | webapp, dataapp | 异步任务队列 |
| PyTorch | webapp | 向量化特征计算 (EMA/SMA/WMA/Bollinger) |
| statsmodels 0.14.4 | webapp | VAR 模型、Granger 因果检验 |
| CuPy (cuda13x) | webapp | GPU 加速（可选，自动回退 CPU） |
| PHP 8.0+ / ThinkPHP 6 | ecsite | 电商后端 |
| C++ (C++17) | desktopapp, dedktoptools | 桌面应用 |

### 5.2 前端技术

| 技术 | 使用项目 | 用途 |
|------|----------|------|
| Vue 3 + Vite | dashboard | 前端框架 |
| Ant Design Vue | dashboard | UI 组件库 |
| Qt 6 (Widgets) | desktopapp, dedktoptools | 桌面 GUI |
| ThinkPHP 模板 | ecsite | 服务端渲染 |
| Django 模板 + Chart.js | webapp | 数据可视化 |

### 5.3 数据库与存储

| 技术 | 使用项目 | 用途 |
|------|----------|------|
| PostgreSQL | webapp, dataapp | 主数据库 |
| ClickHouse | webapp | 分析数据仓库（统计指标、特征存储） |
| MySQL | ecsite | 电商数据库 |
| SQLite | desktopapp | 本地嵌入式数据库 |
| Redis | webapp, dataapp, ecsite | 缓存 / 消息队列 |
| Elasticsearch | dev | 日志存储与检索 |

### 5.4 基础设施

| 技术 | 用途 |
|------|------|
| Docker / Docker Compose | 容器化部署 |
| Caddy | 反向代理 + HTTPS 自动管理 |
| Proxmox | 虚拟机管理 |
| Filebeat + Logstash | 日志收集与处理 |
| Playwright | 浏览器自动化（爬虫） |
| Nextcloud (WebDAV) | 文件同步 |

---

## 6. 开发工作总结

### 6.1 主要开发成果（2024.09 ~ 2025.02）

以下根据代码库分析推断，具体时间节点请根据实际情况修正：

#### ecsite（电商网站）
- 基于购买的 FastAdmin + ThinkPHP 系统进行二次开发
- 添加商品价格 API 接口（list/update）
- 实现 Token 认证机制
- 适配二手 iPhone 买取业务流程
- Docker 化部署

#### webapp（价格监控与分析）
- 开发多源价格爬虫系统（Playwright）
- 实现 Celery 定时任务调度
- 构建 ClickHouse 分析数据仓库（price_aligned + features_wide）
- 开发 ETL 数据管道：读取 → 对齐 → 聚合 → 特征计算 → Cohort → ClickHouse
- 实现 PyTorch 向量化统计指标计算（32 个特征：EMA/SMA/WMA/Bollinger Bands × 3 时间窗口）
- 开发三阶段 AutoML 因果推断管道（预处理 → VAR 建模 → Granger 因果检验）
- 添加 CuPy GPU 加速支持（自动回退 CPU）
- 添加价格趋势分析与可视化（A/B/C 三线均线 + Chart.js）
- 开发 Dashboard API 端点

#### dataapp（数据整合平台）
- 设计并实现库存管理数据模型: Inventory（五状态流转）+ 四种来源（Purchasing / LegalPersonOffline / EcSite / TemporaryChannel）+ 三级批次分类
- 开发 `create_with_inventory` 工厂方法，支持 JAN 码/型号名自动匹配商品、IMEI 重复检测、支付卡自动关联
- 构建六阶段采购订单管道（confirmed_at → shipped_at → estimated_arrival → tracking_number → delivery_date → 完成）
- 开发 7 种快递追踪任务类型（ヤマト運輸 + 日本郵便），含自动重定向机制（ヤマト无数据时自动切换日本郵便）
- 实现 8 个自动化 Worker 定时扫描各阶段订单，通过 WebScraper API 补全缺失信息
- 开发追踪批次管理（TrackingBatch/TrackingJob），支持进度追踪和每 10 条自动回写 Excel
- 实现字段级冲突检测（OrderConflict），tracking_number / email 等关键字段变更时记录而非覆盖
- 构建 Nextcloud WebDAV 双向同步模块（Excel ↔ DB），含 ETag + 版本号冲突检测
- 开发 OnlyOffice 回调拦截器，实现 Nextcloud 文件保存事件驱动的数据同步
- 实现邮件自动处理（IMAP 监控、内容解析、配送日期提取）
- 开发库存 API（供 desktopapp 调用 create_with_inventory）
- 开发 Dashboard API 端点（Nextcloud / Tracking / Email 事件流）
- Celery Beat 多队列定时任务配置

#### auto（自动化脚本）
- 开发 wiki-price 价格抓取脚本
- 实现 Caddy Root CA 自签证书集成
- 配置 systemd 定时服务
- 开发翻译和价格解码脚本

#### desktopapp（库存管理桌面应用）
- 从零开发 C++ / Qt6 桌面应用
- 实现 JAN 码 + IMEI 扫码录入流程
- 开发实时重复检测与视觉反馈
- 实现会话制记录管理（断点续录）
- 集成 QXlsx Excel 导出功能
- 与 dataapp API 对接

#### dedktoptools（PDF 重命名工具）
- 开发 PDF 注文番号提取功能
- 实现 Excel 映射表批量重命名
- 构建 Qt6 GUI 界面

#### n8n-auto（n8n 自动化）
- 开发 FastAPI 接口供 n8n 调用
- 实现 iPhone Air 等新机型价格管理
- 配置价格折减规则

#### dev（ELK 日志平台）
- 搭建 ELK Stack 8.12.0
- 配置 Filebeat Docker 日志采集
- 开发 Logstash 日志解析规则（Django、Celery）
- 配置 30天日志保留策略
- 开发容器名映射和日志清理脚本

#### dashboard（任务监控仪表盘）
- 从零搭建 Vue 3 + FastAPI 项目
- 实现 SSE 实时数据推送
- 开发 Gantt 甘特图时间轴视图
- 开发 Card 卡片布局（移动端适配）
- 集成 dataapp + webapp 数据源
- Docker 化部署（nginx + Python）

### 6.2 仓库管理

本仓库采用 **git subtree** 方式管理多个子项目。每个子项目有独立的上游仓库，通过 subtree 合并到本 monorepo。

相关脚本：
- `pull-from-upstream.sh` — 从各子项目上游拉取更新
- `push-to-upstream.sh` — 将修改推送回子项目上游
- `subtrees.config` — subtree 配置文件

---

## 7. 已知问题与待办事项

根据代码分析发现的待处理事项：

1. **webapp → ecsite 价格同步**: 计划中但尚未实现，webapp 向 ecsite 的价格自动同步功能待开发
2. **GitHub Actions**: 已停用，如需恢复 CI/CD 需重新配置
3. **ELK 安全**: dev 环境的 Elasticsearch 安全功能已关闭（`xpack.security.enabled: false`），生产环境应启用
4. **n8n-auto 架构**: 当前仅一个脚本文件，如功能扩展建议规范化项目结构

---

## 8. 附录：仓库管理

### 8.1 Subtree 配置

各子项目对应的上游仓库和前缀均配置在 `subtrees.config` 文件中。

### 8.2 常用操作

```bash
# 从上游拉取某个子项目的更新
./pull-from-upstream.sh <project-name>

# 将本地修改推送回上游
./push-to-upstream.sh <project-name>
```

### 8.3 注意事项

- 由于使用 subtree，各子项目的 git 历史在本仓库中会以 squash 形式合并
- 修改子项目代码后，需通过 `push-to-upstream.sh` 同步回上游仓库
- git 2.39+ 存在 subtree dirname bug，已在脚本中做了 workaround

---

*本文档由代码分析自动生成，部分信息（如时间节点、业务细节）基于代码推断，请根据实际情况修正补充。*
