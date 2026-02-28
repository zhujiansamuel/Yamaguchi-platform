# MySQL 本地数据库配置指南

## 📊 数据库配置分析

根据项目代码分析，以下是服务器使用的数据库配置：

### 核心配置要求

```ini
数据库类型: MySQL
字符集: utf8mb4
排序规则: utf8mb4_general_ci
存储引擎: InnoDB
表前缀: fa_
默认端口: 3306
最低 MySQL 版本: 5.5+（推荐 5.7+ 或 8.0+）
```

### 配置文件位置

- 主配置：`application/database.php`
- 环境配置：`.env`
- SQL 初始化文件：`application/admin/command/Install/fastadmin.sql`

## 🚀 macOS 本地 MySQL 安装与配置

### 方法一：使用 Homebrew 安装（推荐）

```bash
# 1. 安装 MySQL
brew install mysql

# 2. 启动 MySQL 服务
brew services start mysql

# 3. 运行安全配置（设置 root 密码）
mysql_secure_installation
```

**安全配置建议：**
```
- 设置 root 密码: root（或自定义）
- 移除匿名用户: Yes
- 禁止 root 远程登录: No（本地开发可以选 No）
- 移除 test 数据库: Yes
- 重载权限表: Yes
```

### 方法二：下载 MySQL 安装包

访问：https://dev.mysql.com/downloads/mysql/
下载 macOS DMG 安装包并安装

## 🔧 创建项目数据库

### 1. 连接到 MySQL

```bash
mysql -u root -p
# 输入密码: root（或你设置的密码）
```

### 2. 创建数据库（兼容服务器配置）

```sql
-- 创建数据库，使用 utf8mb4 字符集和 utf8mb4_general_ci 排序规则
CREATE DATABASE fastadmin
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_general_ci;

-- 验证数据库创建
SHOW CREATE DATABASE fastadmin;

-- 切换到新数据库
USE fastadmin;
```

### 3. 创建数据库用户（可选，推荐）

```sql
-- 创建专用用户（用户名: fastadmin, 密码: fastadmin123）
CREATE USER 'fastadmin'@'localhost' IDENTIFIED BY 'fastadmin123';

-- 授予所有权限
GRANT ALL PRIVILEGES ON fastadmin.* TO 'fastadmin'@'localhost';

-- 刷新权限
FLUSH PRIVILEGES;

-- 验证用户创建
SELECT User, Host FROM mysql.user WHERE User = 'fastadmin';
```

### 4. 导入初始化 SQL（安装后自动执行，这里仅供手动导入参考）

```bash
# 如果需要手动导入 SQL 文件
mysql -u root -p fastadmin < application/admin/command/Install/fastadmin.sql
```

## ⚙️ 配置项目 .env 文件

编辑项目根目录的 `.env` 文件：

### 配置方案一：使用 root 用户（简单）

```ini
[app]
debug = true
trace = true

[database]
hostname = 127.0.0.1
database = fastadmin
username = root
password = root              # 改为你的 root 密码
hostport = 3306
prefix = fa_
charset = utf8mb4
```

### 配置方案二：使用专用用户（推荐）

```ini
[app]
debug = true
trace = true

[database]
hostname = 127.0.0.1
database = fastadmin
username = fastadmin         # 使用专用用户
password = fastadmin123      # 使用专用密码
hostport = 3306
prefix = fa_
charset = utf8mb4
```

## 🔍 在 PhpStorm 中配置数据库连接

### 1. 打开数据库工具

- `View` → `Tool Windows` → `Database`
- 或按快捷键：`⌘ + Shift + D` (macOS) / `Ctrl + Shift + D` (Windows)

### 2. 添加 MySQL 数据源

1. 点击 `+` → `Data Source` → `MySQL`
2. 填写连接信息：
   ```
   Host: localhost (或 127.0.0.1)
   Port: 3306
   Database: fastadmin
   User: root (或 fastadmin)
   Password: root (或 fastadmin123)
   ```
3. 点击 `Test Connection` 测试连接
4. 如果提示下载驱动，点击 `Download` 下载 MySQL 驱动
5. 连接成功后点击 `OK`

### 3. 配置高级选项（可选）

在 `Advanced` 标签中：
```
serverTimezone: Asia/Shanghai
useSSL: false
allowPublicKeyRetrieval: true
```

## 🛠️ MySQL 配置优化（可选）

### macOS 配置文件位置

```bash
# 使用 Homebrew 安装的 MySQL
/opt/homebrew/etc/my.cnf  # Apple Silicon (M1/M2)
/usr/local/etc/my.cnf     # Intel

# 如果文件不存在，创建它
touch /opt/homebrew/etc/my.cnf  # 或对应路径
```

### 推荐配置（开发环境）

编辑 `my.cnf` 添加以下内容：

```ini
[mysqld]
# 字符集配置
character-set-server = utf8mb4
collation-server = utf8mb4_general_ci

# 默认存储引擎
default-storage-engine = INNODB

# 端口
port = 3306

# 允许的最大数据包大小
max_allowed_packet = 64M

# SQL 模式（与服务器保持一致）
sql_mode = "STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION"

# 时区设置
default-time-zone = '+08:00'

[client]
default-character-set = utf8mb4

[mysql]
default-character-set = utf8mb4
```

### 重启 MySQL 应用配置

```bash
brew services restart mysql
```

## ✅ 验证配置

### 1. 检查 MySQL 版本和字符集

```sql
-- 连接到 MySQL
mysql -u root -p

-- 查看版本
SELECT VERSION();

-- 查看字符集配置
SHOW VARIABLES LIKE 'character%';
SHOW VARIABLES LIKE 'collation%';

-- 应该看到：
-- character_set_server: utf8mb4
-- collation_server: utf8mb4_general_ci
```

### 2. 测试 PHP 连接

创建测试文件 `test-db.php`:

```php
<?php
// 使用 .env 中的配置
$host = '127.0.0.1';
$port = 3306;
$dbname = 'fastadmin';
$username = 'root';  // 或 fastadmin
$password = 'root';  // 或 fastadmin123

try {
    $dsn = "mysql:host=$host;port=$port;dbname=$dbname;charset=utf8mb4";
    $pdo = new PDO($dsn, $username, $password);
    $pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);

    echo "✅ 数据库连接成功！\n";

    // 显示数据库信息
    $stmt = $pdo->query("SELECT DATABASE(), VERSION(), @@character_set_database, @@collation_database");
    $info = $stmt->fetch(PDO::FETCH_NUM);

    echo "数据库名: {$info[0]}\n";
    echo "MySQL 版本: {$info[1]}\n";
    echo "字符集: {$info[2]}\n";
    echo "排序规则: {$info[3]}\n";

} catch(PDOException $e) {
    echo "❌ 连接失败: " . $e->getMessage() . "\n";
}
```

运行测试：
```bash
php test-db.php
```

## 🎯 推荐的本地配置方案

### 完全兼容服务器的配置

```ini
# .env 配置
[app]
debug = true
trace = true

[database]
hostname = 127.0.0.1
database = fastadmin
username = root
password = root
hostport = 3306
prefix = fa_
charset = utf8mb4
```

### MySQL 用户配置

```sql
-- 数据库
CREATE DATABASE fastadmin CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;

-- 用户（如果使用专用用户）
CREATE USER 'fastadmin'@'localhost' IDENTIFIED BY 'fastadmin123';
GRANT ALL PRIVILEGES ON fastadmin.* TO 'fastadmin'@'localhost';
FLUSH PRIVILEGES;
```

## 🚦 下一步操作

配置完成后：

1. **初始化数据库**
   - 访问：http://localhost:8080/install.php
   - 按照安装向导完成系统初始化

2. **或使用命令行安装**
   ```bash
   php think install \
     --hostname=127.0.0.1 \
     --hostport=3306 \
     --database=fastadmin \
     --username=root \
     --password=root \
     --prefix=fa_
   ```

3. **安装完成后**
   - 后台地址：http://localhost:8080/admin
   - 默认账号：admin
   - 密码：安装时设置或自动生成（查看安装输出）

## 🔧 常见问题

### 1. MySQL 服务无法启动

```bash
# 查看 MySQL 状态
brew services list

# 停止并重启
brew services stop mysql
brew services start mysql

# 查看错误日志
tail -f /opt/homebrew/var/mysql/*.err  # Apple Silicon
tail -f /usr/local/var/mysql/*.err     # Intel
```

### 2. 无法连接到 MySQL

```bash
# 检查 MySQL 是否运行
ps aux | grep mysql

# 检查端口是否监听
lsof -i :3306

# 重置 root 密码（如果忘记）
brew services stop mysql
mysqld_safe --skip-grant-tables &
mysql -u root
mysql> ALTER USER 'root'@'localhost' IDENTIFIED BY 'root';
mysql> FLUSH PRIVILEGES;
mysql> EXIT;
killall mysqld
brew services start mysql
```

### 3. 字符集问题

如果遇到乱码：

```sql
-- 修改数据库字符集
ALTER DATABASE fastadmin CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;

-- 修改所有表的字符集
SET @DATABASE_NAME = 'fastadmin';
SELECT CONCAT('ALTER TABLE ', TABLE_NAME, ' CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;')
FROM INFORMATION_SCHEMA.TABLES
WHERE TABLE_SCHEMA = @DATABASE_NAME;
```

### 4. PhpStorm 无法连接数据库

- 确保下载了 MySQL 驱动
- 检查防火墙设置
- 尝试使用 127.0.0.1 代替 localhost

## 📚 参考资源

- MySQL 官方文档：https://dev.mysql.com/doc/
- FastAdmin 文档：https://doc.fastadmin.net
- ThinkPHP 数据库文档：https://www.kancloud.cn/manual/thinkphp5_1/354000

---

配置完成后，你的本地环境将完全兼容服务器配置！
