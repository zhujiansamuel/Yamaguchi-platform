# Yamaguchi 统一任务仪表盘

整合各子系统（dataapp / ecsite / webapp）实时任务状态的 Vue 3 仪表盘。

---

## 技术栈

| 层次 | 技术 |
|------|------|
| 前端 | Vue 3 + Vite + Ant Design Vue 4 + Pinia + Vue Router |
| 后端 | FastAPI + Uvicorn |
| 实时推送 | Server-Sent Events（SSE） |
| 部署 | Docker Compose（nginx + FastAPI） |

---

## 目录结构

```
dashboard/
├── backend/
│   ├── main.py           # FastAPI 应用，含 SSE 端点
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── main.js
│   │   ├── App.vue       # 全局布局 + SSE 启动
│   │   ├── router/       # Vue Router
│   │   ├── stores/       # Pinia store（tasks.js）
│   │   ├── views/        # DashboardView.vue
│   │   └── components/   # TaskTimeline.vue
│   ├── index.html
│   ├── vite.config.js
│   ├── nginx.conf        # 生产用 nginx 配置
│   ├── Dockerfile        # 多阶段构建
│   └── package.json
└── docker-compose.yml
```

---

## 快速开始

### 方式一：Docker Compose（推荐，一键运行）

**前提条件：** Docker 20.10+ 和 Docker Compose v2

```bash
cd dashboard

# 构建并启动
docker compose up --build

# 后台运行
docker compose up --build -d
```

启动后访问：

| 地址 | 说明 |
|------|------|
| http://localhost:3000 | 仪表盘前端 |
| http://localhost:8001/api/health | 后端健康检查 |
| http://localhost:8001/api/tasks | 任务快照（JSON） |
| http://localhost:8001/api/tasks/stream | SSE 实时流 |

停止：

```bash
docker compose down
```

---

### 方式二：本地开发（前后端分离启动）

**前提条件：** Python 3.11+、Node.js 18+

**1. 启动后端**

```bash
cd dashboard/backend

# 创建虚拟环境（可选但推荐）
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate

pip install -r requirements.txt
uvicorn main:app --reload --port 8001
```

**2. 启动前端**

```bash
cd dashboard/frontend
npm install
npm run dev
```

访问 http://localhost:3000

> Vite 已配置 `/api` 代理到 `localhost:8001`，前后端无跨域问题。

---

## API 端点说明

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/health` | 健康检查，返回 `{"status":"ok"}` |
| GET | `/api/tasks` | 当前任务快照（JSON） |
| GET | `/api/tasks/stream` | SSE 流，每 5 秒推送一次 |

### SSE 数据格式

```json
{
  "timestamp": "2026-03-01T09:15:00.123456",
  "tasks": [
    {
      "id": "1",
      "source": "dataapp",
      "title": "数据同步 · Nextcloud WebDAV",
      "status": "running",
      "color": "blue",
      "started_at": "2026-03-01T09:00:00",
      "updated_at": "2026-03-01T09:15:00",
      "detail": "正在从 Nextcloud 拉取最新 Excel 文件"
    }
  ]
}
```

**status 枚举：** `running` / `success` / `error` / `pending`

---

## 接入真实数据

当前后端使用 `MOCK_TASKS` 硬编码数据。接入真实 API 时，修改 `backend/main.py` 中的 `_snapshot()` 函数：

```python
def _snapshot() -> dict:
    # TODO: 调用各子系统 API，聚合数据
    tasks = []
    tasks += fetch_dataapp_tasks()   # 调用 dataapp REST API
    tasks += fetch_ecsite_tasks()    # 调用 ecsite API
    tasks += fetch_webapp_tasks()    # 调用 webapp API
    return {
        "timestamp": datetime.datetime.now().isoformat(),
        "tasks": tasks,
    }
```

---

## 生产部署注意事项

1. **反向代理**：如果已有 Caddy/nginx 作为外层代理，将 `localhost:3000` 转发至该代理即可。
2. **SSE 缓冲**：nginx 配置已设置 `proxy_buffering off`，确保 SSE 实时性。
3. **CORS**：当前后端允许所有来源（`allow_origins=["*"]`），生产环境建议改为实际域名。
4. **端口冲突**：如 3000 或 8001 被占用，修改 `docker-compose.yml` 中的端口映射。

---

## 常见问题

**Q: 仪表盘显示"连接断开"**
A: 检查后端是否正常运行（访问 `http://localhost:8001/api/health`）。

**Q: Docker 构建时 npm install 超时**
A: 可在 `frontend/Dockerfile` 中添加 `RUN npm config set registry https://registry.npmmirror.com` 使用国内镜像。

**Q: 如何添加新的任务来源**
A: 在 `backend/main.py` 的 `MOCK_TASKS` 中添加条目，`source` 字段填写新系统名称；前端 `TaskTimeline.vue` 的 `sourceColor()` 函数中为新来源添加颜色映射。
