#!/bin/bash

# 数据库强制重新导入脚本（处理重复建表问题）

echo "========================================="
echo "数据库强制重新导入（解决表重复问题）"
echo "========================================="
echo ""

# 颜色
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 配置
DB_NAME="fastadmin"
DB_USER="root"
DB_HOST="127.0.0.1"

# 获取 SQL 文件路径
if [ -n "$1" ]; then
    SQL_FILE="$1"
else
    echo "用法: bash $0 <sql_file_path>"
    echo ""
    read -p "请输入 SQL 文件路径: " SQL_FILE
fi

# 移除引号
SQL_FILE=$(echo "$SQL_FILE" | tr -d '"' | tr -d "'")

# 检查文件
if [ ! -f "$SQL_FILE" ]; then
    echo -e "${RED}✗${NC} SQL 文件不存在: $SQL_FILE"
    exit 1
fi

echo -e "${GREEN}✓${NC} 找到 SQL 文件: $SQL_FILE"
FILE_SIZE=$(ls -lh "$SQL_FILE" | awk '{print $5}')
echo "文件大小: $FILE_SIZE"
echo ""

# 获取密码
read -s -p "请输入 MySQL root 密码: " DB_PASSWORD
echo ""
echo ""

# 测试连接
mysql -h "$DB_HOST" -u "$DB_USER" -p"$DB_PASSWORD" -e "SELECT 1;" 2>/dev/null >/dev/null
if [ $? -ne 0 ]; then
    echo -e "${RED}✗${NC} 数据库连接失败"
    exit 1
fi
echo -e "${GREEN}✓${NC} 数据库连接成功"
echo ""

# 方案选择
echo "选择导入方案："
echo ""
echo "1. 完全删除数据库并重建（最彻底）"
echo "2. 删除所有表（保留数据库）"
echo "3. 使用 sed 处理 SQL 文件后导入（推荐用于有问题的 SQL）"
echo "4. 取消"
echo ""
read -p "请选择 (1-4): " METHOD

case $METHOD in
    1)
        echo ""
        echo "=== 方案 1: 完全删除数据库并重建 ==="
        echo ""

        # 先断开所有连接
        echo "断开所有数据库连接..."
        mysql -h "$DB_HOST" -u "$DB_USER" -p"$DB_PASSWORD" -e "
            SELECT CONCAT('KILL ', id, ';')
            FROM INFORMATION_SCHEMA.PROCESSLIST
            WHERE db = '$DB_NAME' AND id != CONNECTION_ID();
        " 2>/dev/null | grep KILL | mysql -h "$DB_HOST" -u "$DB_USER" -p"$DB_PASSWORD" 2>/dev/null

        # 删除数据库
        echo "删除数据库 '$DB_NAME'..."
        mysql -h "$DB_HOST" -u "$DB_USER" -p"$DB_PASSWORD" -e "DROP DATABASE IF EXISTS \`$DB_NAME\`;" 2>/dev/null

        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✓${NC} 数据库已删除"
        fi

        # 重建数据库
        echo "创建数据库 '$DB_NAME'..."
        mysql -h "$DB_HOST" -u "$DB_USER" -p"$DB_PASSWORD" -e "
            CREATE DATABASE \`$DB_NAME\`
            CHARACTER SET utf8mb4
            COLLATE utf8mb4_general_ci;
        " 2>/dev/null

        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✓${NC} 数据库已创建"
        else
            echo -e "${RED}✗${NC} 数据库创建失败"
            exit 1
        fi

        echo ""
        echo "开始导入 SQL 文件..."
        echo "（这可能需要一些时间，请耐心等待...）"
        echo ""

        mysql -h "$DB_HOST" -u "$DB_USER" -p"$DB_PASSWORD" "$DB_NAME" < "$SQL_FILE" 2>&1 | grep -v "Using a password" | grep ERROR

        if [ ${PIPESTATUS[0]} -eq 0 ]; then
            echo -e "${GREEN}✓${NC} SQL 导入成功！"
        else
            echo -e "${RED}✗${NC} SQL 导入失败，但数据库可能已部分导入"
            echo ""
            read -p "是否继续验证数据库? (y/n): " VERIFY
            if [[ ! $VERIFY =~ ^[Yy]$ ]]; then
                exit 1
            fi
        fi
        ;;

    2)
        echo ""
        echo "=== 方案 2: 删除所有表 ==="
        echo ""

        # 禁用外键检查并删除所有表
        echo "删除所有表..."

        mysql -h "$DB_HOST" -u "$DB_USER" -p"$DB_PASSWORD" "$DB_NAME" <<EOF 2>/dev/null
SET FOREIGN_KEY_CHECKS = 0;
SET @tables = NULL;
SELECT GROUP_CONCAT('\`', table_name, '\`') INTO @tables
  FROM information_schema.tables
  WHERE table_schema = '$DB_NAME';
SET @tables = CONCAT('DROP TABLE IF EXISTS ', @tables);
PREPARE stmt FROM @tables;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;
SET FOREIGN_KEY_CHECKS = 1;
EOF

        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✓${NC} 所有表已删除"
        fi

        echo ""
        echo "开始导入 SQL 文件..."
        mysql -h "$DB_HOST" -u "$DB_USER" -p"$DB_PASSWORD" "$DB_NAME" < "$SQL_FILE" 2>&1 | grep -v "Using a password" | grep ERROR

        if [ ${PIPESTATUS[0]} -eq 0 ]; then
            echo -e "${GREEN}✓${NC} SQL 导入成功！"
        else
            echo -e "${RED}✗${NC} SQL 导入失败"
            exit 1
        fi
        ;;

    3)
        echo ""
        echo "=== 方案 3: 处理 SQL 文件后导入 ==="
        echo ""

        TEMP_SQL="/tmp/fastadmin_processed_$(date +%Y%m%d_%H%M%S).sql"

        echo "处理 SQL 文件（添加 DROP TABLE IF EXISTS）..."

        # 在每个 CREATE TABLE 前添加 DROP TABLE IF EXISTS
        sed -E 's/CREATE TABLE `([^`]+)`/DROP TABLE IF EXISTS `\1`;\nCREATE TABLE `\1`/g' "$SQL_FILE" > "$TEMP_SQL"

        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✓${NC} SQL 文件已处理: $TEMP_SQL"
            PROCESSED_SIZE=$(ls -lh "$TEMP_SQL" | awk '{print $5}')
            echo "处理后大小: $PROCESSED_SIZE"
        else
            echo -e "${RED}✗${NC} SQL 文件处理失败"
            exit 1
        fi

        echo ""
        echo "删除数据库并重建..."
        mysql -h "$DB_HOST" -u "$DB_USER" -p"$DB_PASSWORD" <<EOF 2>/dev/null
DROP DATABASE IF EXISTS \`$DB_NAME\`;
CREATE DATABASE \`$DB_NAME\` CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
EOF

        echo ""
        echo "导入处理后的 SQL 文件..."
        mysql -h "$DB_HOST" -u "$DB_USER" -p"$DB_PASSWORD" "$DB_NAME" < "$TEMP_SQL" 2>&1 | grep -v "Using a password" | grep ERROR

        if [ ${PIPESTATUS[0]} -eq 0 ]; then
            echo -e "${GREEN}✓${NC} SQL 导入成功！"
            echo ""
            read -p "是否删除临时文件? (y/n): " DELETE_TEMP
            if [[ $DELETE_TEMP =~ ^[Yy]$ ]]; then
                rm -f "$TEMP_SQL"
                echo "临时文件已删除"
            else
                echo "临时文件保存在: $TEMP_SQL"
            fi
        else
            echo -e "${RED}✗${NC} SQL 导入失败"
            echo "临时文件保存在: $TEMP_SQL"
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

# 验证导入
echo ""
echo "========================================="
echo "验证导入结果"
echo "========================================="
echo ""

# 表数量
TABLE_COUNT=$(mysql -h "$DB_HOST" -u "$DB_USER" -p"$DB_PASSWORD" "$DB_NAME" -se "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = '$DB_NAME';" 2>/dev/null)

if [ -n "$TABLE_COUNT" ] && [ "$TABLE_COUNT" -gt 0 ]; then
    echo -e "${GREEN}✓${NC} 数据库包含 $TABLE_COUNT 个表"
else
    echo -e "${RED}✗${NC} 数据库为空或验证失败"
    exit 1
fi

# 检查关键表
echo ""
echo "检查关键表："
CRITICAL_TABLES=("fa_admin" "fa_category" "fa_config" "fa_attachment" "fa_auth_group" "fa_auth_rule")

for table in "${CRITICAL_TABLES[@]}"; do
    COUNT=$(mysql -h "$DB_HOST" -u "$DB_USER" -p"$DB_PASSWORD" "$DB_NAME" -se "SELECT COUNT(*) FROM \`$table\` 2>/dev/null" 2>/dev/null)
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓${NC} $table: $COUNT 条记录"
    else
        echo -e "${YELLOW}!${NC} $table: 不存在或为空"
    fi
done

# 显示管理员信息
echo ""
echo "管理员账号："
mysql -h "$DB_HOST" -u "$DB_USER" -p"$DB_PASSWORD" "$DB_NAME" -e "SELECT id, username, email, status FROM fa_admin LIMIT 5;" 2>/dev/null

echo ""
echo "========================================="
echo "完成！"
echo "========================================="
echo ""
echo "现在可以启动项目："
echo "  bash start-server.sh"
echo ""
echo "访问后台："
echo "  http://localhost:8080/admin"
echo ""
