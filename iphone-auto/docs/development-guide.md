# iPhone Device Farm - 开发指南

## 项目概述

用一台 Mac 通过 USB 控制 5 台 iPhone 的设备农场系统。支持自定义脚本批量执行、任务队列自动分配、CLI 和 Web Dashboard 双界面。

## 技术栈

| 层级 | 技术 | 说明 |
|------|------|------|
| 后端框架 | FastAPI | 异步 REST API + WebSocket |
| 设备通信 | pymobiledevice3 | 纯 Python，无需 libimobiledevice |
| 数据库 | SQLite + SQLAlchemy | 异步 (aiosqlite) |
| CLI | Typer + Rich | 命令行工具 |
| 前端 | React + TypeScript + Vite | SPA Dashboard |
| 连接方式 | USB | 通过 USB Hub 连接 5 台设备 |

## 项目结构

```
backend/
├── app/
│   ├── main.py              # FastAPI 入口，lifespan 管理启停
│   ├── config.py             # 配置项，环境变量前缀 FARM_
│   ├── database.py           # 异步数据库会话
│   ├── models.py             # ORM 模型：Device, Task
│   ├── device/
│   │   ├── connection.py     # pymobiledevice3 封装（同步操作通过 run_in_executor 转异步）
│   │   └── manager.py        # 设备池管理，定时轮询 USB，维护设备状态
│   ├── task/
│   │   ├── engine.py         # 任务调度器：队列管理 + 自动分配空闲设备
│   │   └── runner.py         # 脚本加载器：动态导入用户脚本并执行
│   ├── api/
│   │   ├── devices.py        # GET /api/devices, /api/devices/{udid}/apps, /screenshot
│   │   ├── tasks.py          # GET/POST /api/tasks
│   │   └── ws.py             # WebSocket /ws 实时推送设备事件
│   └── cli/
│       └── main.py           # CLI 命令：devices, apps, run, tasks, serve
└── pyproject.toml

frontend/
├── src/
│   ├── api/client.ts         # fetch 封装 + WebSocket 连接
│   ├── pages/
│   │   ├── DevicesPage.tsx   # 设备卡片列表，WebSocket 实时刷新
│   │   └── TasksPage.tsx     # 任务列表 + 提交表单
│   └── App.tsx               # 路由
└── vite.config.ts            # 开发代理配置（/api → :8000）

scripts/                      # 用户自定义任务脚本目录
```

## 核心架构

### 设备生命周期

```
USB 连接 → DeviceManager 轮询检测 → 写入 DB (status=connected)
                                     ↓
                              WebSocket 通知前端
                                     ↓
         TaskEngine 发现空闲设备 ← 设备可用
                ↓
         分配队列中的任务 → status=busy
                ↓
         执行完成 → status=connected（重新可用）
```

### 任务调度流程

```
用户提交任务 (API/CLI)
    ↓
TaskEngine.submit_task() → 按 target_devices 拆分为多个 Task 记录 (status=queued)
    ↓
调度循环 (每秒) → 找到 queued 任务 + connected 设备 → 匹配分配
    ↓
TaskRunner.execute_task() → 加载 scripts/{script_name}.py → 调用 run(ctx, args)
    ↓
完成 → status=completed / failed
```

### 用户脚本规范

脚本放在 `scripts/` 目录，必须定义 `async run(ctx, args)` 函数：

```python
async def run(ctx, args):
    """
    ctx: DeviceContext 实例，提供以下方法：
        ctx.udid             - 当前设备 UDID
        ctx.install_app(ipa_path) - 安装 IPA
        ctx.uninstall_app(bundle_id) - 卸载 App
        ctx.list_apps()      - 获取已安装 App 列表
        ctx.screenshot()     - 截图，返回 PNG bytes

    args: dict，用户通过 CLI --args 或 Web 表单传入的 JSON 参数

    返回值: str，任务结果（存入 Task.result）
    """
    apps = await ctx.list_apps()
    return f"Found {len(apps)} apps"
```

## 开发环境搭建

```bash
# 后端
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# 启动后端服务
iphone-farm serve
# 或直接
uvicorn app.main:app --reload --port 8000

# 前端
cd frontend
npm install
npm run dev    # 开发模式，访问 http://localhost:3000
npm run build  # 生产构建到 dist/
```

## 配置项

通过环境变量配置，前缀 `FARM_`：

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `FARM_HOST` | 0.0.0.0 | 服务监听地址 |
| `FARM_PORT` | 8000 | 服务端口 |
| `FARM_DATABASE_URL` | sqlite+aiosqlite:///./device_farm.db | 数据库连接 |
| `FARM_DEVICE_POLL_INTERVAL` | 3.0 | 设备轮询间隔（秒） |
| `FARM_MAX_TASKS_PER_DEVICE` | 1 | 每设备最大并发任务数 |
| `FARM_SCRIPTS_DIR` | scripts | 脚本目录路径 |
| `FARM_TASK_RETENTION_DAYS` | 30 | 任务记录保留天数 |

## API 一览

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/health` | 健康检查 |
| GET | `/api/devices` | 设备列表 |
| GET | `/api/devices/{udid}` | 设备详情 |
| GET | `/api/devices/{udid}/apps` | 设备上的 App 列表 |
| GET | `/api/devices/{udid}/screenshot` | 截图 (返回 PNG) |
| POST | `/api/tasks` | 提交任务 |
| GET | `/api/tasks` | 任务列表 (?status=&limit=) |
| GET | `/api/tasks/{id}` | 任务详情 |
| WS | `/ws` | 实时事件推送 |

## CLI 命令

```bash
iphone-farm devices                    # 查看所有设备
iphone-farm apps <UDID>               # 查看设备上的 App
iphone-farm run <script>               # 对所有设备执行脚本
iphone-farm run <script> -t <UDID>    # 对指定设备执行
iphone-farm run <script> -a '{"k":"v"}'  # 传递参数
iphone-farm tasks                      # 查看任务列表
iphone-farm tasks -s running           # 按状态过滤
iphone-farm task <ID>                  # 查看任务详情
iphone-farm serve                      # 启动服务器
```

## 后续开发建议

### 优先级高

1. **扩展 DeviceContext API** - 添加更多设备操作：重启设备、推送/拉取文件、查看系统日志、获取电池信息等。pymobiledevice3 支持丰富的服务，按需封装即可。
2. **任务取消** - 在 API 和 CLI 中添加取消正在运行/排队任务的功能。TaskEngine 已预留 CancelledError 处理。
3. **脚本管理 API** - 添加上传、列表、删除脚本的 API，让 Web Dashboard 可以管理脚本而不只是提交任务。
4. **日志流** - 任务执行过程中的实时日志输出，通过 WebSocket 推送到前端。

### 优先级中

5. **任务重试** - 失败任务自动重试机制，可配置重试次数和间隔。
6. **设备分组/标签** - 支持给设备打标签（如 "测试组A"），任务可按标签选择目标设备。
7. **任务依赖链** - 支持 DAG 形式的任务编排，比如：安装 App → 运行测试 → 卸载。
8. **认证** - 为 API 和 Dashboard 添加简单的 token 认证。

### 优先级低

9. **数据库迁移** - 集成 Alembic 做 schema 迁移管理。
10. **Docker 化** - 提供 Dockerfile 和 docker-compose.yml（注意 USB 设备透传配置）。
11. **通知** - 任务完成/失败时发送通知（Slack、邮件等）。
12. **历史统计** - 任务成功率、设备利用率等统计面板。

## 关键设计决策记录

| 决策 | 理由 |
|------|------|
| pymobiledevice3 同步调用用 `run_in_executor` 包装 | pymobiledevice3 是同步库，用线程池避免阻塞事件循环 |
| DeviceManager 和 TaskEngine 用单例模式 | 全局唯一，lifespan 统一管理生命周期 |
| 任务按设备拆分为独立记录 | 便于追踪每台设备的执行状态和结果 |
| 用户脚本通过 `importlib` 动态加载 | 无需注册，放入 scripts/ 即可使用 |
| SQLite 而非 PostgreSQL | 5 台设备规模无需重型数据库，部署简单 |
| WebSocket 基于设备事件而非轮询 | 前端实时更新，减少无效请求 |
