# PhpStorm 开发环境配置指南

本文档将指导你如何在 PhpStorm 中配置和运行 Mobile Zone Website 项目（基于 FastAdmin/ThinkPHP 框架）。

## 项目介绍

这是一个基于 FastAdmin 框架（ThinkPHP + Bootstrap）的极速后台开发系统。

## 环境要求

- PHP >= 7.4.0
- MySQL >= 5.5
- Composer
- Apache/Nginx Web 服务器（推荐使用 PhpStorm 内置服务器）
- 以下 PHP 扩展：
  - json
  - curl
  - pdo
  - bcmath

## 一、在 PhpStorm 中打开项目

### 1.1 打开项目
1. 启动 PhpStorm
2. 选择 `File` → `Open`
3. 选择项目目录：`/home/user/mobile-zone-website`
4. 点击 `OK`

### 1.2 配置 PHP 解释器
1. 打开 `File` → `Settings` (Windows/Linux) 或 `PhpStorm` → `Preferences` (macOS)
2. 导航到 `PHP`
3. 点击 `CLI Interpreter` 右侧的 `...` 按钮
4. 点击 `+` 添加新的解释器
5. 选择本地 PHP 安装路径（确保 PHP 版本 >= 7.4）
6. 点击 `OK` 保存

## 二、安装项目依赖

### 2.1 安装 Composer 依赖

在 PhpStorm 底部打开 `Terminal`，执行以下命令：

```bash
composer install
```

如果 composer 安装速度慢，可以使用国内镜像：

```bash
# 配置阿里云镜像
composer config -g repo.packagist composer https://mirrors.aliyun.com/composer/

# 然后再执行安装
composer install
```

### 2.2 配置 Composer

PhpStorm 中配置 Composer：
1. 打开 `Settings` → `PHP` → `Composer`
2. 设置 Composer executable 路径（通常是 `/usr/local/bin/composer` 或 `composer.phar`）
3. 勾选 `Synchronize IDE settings with composer.json`

## 三、配置数据库

### 3.1 创建数据库配置文件

项目根目录下有 `.env.sample` 文件，需要创建实际的配置文件：

```bash
cp .env.sample .env
```

### 3.2 编辑 .env 文件

使用 PhpStorm 打开 `.env` 文件，配置数据库连接信息：

```ini
[app]
debug = true
trace = true

[database]
hostname = 127.0.0.1
database = fastadmin          # 修改为你的数据库名
username = root               # 修改为你的数据库用户名
password = your_password      # 修改为你的数据库密码
hostport = 3306
prefix = fa_
```

### 3.3 创建数据库

使用 MySQL 客户端或 PhpStorm 的数据库工具创建数据库：

```sql
CREATE DATABASE fastadmin CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 3.4 在 PhpStorm 中配置数据库连接

1. 打开 `View` → `Tool Windows` → `Database`
2. 点击 `+` → `Data Source` → `MySQL`
3. 填写数据库连接信息（与 .env 文件中的配置保持一致）
4. 点击 `Test Connection` 测试连接
5. 点击 `OK` 保存

## 四、配置 Web 服务器

### 方法一：使用 PhpStorm 内置服务器（推荐用于开发）

1. 打开 `Settings` → `PHP` → `Built-in Web Server`
2. 设置 `Document root` 为项目根目录

**运行项目：**
1. 在 PhpStorm 中右键点击 `index.php` 文件
2. 选择 `Open in Browser` → 选择浏览器
3. PhpStorm 会自动启动内置服务器并打开浏览器

### 方法二：配置 Apache/Nginx

#### Apache 配置示例

创建虚拟主机配置文件：

```apache
<VirtualHost *:80>
    ServerName mobile-zone.local
    DocumentRoot "/home/user/mobile-zone-website"

    <Directory "/home/user/mobile-zone-website">
        Options Indexes FollowSymLinks
        AllowOverride All
        Require all granted
    </Directory>

    ErrorLog ${APACHE_LOG_DIR}/mobile-zone-error.log
    CustomLog ${APACHE_LOG_DIR}/mobile-zone-access.log combined
</VirtualHost>
```

修改 `/etc/hosts` 文件：
```
127.0.0.1 mobile-zone.local
```

#### Nginx 配置示例

```nginx
server {
    listen 80;
    server_name mobile-zone.local;
    root /home/user/mobile-zone-website;
    index index.php index.html;

    location / {
        if (!-e $request_filename) {
            rewrite ^(.*)$ /index.php?s=$1 last;
            break;
        }
    }

    location ~ \.php$ {
        fastcgi_pass 127.0.0.1:9000;
        fastcgi_index index.php;
        fastcgi_param SCRIPT_FILENAME $document_root$fastcgi_script_name;
        include fastcgi_params;
    }

    location ~ /\.ht {
        deny all;
    }
}
```

修改 `/etc/hosts` 文件：
```
127.0.0.1 mobile-zone.local
```

## 五、导入数据库（如果有 SQL 文件）

FastAdmin 通常需要安装才能初始化数据库。有两种方式：

### 方法一：使用安装向导
1. 访问 `http://localhost:端口/install.php`
2. 按照安装向导完成安装

### 方法二：如果已有数据库备份
在 PhpStorm 的数据库工具中导入 SQL 文件：
1. 在 `Database` 工具窗口中右键点击数据库
2. 选择 `Run SQL Script`
3. 选择 SQL 文件并执行

## 六、PhpStorm 开发工具配置

### 6.1 配置代码格式化

1. `Settings` → `Editor` → `Code Style` → `PHP`
2. 选择 `Set from...` → `PSR-2`

### 6.2 启用 Xdebug 调试

1. 安装 Xdebug 扩展
2. `Settings` → `PHP` → `Debug`
3. 配置 Xdebug 端口（默认 9003）
4. 在代码中设置断点
5. 点击工具栏的调试按钮启动调试

### 6.3 配置版本控制（Git）

项目已经是 Git 仓库，PhpStorm 会自动识别。你可以：
1. 使用 `VCS` → `Git` → `Branches` 管理分支
2. 使用 `VCS` → `Commit` 提交代码
3. 使用 `VCS` → `Update Project` 拉取更新

### 6.4 启用 Laravel/ThinkPHP 插件支持

1. `Settings` → `Plugins`
2. 搜索 "Laravel" 或 "ThinkPHP"
3. 安装相关插件以获得更好的代码提示和补全

## 七、运行项目

### 使用 PhpStorm 内置服务器运行

1. 右键点击 `index.php`
2. 选择 `Run 'index.php'`
3. 浏览器会自动打开项目

或者：
1. 点击 PhpStorm 右上角的 `Add Configuration`
2. 点击 `+` → `PHP Built-in Web Server`
3. 配置：
   - Name: Mobile Zone Website
   - Document root: 项目根目录
   - Use a router script: 勾选并选择 `index.php`
4. 点击 `OK` 保存
5. 点击运行按钮启动

### 访问项目

- 前台：http://localhost:8080
- 后台：http://localhost:8080/admin
- 默认后台账号（如果已安装）：
  - 用户名：admin
  - 密码：（根据安装时设置）

## 八、常见问题排查

### 8.1 权限问题

确保以下目录有写入权限：
```bash
chmod -R 755 runtime
chmod -R 755 public/uploads
```

### 8.2 composer 安装失败

尝试删除 `composer.lock` 和 `vendor` 目录后重新安装：
```bash
rm -rf vendor composer.lock
composer install
```

### 8.3 数据库连接失败

- 检查 `.env` 文件中的数据库配置是否正确
- 确认 MySQL 服务是否已启动
- 检查数据库用户权限

### 8.4 500 错误

- 检查 `runtime` 目录权限
- 查看错误日志：`runtime/log/` 目录
- 开启调试模式（`.env` 中设置 `debug = true`）

## 九、开发建议

### 9.1 目录结构

```
mobile-zone-website/
├── application/        # 应用目录
│   ├── admin/         # 后台模块
│   ├── api/           # API 模块
│   ├── index/         # 前台模块
│   └── ...
├── public/            # 公共资源目录
│   ├── assets/        # 前端资源
│   └── uploads/       # 上传文件
├── thinkphp/          # ThinkPHP 框架核心
├── addons/            # 插件目录
├── runtime/           # 运行时缓存
├── .env               # 环境配置文件
├── composer.json      # Composer 依赖配置
└── index.php          # 入口文件
```

### 9.2 开发流程

1. 在 `application` 目录下创建或修改模块
2. 使用 FastAdmin 的一键生成功能生成 CRUD
3. 修改视图文件（.html）在对应模块的 view 目录
4. 修改控制器在对应模块的 controller 目录
5. 修改模型在 model 目录

### 9.3 查看文档

- FastAdmin 官方文档：https://doc.fastadmin.net
- ThinkPHP 官方文档：https://www.kancloud.cn/manual/thinkphp5_1/

## 十、开始开发

现在你的开发环境已经配置完成！可以开始进行二次开发了。

主要开发入口：
- 控制器：`application/*/controller/`
- 模型：`application/*/model/`
- 视图：`application/*/view/`
- 公共函数：`application/common.php`
- 配置文件：`application/*/config.php`

祝开发愉快！
