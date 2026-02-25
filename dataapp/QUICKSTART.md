# 快速部署指南

## 📝 部署前检查清单

- [ ] Docker >= 20.10 已安装
- [ ] Docker Compose >= 2.0 已安装
- [ ] Nextcloud 容器正在运行（nextcloud-app, nextcloud-web）
- [ ] Nextcloud 网络 `nextcloud_internal` 存在
- [ ] Caddy 已在宿主机上运行
- [ ] SSL 证书已准备（cert.pem, key.pem）

## 🚀 一键部署

### 步骤 1: 准备环境

```bash
cd /home/user/Data-consolidation

# 复制环境变量模板
cp .env.docker .env

# 编辑环境变量（必须修改所有密码和密钥！）
nano .env
```

**必须修改的配置项**：
```env
SECRET_KEY=                    # 生成: python -c "import secrets; print(secrets.token_urlsafe(50))"
DB_PASSWORD=                   # 强密码
REDIS_PASSWORD=                # 强密码
NEXTCLOUD_PASSWORD=            # 你的 Nextcloud admin 密码
NEXTCLOUD_WEBHOOK_TOKEN=       # 生成: python -c "import secrets; print(secrets.token_urlsafe(32))"
FLOWER_PASSWORD=               # Flower 监控密码
DJANGO_SUPERUSER_PASSWORD=     # Django admin 密码
```

### 步骤 2: 准备 SSL 证书

```bash
# 创建证书目录
mkdir -p docker/certs

# 复制你的证书文件
cp /path/to/your/cert.pem docker/certs/
cp /path/to/your/key.pem docker/certs/

# 验证证书文件
ls -la docker/certs/
```

### 步骤 3: 配置 Caddy（宿主机）

```bash
# 将 docker/Caddyfile.host 的内容添加到宿主机 Caddy 配置
sudo nano /etc/caddy/Caddyfile

# 测试配置
sudo caddy validate --config /etc/caddy/Caddyfile

# 重载 Caddy
sudo systemctl reload caddy
```

### 步骤 4: 部署服务

```bash
# 运行部署脚本
chmod +x deploy.sh
./deploy.sh

# 选择选项 1: Build and start all services
```

或者手动部署：

```bash
# 构建镜像
docker compose build

# 启动服务
docker compose up -d

# 查看日志
docker compose logs -f
```

### 步骤 5: 初始化数据库

```bash
# 创建超级用户（如果环境变量中没有设置）
docker compose exec django python manage.py createsuperuser

# 验证迁移
docker compose exec django python manage.py migrate --check
```

### 步骤 6: 验证部署

```bash
# 检查所有容器状态
docker compose ps

# 检查健康状态
curl -k https://data.yamaguchi.lan/api/schema/
curl -k https://flower.yamaguchi.lan/

# 查看日志
docker compose logs -f django
```

## 🔧 配置 Nextcloud Webhook

### 方法 1: 使用 Workflow 应用（推荐）

1. 在 Nextcloud 中安装 **Workflow** 应用
2. 进入 **Settings** → **Flow**
3. 添加新规则：

**When (触发条件)**:
- File created or updated

**And (过滤条件)**:
- File path matches: `/Data/*.xlsx`

**Then (动作)**:
- Send webhook
- URL: `http://data-platform-django:8000/api/acquisition/webhook/nextcloud/`
- Method: `POST`
- Headers:
  ```
  X-Nextcloud-Webhook-Token: <你在.env中设置的NEXTCLOUD_WEBHOOK_TOKEN>
  ```
- Body (JSON):
  ```json
  {
    "event": "file_changed",
    "file_path": "{file.path}",
    "user": "{user.displayName}",
    "timestamp": "{timestamp}"
  }
  ```

### 方法 2: 使用外部脚本

如果 Nextcloud Workflow 不可用，可以使用 inotify 监控文件变化：

```bash
# 在 Nextcloud 容器中安装 inotify-tools
docker exec -it nextcloud-app bash
apt-get update && apt-get install -y inotify-tools

# 创建监控脚本
cat > /monitor-excel.sh << 'EOF'
#!/bin/bash
inotifywait -m -r -e modify,create /var/www/html/data/admin/files/Data/*.xlsx |
while read path action file; do
    curl -X POST http://data-platform-django:8000/api/acquisition/webhook/nextcloud/ \
        -H "X-Nextcloud-Webhook-Token: YOUR_TOKEN" \
        -H "Content-Type: application/json" \
        -d "{\"event\":\"file_changed\",\"file_path\":\"/Data/$file\",\"user\":\"system\",\"timestamp\":\"$(date -Iseconds)\"}"
done
EOF

chmod +x /monitor-excel.sh
./monitor-excel.sh &
EOF
```

## 📊 访问服务

| 服务 | URL | 认证 |
|-----|-----|------|
| Django Admin | https://data.yamaguchi.lan/admin/ | Django 超级用户 |
| API 文档 | https://data.yamaguchi.lan/api/docs/ | 无需认证 |
| Flower 监控 | https://flower.yamaguchi.lan/ | Basic Auth (FLOWER_USER/FLOWER_PASSWORD) |

## 🧪 测试 Webhook

### 1. 准备测试 Excel 文件

创建测试文件 `/Data/Purchasing_test001.xlsx`：

| __id | __version | __op | amount | description |
|------|-----------|------|--------|-------------|
|      |           | add  | 100.50 | Test item 1 |
|      |           | add  | 200.75 | Test item 2 |

### 2. 手动触发 Webhook

```bash
# 获取文件 etag
docker compose exec django python manage.py shell
>>> from apps.data_acquisition.webdav_client import NextcloudWebDAVClient
>>> client = NextcloudWebDAVClient()
>>> info = client.get_file_info('/Data/Purchasing_test001.xlsx')
>>> print(info)

# 手动触发同步
curl -X POST http://localhost:8000/api/acquisition/webhook/nextcloud/ \
  -H "X-Nextcloud-Webhook-Token: YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "event": "file_changed",
    "file_path": "/Data/Purchasing_test001.xlsx",
    "user": "admin",
    "timestamp": "2024-01-01T00:00:00Z"
  }'
```

### 3. 检查同步结果

```bash
# 查看 Celery 任务日志
docker compose logs -f celery_worker_acquisition

# 查看数据库
docker compose exec django python manage.py shell
>>> from apps.data_acquisition.models import Purchasing, NextcloudSyncState
>>> Purchasing.objects.all()
>>> NextcloudSyncState.objects.filter(file_path__contains='Purchasing')

# 查看 Flower 监控
# 访问 https://flower.yamaguchi.lan/
```

## 🔍 故障排查

### 问题 1: 容器无法启动

```bash
# 查看具体错误
docker compose logs <service_name>

# 检查端口占用
sudo netstat -tulpn | grep -E '8000|5555'

# 检查网络
docker network ls
docker network inspect nextcloud_internal
```

### 问题 2: 无法连接 Nextcloud

```bash
# 测试网络连通性
docker compose exec django ping nextcloud-app

# 测试 WebDAV
docker compose exec django curl -u admin:password http://nextcloud-app/remote.php/dav/

# 检查环境变量
docker compose exec django env | grep NEXTCLOUD
```

### 问题 3: Webhook 认证失败

```bash
# 检查 token 配置
docker compose exec django env | grep WEBHOOK_TOKEN

# 查看 Django 日志
docker compose logs -f django | grep webhook
```

### 问题 4: Celery 任务不执行

```bash
# 检查 worker 状态
docker compose exec django celery -A config.celery inspect ping

# 检查队列
docker compose exec django celery -A config.celery inspect active

# 重启 workers
docker compose restart celery_worker_acquisition celery_worker_aggregation
```

## 📈 监控和维护

### 日常监控

```bash
# 查看所有服务状态
docker compose ps

# 查看资源使用
docker stats

# 查看日志
docker compose logs -f --tail=100
```

### 定期维护

```bash
# 数据库备份
docker compose exec postgres pg_dump -U postgres data_platform > backup_$(date +%Y%m%d).sql

# 清理旧日志
docker compose logs --no-log-prefix django > /dev/null

# 更新镜像
docker compose pull
docker compose up -d
```

## 🎯 下一步

- [ ] 配置定时任务（Celery Beat）
- [ ] 设置监控告警
- [ ] 配置日志轮转
- [ ] 设置自动备份
- [ ] 优化性能参数

## 📚 相关文档

- [完整部署文档](DOCKER_DEPLOYMENT.md)
- [Nextcloud 同步说明](NEXTCLOUD_SYNC_README.md)
- [API 文档](https://data.yamaguchi.lan/api/docs/)
