#!/bin/bash

# 检查并切换到已存在的数据库

echo "========================================="
echo "检查并切换数据库"
echo "========================================="
echo ""

# 颜色
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

DB_HOST="127.0.0.1"
DB_USER="root"
TARGET_DB="xs942548_mobilezoneweb"

# 获取密码
read -s -p "请输入 MySQL root 密码: " DB_PASSWORD
echo ""
echo ""

# 测试连接
mysql -h "$DB_HOST" -u "$DB_USER" -p"$DB_PASSWORD" -e "SELECT 1;" 2>/dev/null >/dev/null
if [ $? -ne 0 ]; then
    echo -e "${RED}✗${NC} 数据库连接失败，请检查密码"
    exit 1
fi

echo -e "${GREEN}✓${NC} 数据库连接成功"
echo ""

# 列出所有数据库
echo "本地所有数据库："
mysql -h "$DB_HOST" -u "$DB_USER" -p"$DB_PASSWORD" -e "SHOW DATABASES;" 2>/dev/null | grep -v "Database\|information_schema\|performance_schema\|mysql\|sys"
echo ""

# 检查目标数据库是否存在
DB_EXISTS=$(mysql -h "$DB_HOST" -u "$DB_USER" -p"$DB_PASSWORD" -e "SHOW DATABASES LIKE '$TARGET_DB';" 2>/dev/null | grep "$TARGET_DB")

if [ -z "$DB_EXISTS" ]; then
    echo -e "${RED}✗${NC} 数据库 '$TARGET_DB' 不存在"
    echo ""
    echo "可用的数据库："
    mysql -h "$DB_HOST" -u "$DB_USER" -p"$DB_PASSWORD" -e "SHOW DATABASES;" 2>/dev/null | grep -v "Database\|information_schema\|performance_schema\|mysql\|sys" | nl
    echo ""
    read -p "请输入要使用的数据库名: " TARGET_DB

    DB_EXISTS=$(mysql -h "$DB_HOST" -u "$DB_USER" -p"$DB_PASSWORD" -e "SHOW DATABASES LIKE '$TARGET_DB';" 2>/dev/null | grep "$TARGET_DB")
    if [ -z "$DB_EXISTS" ]; then
        echo -e "${RED}✗${NC} 数据库 '$TARGET_DB' 不存在"
        exit 1
    fi
fi

echo -e "${GREEN}✓${NC} 找到数据库: $TARGET_DB"
echo ""

# 显示数据库信息
echo "数据库信息："
mysql -h "$DB_HOST" -u "$DB_USER" -p"$DB_PASSWORD" "$TARGET_DB" <<EOF 2>/dev/null
SELECT
    SCHEMA_NAME AS '数据库名',
    DEFAULT_CHARACTER_SET_NAME AS '字符集',
    DEFAULT_COLLATION_NAME AS '排序规则'
FROM information_schema.SCHEMATA
WHERE SCHEMA_NAME = '$TARGET_DB';
EOF

echo ""

# 显示表列表
echo "数据库表列表："
TABLE_COUNT=$(mysql -h "$DB_HOST" -u "$DB_USER" -p"$DB_PASSWORD" "$TARGET_DB" -se "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = '$TARGET_DB';" 2>/dev/null)

if [ "$TABLE_COUNT" -gt 0 ]; then
    echo -e "${GREEN}✓${NC} 包含 $TABLE_COUNT 个表"
    echo ""
    mysql -h "$DB_HOST" -u "$DB_USER" -p"$DB_PASSWORD" "$TARGET_DB" -e "SHOW TABLES;" 2>/dev/null | head -20

    if [ "$TABLE_COUNT" -gt 20 ]; then
        echo "... (共 $TABLE_COUNT 个表)"
    fi
else
    echo -e "${YELLOW}!${NC} 数据库为空（0 个表）"
fi

echo ""

# 检查关键表
echo "检查 FastAdmin 关键表："
CRITICAL_TABLES=("fa_admin" "fa_category" "fa_config" "fa_attachment")

MISSING_TABLES=()
for table in "${CRITICAL_TABLES[@]}"; do
    EXISTS=$(mysql -h "$DB_HOST" -u "$DB_USER" -p"$DB_PASSWORD" "$TARGET_DB" -se "SHOW TABLES LIKE '$table';" 2>/dev/null)
    if [ -n "$EXISTS" ]; then
        COUNT=$(mysql -h "$DB_HOST" -u "$DB_USER" -p"$DB_PASSWORD" "$TARGET_DB" -se "SELECT COUNT(*) FROM \`$table\`;" 2>/dev/null)
        echo -e "${GREEN}✓${NC} $table: $COUNT 条记录"
    else
        echo -e "${RED}✗${NC} $table: 不存在"
        MISSING_TABLES+=("$table")
    fi
done

echo ""

# 如果有缺失的关键表，询问是否继续
if [ ${#MISSING_TABLES[@]} -gt 0 ]; then
    echo -e "${YELLOW}警告: 缺少以下关键表: ${MISSING_TABLES[*]}${NC}"
    echo ""
    read -p "仍然要使用此数据库吗? (y/n): " USE_ANYWAY
    if [[ ! $USE_ANYWAY =~ ^[Yy]$ ]]; then
        echo "已取消"
        exit 0
    fi
fi

# 显示管理员信息（如果表存在）
ADMIN_EXISTS=$(mysql -h "$DB_HOST" -u "$DB_USER" -p"$DB_PASSWORD" "$TARGET_DB" -se "SHOW TABLES LIKE 'fa_admin';" 2>/dev/null)
if [ -n "$ADMIN_EXISTS" ]; then
    echo "管理员账号："
    mysql -h "$DB_HOST" -u "$DB_USER" -p"$DB_PASSWORD" "$TARGET_DB" -e "SELECT id, username, email, status FROM fa_admin LIMIT 5;" 2>/dev/null
    echo ""
fi

# 更新 .env 文件
echo "========================================="
echo "更新配置文件"
echo "========================================="
echo ""

if [ ! -f ".env" ]; then
    echo -e "${YELLOW}!${NC} .env 文件不存在，从模板创建..."
    if [ -f ".env.sample" ]; then
        cp .env.sample .env
        echo -e "${GREEN}✓${NC} 已创建 .env 文件"
    else
        echo -e "${RED}✗${NC} .env.sample 文件不存在"
        exit 1
    fi
fi

# 备份 .env
cp .env .env.backup.$(date +%Y%m%d_%H%M%S)
echo -e "${GREEN}✓${NC} 已备份 .env 文件"

# 更新数据库配置
echo ""
echo "当前 .env 配置："
grep "^database" .env 2>/dev/null || grep "database" .env 2>/dev/null | head -5

echo ""
echo "更新为："
echo "  hostname = $DB_HOST"
echo "  database = $TARGET_DB"
echo "  username = $DB_USER"
echo "  password = ********"
echo ""

# 使用 sed 或直接重写 .env 数据库部分
cat > .env <<EOF
[app]
debug = true
trace = true

[database]
hostname = $DB_HOST
database = $TARGET_DB
username = $DB_USER
password = $DB_PASSWORD
hostport = 3306
prefix = fa_
charset = utf8mb4
EOF

echo -e "${GREEN}✓${NC} .env 配置已更新"

echo ""
echo "========================================="
echo "完成！"
echo "========================================="
echo ""
echo "数据库已切换到: $TARGET_DB"
echo ""
echo "下一步："
echo "1. 启动项目测试:"
echo "   bash start-server.sh"
echo ""
echo "2. 访问后台:"
echo "   http://localhost:8080/admin"
echo ""
echo "3. 使用数据库中的管理员账号登录"
echo ""
