# 依赖安装指南

## 问题说明

这个 FastAdmin 项目遇到了依赖安装的问题，原因如下：

1. **Gitee 仓库访问限制**
   - 项目的 `composer.json` 配置了从 Gitee 拉取特定版本的包
   - 这些 Gitee 仓库返回 403 错误（访问被拒绝）

2. **版本不匹配**
   - 项目使用 ThinkPHP 5.x（`topthink/framework: dev-master`）
   - 需要 `topthink/think-captcha ^1.0.9`
   - 但 Packagist.org 上只有到 v1.0.8，之后就是 v3.0（需要 ThinkPHP 6+）

## 解决方案

### 方案一：在中国大陆网络环境安装（推荐）

如果你在中国大陆，Gitee 访问应该没问题：

```bash
# 1. 清除缓存
composer clear-cache

# 2. 直接安装（使用原 composer.json 配置）
composer install --ignore-platform-reqs

# 3. 如果还是有问题，尝试使用代理或 VPN
```

### 方案二：从已有环境复制 vendor 目录

如果你有其他已经安装成功的环境：

```bash
# 在已安装成功的环境中
tar -czf vendor.tar.gz vendor/

# 复制到当前项目目录并解压
tar -xzf vendor.tar.gz
```

### 方案三：使用 Docker（最稳定）

创建 `docker-compose.yml`:

```yaml
version: '3'
services:
  web:
    image: php:7.4-apache
    ports:
      - "8080:80"
    volumes:
      - .:/var/www/html
    environment:
      - APACHE_DOCUMENT_ROOT=/var/www/html
  db:
    image: mysql:5.7
    environment:
      MYSQL_ROOT_PASSWORD: root
      MYSQL_DATABASE: fastadmin
    ports:
      - "3306:3306"
```

然后：
```bash
docker-compose up -d
docker-compose exec web composer install --ignore-platform-reqs
```

### 方案四：修改 composer.json 使用替代包（可能需要代码调整）

如果无法访问 Gitee，可以尝试：

1. **使用 ThinkPHP 6 或 8**（需要大量代码修改，不推荐）

2. **手动下载包**
   ```bash
   # 从 GitHub 或其他镜像手动下载所需的包
   # 放到 vendor 目录对应位置
   ```

### 方案五：联系项目原作者

访问 FastAdmin 官方网站获取完整安装包：
- 官网：https://www.fastadmin.net
- 下载完整版（已包含 vendor 目录）

## 网络环境诊断

检查你的网络是否可以访问 Gitee：

```bash
# 测试 Gitee 连接
curl -I https://gitee.com

# 测试 Packagist 连接
curl -I https://packagist.org

# 测试阿里云镜像连接
curl -I https://mirrors.aliyun.com
```

## 临时解决方案（仅用于学习测试）

### 使用本地 PHP 服务器（无需完整依赖）

某些 FastAdmin 功能可能不需要所有依赖。你可以：

```bash
# 1. 创建最小的 vendor 目录结构
mkdir -p vendor/topthink

# 2. 下载 ThinkPHP 5.1 核心
git clone https://github.com/top-think/framework.git vendor/topthink/framework

# 3. 下载其他必要的包
# （根据实际需要逐个下载）
```

但这种方法：
- ❌ 不完整，缺少很多依赖
- ❌ 可能导致功能异常
- ❌ 仅适合学习了解项目结构
- ✅ 可以快速查看代码

## 推荐流程

**如果你在中国大陆：**
1. 使用原配置直接安装: `composer install --ignore-platform-reqs`
2. 如果失败，检查网络连接
3. 尝试使用代理

**如果你在海外：**
1. 尝试使用 VPN 连接到中国节点
2. 或从 FastAdmin 官网下载完整包
3. 或使用 Docker 方案

## 安装成功后的验证

```bash
# 检查 vendor 目录
ls -la vendor/

# 检查关键依赖
ls -la vendor/topthink/framework
ls -la vendor/topthink/think-captcha

# 运行项目
php -S localhost:8000
```

## 需要帮助？

1. FastAdmin 官方问答社区: https://ask.fastadmin.net
2. FastAdmin GitHub: https://github.com/karsonzhang/fastadmin
3. FastAdmin Gitee: https://gitee.com/karson/fastadmin

## 当前项目状态

✅ 已完成:
- PhpStorm 配置文档
- 环境配置脚本
- .env 文件配置

❌ 待完成:
- Composer 依赖安装（受网络环境影响）
- PHP 扩展安装（pdo, bcmath）
- 数据库创建和初始化

## 下一步

安装完依赖后，请按照 `PHPSTORM_SETUP.md` 继续配置开发环境。
