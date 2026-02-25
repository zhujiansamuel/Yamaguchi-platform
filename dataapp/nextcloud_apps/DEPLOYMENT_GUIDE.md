# OnlyOffice Callback Interceptor - 部署指南

## 📦 插件包信息

- **版本**: 1.0.0
- **文件**: `onlyoffice_callback_interceptor_v1.0.0.tar.gz` (45KB)
- **位置**: `/home/user/Data-consolidation/nextcloud_apps/`
- **包含内容**:
  - ✅ 所有后端代码（lib/）
  - ✅ Composer 依赖（vendor/ 包含 firebase/php-jwt）
  - ✅ 前端文件（js/, css/, templates/）
  - ✅ 配置文件（appinfo/, composer.json）

## 🚀 部署选项

### 选项 A：从 Git 部署（推荐）

**适用于：服务器可以访问 Git 仓库**

```bash
# 1. SSH 到 Nextcloud 服务器
ssh user@nextcloud-server

# 2. 进入项目目录
cd ~/Data-consolidation

# 3. 拉取最新代码
git fetch origin
git checkout claude/fix-onlyoffice-interceptor-eSwtN
git pull

# 4. 安装依赖（如果需要）
cd nextcloud_apps/onlyoffice_callback_interceptor
composer install --no-dev

# 5. 部署插件
cd ~/Data-consolidation
./nextcloud_apps/deploy_app_correct.sh

# 6. 配置插件
./nextcloud_apps/fix_config_correct.sh
```

### 选项 B：使用预打包文件部署

**适用于：无法使用 Git 或 Composer 的环境**

#### 步骤 1：上传插件包到服务器

```bash
# 从开发机器复制到服务器
scp /home/user/Data-consolidation/nextcloud_apps/onlyoffice_callback_interceptor_v1.0.0.tar.gz \
    user@nextcloud-server:~/
```

#### 步骤 2：在服务器上解压

```bash
# SSH 到服务器
ssh user@nextcloud-server

# 解压插件包
cd ~/Data-consolidation/nextcloud_apps
tar -xzf ~/onlyoffice_callback_interceptor_v1.0.0.tar.gz

# 验证文件
ls -la onlyoffice_callback_interceptor/
```

#### 步骤 3：部署到 Nextcloud

```bash
# 运行部署脚本
cd ~/Data-consolidation
./nextcloud_apps/deploy_app_correct.sh
```

#### 步骤 4：配置插件

```bash
# 自动配置
./nextcloud_apps/fix_config_correct.sh
```

### 选项 C：手动部署（最灵活）

**适用于：需要自定义部署流程的场景**

```bash
# 假设 Nextcloud 在 /opt/docker/nextcloud

# 1. 复制插件到容器
cd /opt/docker/nextcloud
docker compose exec -T app mkdir -p /var/www/html/custom_apps
docker compose cp \
    ~/Data-consolidation/nextcloud_apps/onlyoffice_callback_interceptor \
    app:/var/www/html/custom_apps/

# 2. 设置权限
docker compose exec -T app chown -R www-data:www-data \
    /var/www/html/custom_apps/onlyoffice_callback_interceptor

# 3. 启用插件
docker compose exec -T -u www-data app php occ app:enable onlyoffice_callback_interceptor

# 4. 手动配置
docker compose exec -T -u www-data app php occ config:app:set \
    onlyoffice_callback_interceptor enabled --value="true"

docker compose exec -T -u www-data app php occ config:app:set \
    onlyoffice_callback_interceptor django_callback_url \
    --value="http://data.yamaguchi.lan/api/acquisition/onlyoffice/callback/"

docker compose exec -T -u www-data app php occ config:app:set \
    onlyoffice_callback_interceptor health_check_url \
    --value="http://data.yamaguchi.lan/api/acquisition/health/"

docker compose exec -T -u www-data app php occ config:app:set \
    onlyoffice_callback_interceptor path_filter --value="/data_platform/"

docker compose exec -T -u www-data app php occ config:app:set \
    onlyoffice_callback_interceptor onlyoffice_secret --value="tDCVy4C0oUPWjEXCvCZ4KnFe7N7z5V"

docker compose exec -T -u www-data app php occ config:app:set \
    onlyoffice_callback_interceptor debug_mode --value="true"
```

## ✅ 验证部署

### 1. 检查插件状态

```bash
cd /opt/docker/nextcloud

# 查看已安装的应用
docker compose exec -u www-data app php occ app:list | grep onlyoffice

# 应该看到：
# - onlyoffice_callback_interceptor: enabled
```

### 2. 检查配置

```bash
# 查看所有配置
docker compose exec -u www-data app php occ config:list onlyoffice_callback_interceptor

# 应该包含：
# - enabled: true
# - django_callback_url: http://data.yamaguchi.lan/...
# - health_check_url: http://data.yamaguchi.lan/...
# - path_filter: /data_platform/
# - debug_mode: true
```

### 3. 测试健康检查

```bash
# 手动测试 Django 连接
docker compose exec app curl -f http://data.yamaguchi.lan/api/acquisition/health/

# 应该返回成功状态（HTTP 200）
```

### 4. 检查文件结构

```bash
# 验证所有文件已部署
docker compose exec app ls -la /var/www/html/custom_apps/onlyoffice_callback_interceptor/

# 应该看到：
# - appinfo/
# - lib/
# - vendor/  (包含 firebase/php-jwt)
# - templates/
# - js/
# - css/
# - composer.json
```

## 📊 监控和测试

### 启动日志监控

**终端 1 - Nextcloud 日志：**
```bash
cd /opt/docker/nextcloud
docker compose logs -f app | grep -i "onlyoffice\|callback"
```

**终端 2 - Django 日志：**
```bash
docker logs -f data-platform-django | grep -i onlyoffice
```

### 测试流程

1. **创建测试文件夹**
   - 在 Nextcloud 中创建 `/data_platform/` 文件夹

2. **上传测试文件**
   - 上传一个 Excel 文件到该文件夹

3. **打开文件**
   - 使用 OnlyOffice 打开文件
   - 观察日志输出

4. **验证拦截**
   - Nextcloud 日志应显示: "Callback URL modified"
   - Django 日志应显示: 接收到回调请求

5. **编辑和保存**
   - 编辑文件内容
   - 保存并关闭
   - 验证回调链: OnlyOffice → Django → Nextcloud

## 🔧 故障排查

### 问题：插件未启用

```bash
# 强制启用
docker compose exec -u www-data app php occ app:enable onlyoffice_callback_interceptor --force

# 检查错误日志
docker compose logs app | tail -50
```

### 问题：Composer 依赖缺失

```bash
# 如果 vendor/ 目录不存在或不完整
docker compose exec -u www-data app sh -c \
    "cd /var/www/html/custom_apps/onlyoffice_callback_interceptor && composer install --no-dev"
```

### 问题：权限错误

```bash
# 修复权限
docker compose exec app chown -R www-data:www-data \
    /var/www/html/custom_apps/onlyoffice_callback_interceptor
```

### 问题：健康检查失败

```bash
# 测试 Django 连接
docker compose exec app curl -v http://data.yamaguchi.lan/api/acquisition/health/

# 检查网络连接
docker compose exec app ping -c 3 data.yamaguchi.lan
```

### 问题：回调未被拦截

```bash
# 启用调试模式
docker compose exec -u www-data app php occ config:app:set \
    onlyoffice_callback_interceptor debug_mode --value="true"

# 检查路径过滤器
docker compose exec -u www-data app php occ config:app:get \
    onlyoffice_callback_interceptor path_filter

# 确保文件在正确的目录下（/data_platform/）
```

## 📝 配置参数说明

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `enabled` | `false` | 启用/禁用拦截器 |
| `django_callback_url` | - | Django 回调端点 URL |
| `health_check_url` | - | Django 健康检查 URL |
| `path_filter` | `/Data/` | 只拦截此路径下的文件 |
| `onlyoffice_secret` | - | JWT 签名密钥 |
| `auth_token` | - | 可选的认证 token |
| `include_user_metadata` | `true` | 包含用户信息 |
| `include_timestamp` | `true` | 包含时间戳 |
| `health_check_enabled` | `true` | 启用健康检查 |
| `health_check_interval` | `300` | 健康检查间隔（秒） |
| `debug_mode` | `false` | 调试日志模式 |

## 🎯 预期行为

部署成功后，当用户在 `/data_platform/` 目录下打开 OnlyOffice 文档时：

1. **配置拦截**：OnlyOfficeConfigListener 拦截编辑器配置
2. **健康检查**：验证 Django 后端可用
3. **URL 修改**：回调 URL 改为 Django 端点
4. **元数据注入**：添加 user_id, file_path, timestamp 参数
5. **JWT 签名**：使用 OnlyOffice secret 签名
6. **日志记录**：记录拦截详情（调试模式）

## 📞 支持

如有问题，请查看：
- `IMPLEMENTATION_FIXES.md` - 详细技术文档
- Nextcloud 日志：`docker compose logs app`
- Django 日志：`docker logs data-platform-django`

---

**版本**: 1.0.0
**最后更新**: 2025-01-02
**分支**: claude/fix-onlyoffice-interceptor-eSwtN
