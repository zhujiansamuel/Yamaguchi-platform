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

**用途**: 从多个竞品网站抓取 iPhone 买取价格数据，进行分析对比，辅助定价决策。

**技术栈**:
- 后端: Python 3.11+ / Django 4.2+ / Django REST Framework
- 异步任务: Celery + Redis
- 数据库: PostgreSQL
- 前端: Django 模板 + Chart.js（价格趋势图）
- 浏览器自动化: Playwright（爬虫使用）
- 容器化: Docker Compose
- Web 服务器: Daphne (ASGI)

**核心功能**:
1. **价格爬虫**: 定时抓取竞品网站的 iPhone 买取价格
2. **价格分析**: 生成价格趋势图表、对比分析
3. **Dashboard API**: 向 dashboard 系统提供爬虫任务状态接口
   - `GET /api/dashboard/scraper-events/` — 爬虫事件流

**项目结构**:
```
webapp/
├── scraper/              # 爬虫模块
│   ├── tasks.py          # Celery 定时任务
│   ├── scrapers/         # 各网站爬虫实现
│   └── models.py         # 数据模型
├── analysis/             # 分析模块
├── dashboard_api/        # Dashboard 接口
├── config/               # Django 项目配置
├── docker-compose.yml    # 容器编排
├── Dockerfile            # 应用容器
└── requirements.txt      # Python 依赖
```

**部署**: 独立部署在 Proxmox 虚拟机中。

---

### 3.3 dataapp — 数据整合平台

**用途**: 平台的数据中枢，负责从多个数据源采集、整合、分发数据。

**技术栈**:
- 后端: Python 3.11+ / Django 4.2+ / Django REST Framework
- 异步任务: Celery + Redis + Celery Beat
- 数据库: PostgreSQL
- 文件同步: Nextcloud WebDAV
- 邮件处理: IMAP
- 容器化: Docker Compose
- Web 服务器: Gunicorn / Daphne

**核心功能**:
1. **Nextcloud 数据同步**: 从 Nextcloud 服务器同步业务文件（Excel 等）
2. **Tracking 批次管理**: 管理快递追踪批次数据，支持批量导入
3. **邮件任务处理**: 自动处理业务邮件
4. **商品价格管理**: 维护 iPhone 各机型的买取价格数据
5. **库存 API**: 为 desktopapp 提供库存登录接口
6. **Dashboard API**: 向 dashboard 系统提供各任务状态接口
   - `GET /api/dashboard/nextcloud-events/` — Nextcloud 同步事件
   - `GET /api/dashboard/tracking-batches/` — Tracking 批次事件
   - `GET /api/dashboard/email-events/` — 邮件处理事件

**项目结构**:
```
dataapp/
├── inventory/            # 库存管理模块
├── tracking/             # 快递追踪模块
├── pricing/              # 价格管理模块
├── sync/                 # 数据同步模块 (Nextcloud)
├── email_tasks/          # 邮件处理模块
├── dashboard_api/        # Dashboard 接口
├── config/               # Django 项目配置
├── docker-compose.yml    # 容器编排
├── Dockerfile            # 应用容器
└── requirements.txt      # Python 依赖
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

**用途**: 面向仓库操作人员的 Windows 桌面应用，通过扫描条码完成 iPhone 入库操作。

**技术栈**:
- 语言: C++ (C++17)
- GUI 框架: Qt 6 (Widgets, SvgWidgets)
- 构建系统: CMake 3.16+
- 本地数据库: SQLite
- Excel 库: QXlsx（嵌入式）
- 编译器: MSVC (Visual Studio 2019/2022)
- 平台: Windows

**核心功能**:
1. **iPhone 入库管理** (Tab 1):
   - JAN 码（13位）和 IMEI（15位）扫码录入
   - 实时重复检测（红色高亮提示）
   - 会话制记录管理（支持断点续录）
   - Excel 导出
2. **批量数据导入** (Tab 2):
   - 支持 V3/V4 格式解析
   - 批量导入历史数据
3. **会话管理** (Tab 3):
   - 会话历史记录
   - 会话恢复与回溯

**通信**: 通过 REST API 与 dataapp 通信，实现库存数据的上传和查询。

**项目结构**:
```
desktopapp/
├── CMakeLists.txt        # CMake 构建配置
├── main.cpp              # 入口
├── mainwindow.h/cpp      # 主窗口逻辑
├── Mainwindow.ui         # UI 布局 (Qt Designer)
├── QXlsx-master/         # Excel 库（嵌入）
├── pic/                  # SVG/PNG 图标资源
├── sounds/               # WAV 音效（成功/错误提示音）
├── deploy_windows.ps1    # Windows 部署脚本
└── WINDOWS_BUILD.md      # Windows 编译说明
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

**用途**: 聚合 dataapp 和 webapp 的任务状态数据，提供实时可视化监控面板。

**技术栈**:
- 前端: Vue 3 (Composition API) + Vite 6.1 + Ant Design Vue 4.2 + Pinia
- 后端: Python FastAPI + httpx
- 实时推送: Server-Sent Events (SSE)
- 容器化: Docker Compose（nginx + Python）

**核心功能**:
1. **实时任务监控**:
   - Nextcloud 数据同步状态
   - Tracking 批次处理状态
   - Email 任务处理状态
   - Webapp 价格爬虫状态
2. **双视图模式**:
   - Gantt 图（甘特图时间轴）— 桌面端
   - Card 卡片布局 — 移动端
3. **状态统计**: 总数、运行中、成功、错误计数
4. **响应式设计**: 桌面侧边栏 + 移动端抽屉导航

**数据源**:
- dataapp API:
  - `/api/dashboard/nextcloud-events/`
  - `/api/dashboard/tracking-batches/`
  - `/api/dashboard/email-events/`
- webapp API:
  - `/api/dashboard/scraper-events/`

**环境变量**:
| 变量 | 说明 | 默认值 |
|------|------|--------|
| `DATAAPP_API_URL` | dataapp 地址 | — |
| `DATAAPP_SERVICE_TOKEN` | 认证 Token | — |
| `WEBAPP_API_URL` | webapp 地址 | — |
| `FETCH_INTERVAL_S` | 轮询间隔 | 30s |
| `TIME_WINDOW_DAYS` | 历史时间窗口 | 2天 |

**访问端口**: 前端 3080 → nginx 80, 后端 8002 → 8001

**项目结构**:
```
dashboard/
├── docker-compose.yml
├── backend/
│   ├── main.py            # FastAPI 应用
│   ├── requirements.txt
│   └── Dockerfile
└── frontend/
    ├── src/
    │   ├── App.vue         # 根组件
    │   ├── views/
    │   │   └── DashboardView.vue
    │   ├── components/
    │   │   ├── TaskTimeline.vue    # Gantt 视图
    │   │   └── TaskCards.vue       # Card 视图
    │   ├── stores/
    │   │   └── tasks.js           # Pinia 状态管理 (SSE)
    │   └── composables/
    │       └── useIsMobile.js     # 移动端检测
    ├── package.json
    ├── nginx.conf
    └── Dockerfile
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

#### webapp（价格监控）
- 开发多源价格爬虫系统（Playwright）
- 实现 Celery 定时任务调度
- 添加价格趋势分析与可视化（Chart.js）
- 开发 Dashboard API 端点

#### dataapp（数据整合平台）
- 构建 Nextcloud WebDAV 数据同步模块
- 开发 Tracking 批次管理功能
- 实现邮件自动处理（IMAP）
- 开发库存 API（供 desktopapp 使用）
- 开发 Dashboard API 端点
- Celery Beat 定时任务配置

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
