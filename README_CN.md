# Mobile Zone Website - 快速开始指南

这是一个基于 FastAdmin 框架（ThinkPHP + Bootstrap）的网站管理系统。

## 快速开始

### 方式一：自动配置（推荐）

运行自动配置脚本：

```bash
bash dev-setup.sh
```

脚本会自动检查：
- PHP 版本和必需扩展
- Composer 安装情况
- 自动安装依赖
- 创建配置文件
- 设置目录权限

### 方式二：手动配置

1. **安装依赖**
```bash
composer install --ignore-platform-reqs
```

2. **配置数据库**
```bash
# 使用 MySQL 配置脚本（推荐）
bash setup-mysql.sh

# 或手动创建数据库
mysql -u root -p
CREATE DATABASE fastadmin CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

详细配置说明：**[MySQL 数据库配置指南](./MYSQL_SETUP_GUIDE.md)**

3. **配置环境文件**
```bash
# 编辑 .env 文件，填写数据库连接信息
nano .env
```

4. **设置权限**
```bash
chmod -R 755 runtime
chmod -R 755 public/uploads
```

## 在 PhpStorm 中开发

详细的 PhpStorm 配置指南请查看：**[PHPSTORM_SETUP.md](./PHPSTORM_SETUP.md)**

### 快速步骤：

1. **打开项目**
   - 在 PhpStorm 中打开此目录

2. **配置 PHP 解释器**
   - `File` → `Settings` → `PHP`
   - 选择 PHP >= 7.4 的解释器

3. **配置数据库**
   - 编辑 `.env` 文件
   - 填写数据库连接信息

4. **运行项目**
   - 右键点击 `index.php`
   - 选择 `Run 'index.php'`
   - 或使用已配置的 "Built-in Server" 运行配置

5. **安装系统**
   - 访问 `http://localhost:8080/install.php`
   - 按照安装向导完成初始化

## 环境要求

- PHP >= 7.4.0
- MySQL >= 5.5
- Composer
- PHP 扩展：json, curl, pdo, bcmath, mbstring

## 项目结构

```
mobile-zone-website/
├── application/        # 应用目录
│   ├── admin/         # 后台管理模块
│   ├── api/           # API 接口模块
│   ├── index/         # 前台模块
│   └── common/        # 公共模块
├── public/            # 公共资源
│   ├── assets/        # 前端资源（CSS、JS）
│   └── uploads/       # 上传文件目录
├── thinkphp/          # ThinkPHP 核心框架
├── addons/            # 插件/扩展目录
├── runtime/           # 运行时缓存
├── .env               # 环境配置文件
└── index.php          # 入口文件
```

## 开发文档

- [PhpStorm 配置详细指南](./PHPSTORM_SETUP.md) - 完整的 IDE 配置说明
- [MySQL 数据库配置指南](./MYSQL_SETUP_GUIDE.md) - 本地数据库配置详解
- [数据库导入指南](./DATABASE_IMPORT_GUIDE.md) - 从服务器导入数据库到本地
- [依赖安装详细指南](./DEPENDENCY_INSTALL_GUIDE.md) - Composer 依赖问题解决
- [FastAdmin 官方文档](https://doc.fastadmin.net) - 框架使用文档
- [ThinkPHP 文档](https://www.kancloud.cn/manual/thinkphp5_1/) - 底层框架文档

## 常用功能

### 后台地址
```
http://localhost:8080/admin
```

### 一键生成 CRUD
FastAdmin 提供了强大的一键生成功能，可以快速生成增删改查功能：
1. 登录后台
2. 进入"一键生成CRUD"菜单
3. 选择数据表并配置
4. 点击生成

### 清除缓存
```bash
# 清除运行时缓存
rm -rf runtime/cache/*
rm -rf runtime/temp/*
```

## 常见问题

### 1. 权限错误
```bash
chmod -R 755 runtime
chmod -R 755 public/uploads
```

### 2. Composer 依赖安装失败
如果遇到 Gitee 403 错误或依赖安装问题，请查看：
**[依赖安装详细指南](./DEPENDENCY_INSTALL_GUIDE.md)**

快速解决方案：
```bash
# 在中国大陆网络环境直接运行
composer install --ignore-platform-reqs

# 如果还是失败，可能需要 VPN 或从官网下载完整包
```

### 3. 数据库表不存在错误
如果出现 `Table 'fastadmin.fa_xxx' doesn't exist` 错误：

需要从服务器导入完整数据库，查看：**[数据库导入指南](./DATABASE_IMPORT_GUIDE.md)**

快速导入：
```bash
# 使用导入脚本
bash import-database.sh

# 或手动导入 SQL 文件
mysql -u root -p fastadmin < your_backup.sql
```

### 4. 数据库连接失败
检查 `.env` 文件中的数据库配置是否正确

### 5. 页面 500 错误
- 检查 `runtime` 目录权限
- 查看错误日志：`runtime/log/`
- 开启调试：`.env` 中设置 `debug = true`

## 开发建议

1. **代码规范**
   - 遵循 PSR-2 编码规范
   - 在 PhpStorm 中启用代码格式化

2. **版本控制**
   - 使用 Git 管理代码
   - 不要提交 `vendor/` 和 `runtime/` 目录

3. **调试**
   - 开发环境开启 debug 模式
   - 使用 PhpStorm 的 Xdebug 进行调试

4. **插件开发**
   - 插件放在 `addons/` 目录
   - 遵循 FastAdmin 插件开发规范

## 技术支持

- FastAdmin 问答社区：https://ask.fastadmin.net
- FastAdmin GitHub：https://github.com/karsonzhang/fastadmin
- ThinkPHP 社区：https://www.thinkphp.cn

## 许可证

Apache-2.0 License

---

**开始愉快地开发吧！** 🚀
