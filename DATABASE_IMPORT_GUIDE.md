# 服务器数据库导入本地指南

## 问题说明

错误信息：`SQLSTATE[42S02]: Base table or view not found: 1146 Table 'fastadmin.fa_category' doesn't exist`

这说明本地数据库缺少必要的表和数据。需要从服务器导出完整数据库并导入到本地。

## 🚀 方法一：使用 mysqldump（推荐，最完整）

### 1. 在服务器上导出数据库

```bash
# SSH 连接到服务器
ssh user@your-server.com

# 导出整个数据库（包含结构和数据）
mysqldump -u root -p fastadmin > fastadmin_backup_$(date +%Y%m%d).sql

# 或者指定主机和端口
mysqldump -h 127.0.0.1 -P 3306 -u root -p fastadmin > fastadmin_backup.sql

# 导出完成后，下载到本地
# 退出 SSH，然后在本地执行：
scp user@your-server.com:/path/to/fastadmin_backup.sql ~/Downloads/
```

### 2. 在本地导入数据库

```bash
# 进入项目目录
cd /path/to/mobile-zone-website

# 方式 A：直接导入（会覆盖现有数据）
mysql -u root -p fastadmin < ~/Downloads/fastadmin_backup.sql

# 方式 B：先删除数据库再导入（更干净）
mysql -u root -p <<EOF
DROP DATABASE IF EXISTS fastadmin;
CREATE DATABASE fastadmin CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
USE fastadmin;
SOURCE ~/Downloads/fastadmin_backup.sql;
EOF
```

### 3. 验证导入

```bash
# 检查表是否存在
mysql -u root -p fastadmin -e "SHOW TABLES;"

# 检查数据
mysql -u root -p fastadmin -e "SELECT COUNT(*) FROM fa_admin;"
mysql -u root -p fastadmin -e "SELECT COUNT(*) FROM fa_category;"
```

## 🔧 方法二：使用项目内置的 adminer.php

项目中有 `adminer_jx.php` 工具，可以用来管理数据库。

### 1. 在服务器上导出

```bash
# 访问服务器的 adminer
https://your-server.com/adminer_jx.php

# 登录后：
1. 选择数据库 'fastadmin'
2. 点击 "Export" 导出
3. 选择格式：SQL
4. 选择选项：
   - Output: save (下载到本地)
   - Format: SQL
   - Database: 勾选所有表
   - 勾选 "DROP + CREATE"
   - 勾选 "Data"
5. 点击 "Export" 下载
```

### 2. 在本地导入

```bash
# 方式 A：使用命令行
mysql -u root -p fastadmin < adminer_export.sql

# 方式 B：使用本地 adminer
# 启动项目服务器
php -S localhost:8080 -t public

# 访问 adminer
http://localhost:8080/../adminer_jx.php

# 登录本地数据库后：
1. 选择数据库 'fastadmin'
2. 点击 "Import"
3. 选择之前下载的 SQL 文件
4. 点击 "Execute" 执行导入
```

## 💻 方法三：使用 PhpStorm 数据库工具

### 1. 连接到服务器数据库

```
File → New → Data Source → MySQL

连接信息：
Host: your-server.com
Port: 3306
Database: fastadmin
User: root
Password: 服务器密码

注意：确保服务器允许远程连接
```

### 2. 导出服务器数据

```
1. 在 Database 工具窗口中，右键点击服务器的数据库
2. 选择 SQL Scripts → SQL Generator
3. 选择所有表
4. 勾选：
   - CREATE statements
   - INSERT statements
   - DROP statements (可选)
5. 点击 "Copy to Clipboard" 或保存为文件
```

### 3. 导入到本地数据库

```
1. 在 Database 工具窗口中，右键点击本地数据库
2. 选择 Run SQL Script
3. 选择刚才保存的 SQL 文件
4. 点击 "Run" 执行
```

## 🔐 方法四：通过 SSH 隧道连接服务器数据库

如果服务器不允许远程 MySQL 连接，可以使用 SSH 隧道：

### 1. 建立 SSH 隧道

```bash
# 在本地执行（保持运行）
ssh -L 3307:127.0.0.1:3306 user@your-server.com

# 这会将服务器的 3306 端口映射到本地的 3307 端口
```

### 2. 使用本地工具连接

```bash
# 使用 mysqldump 通过隧道导出
mysqldump -h 127.0.0.1 -P 3307 -u root -p fastadmin > server_fastadmin.sql

# 导入到本地数据库
mysql -u root -p fastadmin < server_fastadmin.sql
```

## 📝 快速导入脚本

创建一个自动化脚本：

```bash
#!/bin/bash

echo "========================================="
echo "从服务器导入数据库到本地"
echo "========================================="
echo ""

# 配置
SERVER_HOST="your-server.com"
SERVER_USER="root"
SERVER_DB="fastadmin"
LOCAL_USER="root"
LOCAL_DB="fastadmin"
BACKUP_FILE="server_fastadmin_$(date +%Y%m%d_%H%M%S).sql"

echo "步骤 1: 从服务器导出数据库..."
ssh $SERVER_HOST "mysqldump -u $SERVER_USER -p $SERVER_DB" > $BACKUP_FILE

if [ $? -eq 0 ]; then
    echo "✓ 导出成功: $BACKUP_FILE"
else
    echo "✗ 导出失败"
    exit 1
fi

echo ""
echo "步骤 2: 导入到本地数据库..."
echo "请输入本地 MySQL root 密码:"
mysql -u $LOCAL_USER -p $LOCAL_DB < $BACKUP_FILE

if [ $? -eq 0 ]; then
    echo "✓ 导入成功"
else
    echo "✗ 导入失败"
    exit 1
fi

echo ""
echo "步骤 3: 验证数据..."
mysql -u $LOCAL_USER -p $LOCAL_DB -e "SHOW TABLES;" | wc -l

echo ""
echo "========================================="
echo "完成！"
echo "备份文件已保存: $BACKUP_FILE"
echo "========================================="
```

## ⚠️ 注意事项

### 1. 数据库配置差异

确保本地 `.env` 配置正确：

```ini
[database]
hostname = 127.0.0.1
database = fastadmin
username = root
password = root        # 本地密码
hostport = 3306
prefix = fa_
charset = utf8mb4
```

### 2. 文件路径问题

如果数据库中存储了文件路径（如上传的图片），可能需要：

```bash
# 同时下载服务器的 public/uploads 目录
rsync -avz user@your-server.com:/path/to/public/uploads/ ./public/uploads/
```

### 3. 管理员密码

从服务器导入数据后，管理员账号和密码也会被覆盖为服务器的账号密码。

### 4. 字符集检查

```sql
-- 检查数据库字符集
SHOW CREATE DATABASE fastadmin;

-- 如果字符集不对，修改：
ALTER DATABASE fastadmin CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
```

## 🔍 常见问题

### 问题 1：导入时出现字符集错误

```bash
# 导入时指定字符集
mysql -u root -p --default-character-set=utf8mb4 fastadmin < backup.sql
```

### 问题 2：表已存在错误

```bash
# 先删除所有表
mysql -u root -p fastadmin -e "
SET FOREIGN_KEY_CHECKS = 0;
DROP TABLE IF EXISTS fa_admin, fa_category, fa_config;
-- 列出所有表
SET FOREIGN_KEY_CHECKS = 1;
"

# 或者直接重建数据库
mysql -u root -p -e "
DROP DATABASE IF EXISTS fastadmin;
CREATE DATABASE fastadmin CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
"

# 然后导入
mysql -u root -p fastadmin < backup.sql
```

### 问题 3：权限问题

```bash
# 确保本地用户有足够权限
mysql -u root -p -e "
GRANT ALL PRIVILEGES ON fastadmin.* TO 'root'@'localhost';
FLUSH PRIVILEGES;
"
```

## ✅ 验证清单

导入完成后，检查以下内容：

```bash
# 1. 检查所有表
mysql -u root -p fastadmin -e "SHOW TABLES;"

# 2. 检查表数量
mysql -u root -p fastadmin -e "
SELECT COUNT(*) AS table_count
FROM information_schema.tables
WHERE table_schema = 'fastadmin';
"

# 3. 检查关键表的数据
mysql -u root -p fastadmin -e "
SELECT 'fa_admin' AS table_name, COUNT(*) AS row_count FROM fa_admin
UNION ALL
SELECT 'fa_category', COUNT(*) FROM fa_category
UNION ALL
SELECT 'fa_config', COUNT(*) FROM fa_config;
"

# 4. 检查管理员账号
mysql -u root -p fastadmin -e "SELECT id, username, email FROM fa_admin;"
```

## 🎯 推荐流程（最简单）

```bash
# 1. 在服务器上
ssh your-server
mysqldump -u root -p fastadmin > /tmp/fastadmin.sql
exit

# 2. 下载到本地
scp your-server:/tmp/fastadmin.sql ~/Downloads/

# 3. 在本地导入
mysql -u root -p fastadmin < ~/Downloads/fastadmin.sql

# 4. 启动项目测试
bash start-server.sh

# 5. 访问后台
# http://localhost:8080/admin
# 使用服务器的管理员账号密码登录
```

---

选择最适合你的方法，如果服务器有 SSH 访问权限，推荐使用 **方法一（mysqldump）**，这是最可靠和完整的方式。
