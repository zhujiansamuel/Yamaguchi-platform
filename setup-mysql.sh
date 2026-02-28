#!/bin/bash

# FastAdmin MySQL 快速配置脚本
# 适用于 macOS 本地开发环境

echo "========================================="
echo "FastAdmin MySQL 数据库配置向导"
echo "========================================="
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 默认配置
DB_HOST="127.0.0.1"
DB_PORT="3306"
DB_NAME="fastadmin"
DB_PREFIX="fa_"
DB_CHARSET="utf8mb4"
DB_COLLATE="utf8mb4_general_ci"

echo "步骤 1: 检查 MySQL 安装状态"
echo "-----------------------------------------"

# 检查 MySQL 是否安装
if command -v mysql &> /dev/null; then
    MYSQL_VERSION=$(mysql --version)
    echo -e "${GREEN}✓${NC} MySQL 已安装: $MYSQL_VERSION"
else
    echo -e "${RED}✗${NC} MySQL 未安装"
    echo ""
    echo "请先安装 MySQL："
    echo "  brew install mysql"
    echo "  brew services start mysql"
    exit 1
fi

# 检查 MySQL 服务是否运行
if pgrep -x mysqld > /dev/null; then
    echo -e "${GREEN}✓${NC} MySQL 服务正在运行"
else
    echo -e "${YELLOW}!${NC} MySQL 服务未运行"
    echo "尝试启动 MySQL..."
    brew services start mysql
    sleep 3
    if pgrep -x mysqld > /dev/null; then
        echo -e "${GREEN}✓${NC} MySQL 服务已启动"
    else
        echo -e "${RED}✗${NC} 无法启动 MySQL 服务"
        exit 1
    fi
fi

echo ""
echo "步骤 2: 配置数据库连接信息"
echo "-----------------------------------------"

# 获取 MySQL root 密码
echo "请输入 MySQL root 密码（默认: root）:"
read -s MYSQL_ROOT_PASSWORD
MYSQL_ROOT_PASSWORD=${MYSQL_ROOT_PASSWORD:-root}

# 测试连接
echo ""
echo "测试 MySQL 连接..."
if mysql -h "$DB_HOST" -P "$DB_PORT" -u root -p"$MYSQL_ROOT_PASSWORD" -e "SELECT 1;" &> /dev/null; then
    echo -e "${GREEN}✓${NC} MySQL 连接成功"
else
    echo -e "${RED}✗${NC} MySQL 连接失败，请检查密码是否正确"
    exit 1
fi

echo ""
echo "步骤 3: 数据库配置选项"
echo "-----------------------------------------"

# 询问数据库名称
echo "数据库名称 (默认: $DB_NAME):"
read INPUT_DB_NAME
DB_NAME=${INPUT_DB_NAME:-$DB_NAME}

# 询问表前缀
echo "表前缀 (默认: $DB_PREFIX):"
read INPUT_DB_PREFIX
DB_PREFIX=${INPUT_DB_PREFIX:-$DB_PREFIX}

echo ""
echo "配置摘要："
echo "  主机: $DB_HOST"
echo "  端口: $DB_PORT"
echo "  数据库: $DB_NAME"
echo "  用户: root"
echo "  表前缀: $DB_PREFIX"
echo "  字符集: $DB_CHARSET"
echo "  排序规则: $DB_COLLATE"
echo ""

read -p "确认创建数据库? (y/n): " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "已取消"
    exit 0
fi

echo ""
echo "步骤 4: 创建数据库"
echo "-----------------------------------------"

# 检查数据库是否已存在
DB_EXISTS=$(mysql -h "$DB_HOST" -P "$DB_PORT" -u root -p"$MYSQL_ROOT_PASSWORD" -e "SHOW DATABASES LIKE '$DB_NAME';" 2>/dev/null | grep "$DB_NAME")

if [ ! -z "$DB_EXISTS" ]; then
    echo -e "${YELLOW}!${NC} 数据库 '$DB_NAME' 已存在"
    read -p "是否删除并重新创建? (y/n): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        mysql -h "$DB_HOST" -P "$DB_PORT" -u root -p"$MYSQL_ROOT_PASSWORD" -e "DROP DATABASE $DB_NAME;" 2>/dev/null
        echo -e "${GREEN}✓${NC} 已删除旧数据库"
    else
        echo "保留现有数据库"
    fi
fi

# 创建数据库
CREATE_DB_SQL="CREATE DATABASE IF NOT EXISTS \`$DB_NAME\` CHARACTER SET $DB_CHARSET COLLATE $DB_COLLATE;"

if mysql -h "$DB_HOST" -P "$DB_PORT" -u root -p"$MYSQL_ROOT_PASSWORD" -e "$CREATE_DB_SQL" 2>/dev/null; then
    echo -e "${GREEN}✓${NC} 数据库 '$DB_NAME' 创建成功"
else
    echo -e "${RED}✗${NC} 数据库创建失败"
    exit 1
fi

# 验证数据库
echo ""
echo "验证数据库配置..."
DB_INFO=$(mysql -h "$DB_HOST" -P "$DB_PORT" -u root -p"$MYSQL_ROOT_PASSWORD" -e "SELECT SCHEMA_NAME, DEFAULT_CHARACTER_SET_NAME, DEFAULT_COLLATION_NAME FROM INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME='$DB_NAME';" 2>/dev/null)

if [ ! -z "$DB_INFO" ]; then
    echo -e "${GREEN}✓${NC} 数据库配置验证成功"
    echo "$DB_INFO"
else
    echo -e "${RED}✗${NC} 数据库配置验证失败"
fi

echo ""
echo "步骤 5: 询问是否创建专用数据库用户"
echo "-----------------------------------------"

read -p "是否创建专用数据库用户? (推荐) (y/n): " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    DB_USER="fastadmin"
    echo "请输入用户密码 (默认: fastadmin123):"
    read -s DB_USER_PASSWORD
    DB_USER_PASSWORD=${DB_USER_PASSWORD:-fastadmin123}

    # 删除已存在的用户
    mysql -h "$DB_HOST" -P "$DB_PORT" -u root -p"$MYSQL_ROOT_PASSWORD" -e "DROP USER IF EXISTS '$DB_USER'@'localhost';" 2>/dev/null

    # 创建用户并授权
    mysql -h "$DB_HOST" -P "$DB_PORT" -u root -p"$MYSQL_ROOT_PASSWORD" <<EOF 2>/dev/null
CREATE USER '$DB_USER'@'localhost' IDENTIFIED BY '$DB_USER_PASSWORD';
GRANT ALL PRIVILEGES ON \`$DB_NAME\`.* TO '$DB_USER'@'localhost';
FLUSH PRIVILEGES;
EOF

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓${NC} 用户 '$DB_USER' 创建成功"
        USE_DEDICATED_USER=true
    else
        echo -e "${RED}✗${NC} 用户创建失败，将使用 root 用户"
        USE_DEDICATED_USER=false
        DB_USER="root"
        DB_USER_PASSWORD="$MYSQL_ROOT_PASSWORD"
    fi
else
    USE_DEDICATED_USER=false
    DB_USER="root"
    DB_USER_PASSWORD="$MYSQL_ROOT_PASSWORD"
fi

echo ""
echo "步骤 6: 更新 .env 配置文件"
echo "-----------------------------------------"

# 备份 .env 文件
if [ -f ".env" ]; then
    cp .env .env.backup.$(date +%Y%m%d_%H%M%S)
    echo -e "${GREEN}✓${NC} 已备份 .env 文件"
fi

# 更新 .env 文件
cat > .env <<EOF
[app]
debug = true
trace = true

[database]
hostname = $DB_HOST
database = $DB_NAME
username = $DB_USER
password = $DB_USER_PASSWORD
hostport = $DB_PORT
prefix = $DB_PREFIX
charset = $DB_CHARSET
EOF

echo -e "${GREEN}✓${NC} .env 配置文件已更新"

echo ""
echo "========================================="
echo "配置完成！"
echo "========================================="
echo ""
echo "数据库信息："
echo "  主机: $DB_HOST:$DB_PORT"
echo "  数据库: $DB_NAME"
echo "  用户: $DB_USER"
echo "  密码: $DB_USER_PASSWORD"
echo "  字符集: $DB_CHARSET ($DB_COLLATE)"
echo ""
echo "下一步操作："
echo "1. 确保已安装 Composer 依赖:"
echo "   composer install --ignore-platform-reqs"
echo ""
echo "2. 访问安装页面初始化系统:"
echo "   http://localhost:8080/install.php"
echo ""
echo "3. 或使用命令行安装:"
echo "   php think install --hostname=$DB_HOST --database=$DB_NAME --username=$DB_USER --password=$DB_USER_PASSWORD"
echo ""
echo "详细说明请查看: MYSQL_SETUP_GUIDE.md"
echo ""
