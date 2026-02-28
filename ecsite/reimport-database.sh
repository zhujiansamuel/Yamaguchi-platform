#!/bin/bash

# 数据库清理并重新导入脚本

echo "========================================="
echo "数据库清理并重新导入"
echo "========================================="
echo ""

# 配置
DB_NAME="fastadmin"
DB_USER="root"
DB_HOST="127.0.0.1"
DB_PORT="3306"

# 颜色
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 获取 SQL 文件路径
if [ -n "$1" ]; then
    SQL_FILE="$1"
else
    echo "请提供 SQL 文件路径："
    read -p "SQL 文件: " SQL_FILE
fi

# 移除引号
SQL_FILE=$(echo "$SQL_FILE" | tr -d '"' | tr -d "'")

# 检查文件是否存在
if [ ! -f "$SQL_FILE" ]; then
    echo -e "${RED}✗${NC} SQL 文件不存在: $SQL_FILE"
    exit 1
fi

echo -e "${GREEN}✓${NC} 找到 SQL 文件: $SQL_FILE"
echo ""

# 获取密码
read -s -p "请输入 MySQL root 密码: " DB_PASSWORD
echo ""
echo ""

# 测试连接
echo "测试数据库连接..."
mysql -h "$DB_HOST" -P "$DB_PORT" -u "$DB_USER" -p"$DB_PASSWORD" -e "SELECT 1;" 2>/dev/null >/dev/null

if [ $? -ne 0 ]; then
    echo -e "${RED}✗${NC} 数据库连接失败，请检查密码"
    exit 1
fi

echo -e "${GREEN}✓${NC} 数据库连接成功"
echo ""

# 显示当前表
echo "当前数据库中的表："
TABLE_COUNT=$(mysql -h "$DB_HOST" -P "$DB_PORT" -u "$DB_USER" -p"$DB_PASSWORD" "$DB_NAME" -se "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = '$DB_NAME';" 2>/dev/null)

if [ "$TABLE_COUNT" -gt 0 ]; then
    echo -e "${YELLOW}!${NC} 数据库 '$DB_NAME' 中已有 $TABLE_COUNT 个表"
    mysql -h "$DB_HOST" -P "$DB_PORT" -u "$DB_USER" -p"$DB_PASSWORD" "$DB_NAME" -e "SHOW TABLES;" 2>/dev/null
else
    echo -e "${GREEN}✓${NC} 数据库 '$DB_NAME' 为空"
fi

echo ""

# 询问是否继续
echo "选择操作方式："
echo "1. 删除所有表后重新导入（推荐）"
echo "2. 强制导入（可能导致数据不一致）"
echo "3. 删除数据库后重建并导入（最干净）"
echo "4. 取消"
echo ""
read -p "请选择 (1-4): " CHOICE

case $CHOICE in
    1)
        echo ""
        echo "方式 1: 删除所有表后重新导入"
        echo "-----------------------------------------"

        if [ "$TABLE_COUNT" -gt 0 ]; then
            echo "正在删除所有表..."

            # 禁用外键检查
            mysql -h "$DB_HOST" -P "$DB_PORT" -u "$DB_USER" -p"$DB_PASSWORD" "$DB_NAME" -e "SET FOREIGN_KEY_CHECKS = 0;" 2>/dev/null

            # 获取所有表名并删除
            TABLES=$(mysql -h "$DB_HOST" -P "$DB_PORT" -u "$DB_USER" -p"$DB_PASSWORD" "$DB_NAME" -se "SHOW TABLES;" 2>/dev/null)

            for table in $TABLES; do
                echo "  删除表: $table"
                mysql -h "$DB_HOST" -P "$DB_PORT" -u "$DB_USER" -p"$DB_PASSWORD" "$DB_NAME" -e "DROP TABLE IF EXISTS \`$table\`;" 2>/dev/null
            done

            # 启用外键检查
            mysql -h "$DB_HOST" -P "$DB_PORT" -u "$DB_USER" -p"$DB_PASSWORD" "$DB_NAME" -e "SET FOREIGN_KEY_CHECKS = 1;" 2>/dev/null

            echo -e "${GREEN}✓${NC} 所有表已删除"
        fi

        echo ""
        echo "开始导入 SQL 文件..."
        mysql -h "$DB_HOST" -P "$DB_PORT" -u "$DB_USER" -p"$DB_PASSWORD" "$DB_NAME" < "$SQL_FILE" 2>&1

        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✓${NC} SQL 导入成功！"
        else
            echo -e "${RED}✗${NC} SQL 导入失败"
            exit 1
        fi
        ;;

    2)
        echo ""
        echo "方式 2: 强制导入"
        echo "-----------------------------------------"
        echo -e "${YELLOW}警告: 这可能导致数据不一致${NC}"
        echo ""

        mysql -h "$DB_HOST" -P "$DB_PORT" -u "$DB_USER" -p"$DB_PASSWORD" "$DB_NAME" --force < "$SQL_FILE" 2>&1 | grep -v "ERROR 1050"

        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✓${NC} SQL 导入完成（可能有警告）"
        else
            echo -e "${RED}✗${NC} SQL 导入失败"
            exit 1
        fi
        ;;

    3)
        echo ""
        echo "方式 3: 删除数据库后重建"
        echo "-----------------------------------------"
        echo -e "${RED}警告: 这将删除整个数据库！${NC}"
        echo ""
        read -p "确认删除数据库 '$DB_NAME'? (输入 YES 确认): " CONFIRM

        if [ "$CONFIRM" != "YES" ]; then
            echo "已取消"
            exit 0
        fi

        echo "删除数据库..."
        mysql -h "$DB_HOST" -P "$DB_PORT" -u "$DB_USER" -p"$DB_PASSWORD" -e "DROP DATABASE IF EXISTS \`$DB_NAME\`;" 2>/dev/null

        echo "创建数据库..."
        mysql -h "$DB_HOST" -P "$DB_PORT" -u "$DB_USER" -p"$DB_PASSWORD" -e "CREATE DATABASE \`$DB_NAME\` CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;" 2>/dev/null

        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✓${NC} 数据库已重建"
        else
            echo -e "${RED}✗${NC} 数据库创建失败"
            exit 1
        fi

        echo ""
        echo "开始导入 SQL 文件..."
        mysql -h "$DB_HOST" -P "$DB_PORT" -u "$DB_USER" -p"$DB_PASSWORD" "$DB_NAME" < "$SQL_FILE" 2>&1

        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✓${NC} SQL 导入成功！"
        else
            echo -e "${RED}✗${NC} SQL 导入失败"
            exit 1
        fi
        ;;

    4)
        echo "已取消"
        exit 0
        ;;

    *)
        echo -e "${RED}无效选项${NC}"
        exit 1
        ;;
esac

# 验证导入结果
echo ""
echo "========================================="
echo "验证导入结果"
echo "========================================="
echo ""

# 统计表数量
NEW_TABLE_COUNT=$(mysql -h "$DB_HOST" -P "$DB_PORT" -u "$DB_USER" -p"$DB_PASSWORD" "$DB_NAME" -se "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = '$DB_NAME';" 2>/dev/null)

echo -e "${GREEN}✓${NC} 数据库现有 $NEW_TABLE_COUNT 个表"
echo ""

# 检查关键表
echo "检查关键表："
CRITICAL_TABLES=("fa_admin" "fa_category" "fa_config" "fa_attachment")

for table in "${CRITICAL_TABLES[@]}"; do
    EXISTS=$(mysql -h "$DB_HOST" -P "$DB_PORT" -u "$DB_USER" -p"$DB_PASSWORD" "$DB_NAME" -se "SHOW TABLES LIKE '$table';" 2>/dev/null)
    if [ -n "$EXISTS" ]; then
        COUNT=$(mysql -h "$DB_HOST" -P "$DB_PORT" -u "$DB_USER" -p"$DB_PASSWORD" "$DB_NAME" -se "SELECT COUNT(*) FROM \`$table\`;" 2>/dev/null)
        echo -e "${GREEN}✓${NC} $table: $COUNT 条记录"
    else
        echo -e "${RED}✗${NC} $table: 不存在"
    fi
done

echo ""
echo "========================================="
echo "完成！"
echo "========================================="
echo ""
echo "现在可以启动项目测试："
echo "  bash start-server.sh"
echo ""
echo "访问后台："
echo "  http://localhost:8080/admin"
echo ""
