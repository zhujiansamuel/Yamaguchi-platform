# Docker 部署指南

## 📋 服务架构

本项目使用 Docker Compose 部署以下服务：

```
┌─────────────────────────────────────────────────────────────┐
│                    Caddy (Reverse Proxy)                     │
│            data.yamaguchi.lan (HTTPS/SSL)                    │
│          flower.yamaguchi.lan (Celery Monitor)               │
└──────────────────────┬──────────────────────────────────────┘
                       │
    ┌──────────────────┼──────────────────┐
    │                  │                  │
┌───▼────┐      ┌─────▼─────┐     ┌─────▼──────┐
│ Django │      │  Flower   │     │   Static   │
│  App   │      │(Port 5555)│     │   Files    │
└───┬────┘      └───────────┘     └────────────┘
    │
    │  ┌──────────────┬──────────────┬──────────────┐
    │  │              │              │              │
┌───▼──▼───┐  ┌──────▼──────┐  ┌───▼──────┐  ┌───▼──────┐
│PostgreSQL│  │Celery Worker│  │  Celery  │  │  Redis   │
│   DB     │  │Acquisition  │  │   Beat   │  │  Cache   │
└──────────┘  │& Aggregation│  └──────────┘  └──────────┘
              └──────┬──────┘
                     │
              ┌──────▼───────┐
              │  Nextcloud   │
              │  (External)  │
              └──────────────┘
```

## 🚀 快速开始

### 1. 前置要求

- Docker >= 20.10
- Docker Compose >= 2.0
- 已有 Nextcloud 容器运行（容器名：nextcloud-app，网络：nextcloud_internal）

### 2. 克隆并配置

```bash
cd /home/user/Data-consolidation

# 复制环境变量模板
cp .env.docker .env

# 编辑环境变量
nano .env
```

**必须修改的配置项**：
- `SECRET_KEY` - Django 密钥
- `DB_PASSWORD` - PostgreSQL 密码
- `REDIS_PASSWORD` - Redis 密码
- `NEXTCLOUD_PASSWORD` - Nextcloud admin 密码
- `NEXTCLOUD_WEBHOOK_TOKEN` - Webhook 认证 token
- `FLOWER_PASSWORD` - Flower 监控密码

**生成随机密钥**：
```bash
# Django SECRET_KEY
python -c "import secrets; print(secrets.token_urlsafe(50))"

# Webhook Token
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 3. 准备 SSL 证书

由于你使用自己的根证书，将证书文件放置在 `docker/certs/` 目录：

```bash
mkdir -p docker/certs
# 复制你的证书文件
cp /path/to/your/cert.pem docker/certs/
cp /path/to/your/key.pem docker/certs/
```

**证书文件要求**：
- `cert.pem` - SSL 证书（包含完整证书链）
- `key.pem` - 私钥文件

### 4. 配置宿主机 Caddy

由于 Caddy 直接运行在宿主机上（不在容器中），需要将 `docker/Caddyfile.host` 的内容添加到宿主机的 Caddy 配置：

```bash
# 编辑宿主机 Caddy 配置
sudo nano /etc/caddy/Caddyfile

# 将 docker/Caddyfile.host 的内容添加到文件中

# 验证配置
sudo caddy validate --config /etc/caddy/Caddyfile

# 重载 Caddy
sudo systemctl reload caddy

# 检查 Caddy 状态
sudo systemctl status caddy
```

**重要说明**：
- Django 和 Flower 容器只暴露到 `127.0.0.1:8000` 和 `127.0.0.1:5555`
- Caddy 从宿主机反向代理到这些端口
- 静态文件直接从宿主机路径 `/home/user/Data-consolidation/staticfiles` 和 `media` 提供

### 5. 构建和启动

```bash
# 构建镜像
docker compose build

# 启动所有服务
docker compose up -d

# 查看日志
docker compose logs -f
```

### 6. 初始化数据库

```bash
# 运行迁移（entrypoint.sh 会自动执行，这里是手动验证）
docker compose exec django python manage.py migrate

# 创建超级用户
docker compose exec django python manage.py createsuperuser

# 收集静态文件（entrypoint.sh 会自动执行）
docker compose exec django python manage.py collectstatic --noinput
```

### 7. 验证部署

```bash
# 检查所有容器状态
docker compose ps

# 应该看到以下容器都在运行：
# - data-platform-postgres
# - data-platform-redis
# - data-platform-django
# - data-platform-celery-acquisition
# - data-platform-celery-aggregation
# - data-platform-celery-beat
# - data-platform-flower
# - data-platform-caddy
```

**访问测试**：
- Django Admin: https://data.yamaguchi.lan/admin/
- API Docs: https://data.yamaguchi.lan/api/docs/
- Flower: https://flower.yamaguchi.lan/

## 📦 服务详情

### PostgreSQL
- **容器名**: data-platform-postgres
- **端口**: 5432 (内部)
- **数据卷**: postgres_data
- **健康检查**: `pg_isready`

### Redis
- **容器名**: data-platform-redis
- **端口**: 6379 (内部)
- **数据卷**: redis_data
- **持久化**: AOF 模式

### Django
- **容器名**: data-platform-django
- **端口**: 8000 (内部)
- **Workers**: 4个 Gunicorn workers
- **Threads**: 每个 worker 2个线程
- **超时**: 120秒

### Celery Workers

**Acquisition Worker**:
- **容器名**: data-platform-celery-acquisition
- **队列**: acquisition_queue
- **并发**: 4
- **用途**: 处理 Nextcloud 文件同步任务

**Aggregation Worker**:
- **容器名**: data-platform-celery-aggregation
- **队列**: aggregation_queue
- **并发**: 4
- **用途**: 处理数据聚合任务

### Celery Beat
- **容器名**: data-platform-celery-beat
- **用途**: 定时任务调度器
- **调度器**: Django Celery Beat (数据库存储)

### Flower
- **容器名**: data-platform-flower
- **端口**: 5555 (内部)
- **认证**: Basic Auth (FLOWER_USER/FLOWER_PASSWORD)
- **访问**: https://flower.yamaguchi.lan/

### Caddy
- **容器名**: data-platform-caddy
- **端口**: 80, 443 (HTTP/HTTPS)
- **功能**:
  - 反向代理
  - SSL 终端
  - 静态文件服务
  - Gzip 压缩
  - 安全头设置

## 🔧 常用命令

### 容器管理

```bash
# 启动所有服务
docker compose up -d

# 停止所有服务
docker compose down

# 重启特定服务
docker compose restart django
docker compose restart celery_worker_acquisition

# 查看日志
docker compose logs -f django
docker compose logs -f celery_worker_acquisition

# 进入容器 shell
docker compose exec django bash
docker compose exec postgres psql -U postgres data_platform
```

### Django 管理

```bash
# 运行 Django 命令
docker compose exec django python manage.py <command>

# 创建迁移
docker compose exec django python manage.py makemigrations

# 运行迁移
docker compose exec django python manage.py migrate

# Django shell
docker compose exec django python manage.py shell

# 创建超级用户
docker compose exec django python manage.py createsuperuser
```

### 数据库操作

```bash
# 进入 PostgreSQL
docker compose exec postgres psql -U postgres data_platform

# 备份数据库
docker compose exec postgres pg_dump -U postgres data_platform > backup_$(date +%Y%m%d).sql

# 恢复数据库
docker compose exec -T postgres psql -U postgres data_platform < backup.sql
```

### Celery 操作

```bash
# 查看 Celery worker 状态
docker compose exec celery_worker_acquisition celery -A apps.data_acquisition.celery inspect active

# 查看队列任务
docker compose exec celery_worker_acquisition celery -A apps.data_acquisition.celery inspect reserved

# 清空队列
docker compose exec django celery -A config.celery purge

# 重启 workers
docker compose restart celery_worker_acquisition celery_worker_aggregation
```

## 🔍 监控和调试

### 日志查看

```bash
# 所有服务日志
docker compose logs -f

# 特定服务日志
docker compose logs -f django
docker compose logs -f celery_worker_acquisition

# 最近 100 行日志
docker compose logs --tail=100 django
```

### Flower 监控

访问 https://flower.yamaguchi.lan/ 查看：
- 实时任务执行情况
- Worker 状态和统计
- 任务历史记录
- 队列深度

### 健康检查

```bash
# 检查容器健康状态
docker compose ps

# Django 健康检查
curl -f https://data.yamaguchi.lan/api/schema/

# Celery worker 检查
docker compose exec django celery -A config.celery inspect ping
```

## 🔐 安全配置

### 1. 生产环境最佳实践

**环境变量**：
```env
DEBUG=False
SECRET_KEY=<strong-random-key>
ALLOWED_HOSTS=data.yamaguchi.lan
```

**数据库**：
- 使用强密码
- 限制数据库连接来源
- 定期备份

**Redis**：
- 启用密码认证
- 不暴露到公网

### 2. SSL/TLS 配置

Caddy 配置文件位于 `docker/Caddyfile`，已配置：
- TLS 1.2+
- HSTS
- 安全头（X-Frame-Options, CSP 等）

### 3. 网络隔离

- `data_platform_internal`: 内部服务通信
- `nextcloud_internal`: 连接 Nextcloud（外部网络）

只有 Caddy 暴露端口到宿主机。

## 📊 性能调优

### Gunicorn 配置

编辑 `docker/entrypoint.sh` 中的 Gunicorn 参数：

```bash
--workers 4              # CPU 核心数 * 2 + 1
--threads 2              # 每个 worker 的线程数
--timeout 120            # 请求超时时间
--max-requests 1000      # worker 处理请求后重启
```

### Celery 并发

在 `docker-compose.yml` 中调整：

```yaml
celery_worker_acquisition:
  command: celery_worker_acquisition
  # 在 entrypoint.sh 中修改 --concurrency=4
```

### PostgreSQL 调优

创建 `docker/postgres.conf`：

```ini
shared_buffers = 256MB
effective_cache_size = 1GB
maintenance_work_mem = 64MB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100
random_page_cost = 1.1
```

## 🔄 更新和维护

### 更新代码

```bash
# 拉取最新代码
git pull

# 重新构建镜像
docker compose build django

# 重启服务
docker compose up -d

# 运行迁移
docker compose exec django python manage.py migrate
```

### 清理

```bash
# 清理未使用的镜像
docker image prune -a

# 清理未使用的卷
docker volume prune

# 完全清理（谨慎！会删除数据）
docker compose down -v
```

## 🐛 故障排查

### 问题 1: 容器无法启动

**检查**：
```bash
docker compose logs <container_name>
```

**常见原因**：
- 端口冲突
- 环境变量未设置
- 依赖服务未就绪

### 问题 2: 无法连接 Nextcloud

**检查**：
```bash
# 验证网络连接
docker compose exec django ping nextcloud-app

# 测试 WebDAV
docker compose exec django curl -u admin:password http://nextcloud-app/remote.php/dav/
```

**解决**：
- 确认 Nextcloud 容器在运行
- 检查 `nextcloud_internal` 网络配置
- 验证 WebDAV URL 格式

### 问题 3: Celery 任务不执行

**检查**：
```bash
# Worker 状态
docker compose exec django celery -A config.celery inspect ping

# 队列状态
docker compose exec django celery -A config.celery inspect active
```

**解决**：
- 重启 Celery workers
- 检查 Redis 连接
- 查看 Flower 监控面板

### 问题 4: SSL 证书错误

**检查**：
```bash
# 验证证书文件
ls -la docker/certs/

# 测试 HTTPS
curl -k https://data.yamaguchi.lan/
```

**解决**：
- 确认证书文件存在且权限正确
- 检查证书有效期
- 验证 Caddyfile 中的 tls 配置

## 📞 配置 Nextcloud Webhook

在 Nextcloud 中配置 Webhook（需要 Workflow 应用）：

1. 进入 **Settings** → **Flow**
2. 添加新规则：
   - **When**: File created or updated
   - **and**: File path matches `/Data/*.xlsx`
   - **then**: Send webhook
     - URL: `http://data-platform-django:8000/api/acquisition/webhook/nextcloud/`
     - Method: POST
     - Headers: `X-Nextcloud-Webhook-Token: <your-token>`
     - Body:
       ```json
       {
         "event": "file_changed",
         "file_path": "{file.path}",
         "user": "{user.displayName}",
         "timestamp": "{timestamp}"
       }
       ```

**注意**: 使用容器名 `data-platform-django` 而不是域名，因为它们在同一 Docker 网络中。

## 🎯 下一步

1. ✅ 配置环境变量
2. ✅ 准备 SSL 证书
3. ✅ 启动服务
4. ✅ 创建超级用户
5. ✅ 配置 Nextcloud Webhook
6. ✅ 测试文件同步
7. ✅ 设置监控告警
8. ✅ 配置定期备份

## 📚 相关文档

- [Nextcloud 同步说明](NEXTCLOUD_SYNC_README.md)
- [API 文档](https://data.yamaguchi.lan/api/docs/)
- [Django 文档](https://docs.djangoproject.com/)
- [Celery 文档](https://docs.celeryq.dev/)
- [Caddy 文档](https://caddyserver.com/docs/)
