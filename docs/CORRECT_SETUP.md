# OnlyOffice Callback - 正确配置指南

## 🔧 环境特定配置

### Nextcloud Docker Compose 环境
- **位置**: `/opt/docker/nextcloud`
- **访问命令**: `docker compose exec app` (不是 `docker exec nextcloud-app`)
- **容器服务名**: `app`

### 监听文件夹
- **路径**: `/data_platform/` (不是 `/Data/`)

### Django URL
- **推荐使用容器名**: `http://data-platform-django:8000`
- **备选域名**: `http://data.yamaguchi.lan`

---

## 🚀 快速部署（3 步骤）

### 步骤 1: 部署应用

```bash
cd ~/Data-consolidation
./nextcloud_apps/deploy_app_correct.sh
```

### 步骤 2: 配置应用

```bash
cd ~/Data-consolidation
./nextcloud_apps/fix_config_correct.sh
```

这会自动：
- ✅ 设置路径过滤器为 `/data_platform/`
- ✅ 检测并配置 Django URL
- ✅ 启用所有必要的功能
- ✅ 测试健康检查

### 步骤 3: 验证状态

```bash
cd ~/Data-consolidation
./nextcloud_apps/check_status_correct.sh
```

---

## 📊 监控和测试

### 实时日志监控

```bash
cd ~/Data-consolidation
./nextcloud_apps/monitor_logs_correct.sh
```

### 手动检查配置

```bash
cd /opt/docker/nextcloud

# 查看所有配置
docker compose exec -u www-data app php occ config:list onlyoffice_callback_interceptor

# 查看特定配置
docker compose exec -u www-data app php occ config:app:get onlyoffice_callback_interceptor path_filter

# 查看应用状态
docker compose exec -u www-data app php occ app:list | grep onlyoffice
```

---

## 🎯 测试流程

1. **创建测试文件夹**
   - 在 Nextcloud 中创建 `/data_platform/` 文件夹
   - 注意：必须是 `/data_platform/`，不是 `/Data/`

2. **启动日志监控**
   ```bash
   ./nextcloud_apps/monitor_logs_correct.sh
   ```

3. **上传并打开 Excel 文件**
   - 上传文件到 `/data_platform/test.xlsx`
   - 用 OnlyOffice 打开

4. **预期日志**

   **打开文档时**：
   ```
   [NEXTCLOUD] OnlyOffice edit event detected: file_path=/data_platform/test.xlsx
   [NEXTCLOUD] Callback URL modified to: http://data-platform-django:8000/api/acquisition/onlyoffice/callback/
   ```

   **保存文档时**：
   ```
   [DJANGO] OnlyOffice callback received: status=2, file=/data_platform/test.xlsx
   [DJANGO] Forwarding callback to Nextcloud
   [DJANGO] Callback forwarded: status=200
   ```

---

## ⚙️ 手动配置命令

如果需要手动修改配置：

```bash
cd /opt/docker/nextcloud

# 设置路径过滤器
docker compose exec -u www-data app php occ config:app:set \
  onlyoffice_callback_interceptor path_filter --value="/data_platform/"

# 设置 Django URL（选择一个）
docker compose exec -u www-data app php occ config:app:set \
  onlyoffice_callback_interceptor django_callback_url \
  --value="http://data-platform-django:8000/api/acquisition/onlyoffice/callback/"

# 或使用域名
docker compose exec -u www-data app php occ config:app:set \
  onlyoffice_callback_interceptor django_callback_url \
  --value="http://data.yamaguchi.lan/api/acquisition/onlyoffice/callback/"

# 启用应用
docker compose exec -u www-data app php occ config:app:set \
  onlyoffice_callback_interceptor enabled --value="yes"

# 启用调试模式
docker compose exec -u www-data app php occ config:app:set \
  onlyoffice_callback_interceptor debug_mode --value="yes"
```

---

## 🔍 故障排查

### 问题 1: 应用未安装

```bash
cd ~/Data-consolidation
./nextcloud_apps/deploy_app_correct.sh
```

### 问题 2: Django 连接失败

```bash
cd /opt/docker/nextcloud

# 测试容器名
docker compose exec app curl http://data-platform-django:8000/api/acquisition/health/

# 测试域名
docker compose exec app curl http://data.yamaguchi.lan/api/acquisition/health/
```

### 问题 3: 路径过滤器错误

```bash
cd /opt/docker/nextcloud

# 检查当前值
docker compose exec -u www-data app php occ config:app:get \
  onlyoffice_callback_interceptor path_filter

# 应该返回: /data_platform/
# 如果不是，运行修复脚本
cd ~/Data-consolidation
./nextcloud_apps/fix_config_correct.sh
```

### 问题 4: 没有看到回调日志

检查清单：
- [ ] 文件在 `/data_platform/` 文件夹中（不是 `/Data/`）
- [ ] 应用已启用：`enabled=yes`
- [ ] Django 健康检查通过
- [ ] 调试模式已启用

---

## 📋 配置检查清单

运行状态检查：
```bash
./nextcloud_apps/check_status_correct.sh
```

应该看到：
- ✅ Nextcloud: Running
- ✅ Django: Running
- ✅ App: Installed
- ✅ Enabled: Yes
- ✅ Path Filter: /data_platform/
- ✅ Django Health Check: PASSED

---

## 🔗 重要 URL

- Nextcloud: http://cloud.yamaguchi.lan
- Django 健康检查: http://data.yamaguchi.lan/api/acquisition/health/
- Django 回调端点: http://data.yamaguchi.lan/api/acquisition/onlyoffice/callback/

---

## 📝 关键差异总结

| 项目 | 旧的/错误的 | 正确的 |
|------|------------|--------|
| 容器命令 | `docker exec nextcloud-app` | `cd /opt/docker/nextcloud && docker compose exec app` |
| 路径过滤器 | `/Data/` | `/data_platform/` |
| Django URL | 域名或容器名都可以 | 推荐用容器名 `http://data-platform-django:8000` |
| 脚本 | `deploy_nextcloud_app.sh` | `deploy_app_correct.sh` |
| 状态检查 | `check_status.sh` | `check_status_correct.sh` |
| 配置修复 | `fix_django_connectivity.sh` | `fix_config_correct.sh` |
| 日志监控 | `monitor_logs.sh` | `monitor_logs_correct.sh` |

---

## 🎯 下一步

1. 运行部署脚本
2. 运行配置脚本
3. 运行状态检查
4. 如果一切正常，开始测试

```bash
cd ~/Data-consolidation
./nextcloud_apps/deploy_app_correct.sh
./nextcloud_apps/fix_config_correct.sh
./nextcloud_apps/check_status_correct.sh
```

然后在 Nextcloud 中测试 `/data_platform/` 文件夹中的文档编辑！
