#!/bin/bash

# 从服务器导入数据库到本地

echo "========================================="
echo "FastAdmin 数据库导入工具"
echo "========================================="
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 本地数据库配置
LOCAL_HOST="127.0.0.1"
LOCAL_PORT="3306"
LOCAL_DB="fastadmin"
LOCAL_USER="root"

echo "请选择导入方式:"
echo "1. 从 SQL 文件导入（推荐）"
echo "2. 从服务器直接导入（需要 SSH）"
echo "3. 只查看本地数据库状态"
echo ""
read -p "请输入选项 (1-3): " IMPORT_METHOD

case $IMPORT_METHOD in
    1)
        echo ""
        echo "方式 1: 从 SQL 文件导入"
        echo "-----------------------------------------"
        echo ""

        # 列出可用的 SQL 文件
        echo "项目目录中的 SQL 文件:"
        find . -maxdepth 2 -name "*.sql" -type f 2>/dev/null | nl
        echo ""

        read -p "请输入 SQL 文件路径（或拖拽文件到终端）: " SQL_FILE

        # 移除可能的引号
        SQL_FILE=$(echo "$SQL_FILE" | tr -d '"' | tr -d "'")

        if [ ! -f "$SQL_FILE" ]; then
            echo -e "${RED}✗${NC} 文件不存在: $SQL_FILE"
            exit 1
        fi

        echo ""
        echo "文件信息:"
        ls -lh "$SQL_FILE"
        echo ""

        read -p "是否备份本地数据库? (y/n): " BACKUP_LOCAL

        if [[ $BACKUP_LOCAL =~ ^[Yy]$ ]]; then
            BACKUP_FILE="fastadmin_local_backup_$(date +%Y%m%d_%H%M%S).sql"
            echo "备份本地数据库到: $BACKUP_FILE"
            read -s -p "请输入本地 MySQL root 密码: " LOCAL_PASSWORD
            echo ""

            mysqldump -h "$LOCAL_HOST" -P "$LOCAL_PORT" -u "$LOCAL_USER" -p"$LOCAL_PASSWORD" "$LOCAL_DB" > "$BACKUP_FILE" 2>/dev/null

            if [ $? -eq 0 ]; then
                echo -e "${GREEN}✓${NC} 本地数据库已备份"
            else
                echo -e "${YELLOW}!${NC} 备份失败，但继续导入"
            fi
        fi

        echo ""
        read -s -p "请输入本地 MySQL root 密码: " LOCAL_PASSWORD
        echo ""
        echo ""

        echo "开始导入数据库..."
        mysql -h "$LOCAL_HOST" -P "$LOCAL_PORT" -u "$LOCAL_USER" -p"$LOCAL_PASSWORD" "$LOCAL_DB" < "$SQL_FILE" 2>/dev/null

        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✓${NC} 数据库导入成功！"
        else
            echo -e "${RED}✗${NC} 数据库导入失败"
            echo ""
            echo "请检查："
            echo "1. MySQL 密码是否正确"
            echo "2. 数据库 '$LOCAL_DB' 是否存在"
            echo "3. SQL 文件是否有效"
            exit 1
        fi
        ;;

    2)
        echo ""
        echo "方式 2: 从服务器直接导入"
        echo "-----------------------------------------"
        echo ""

        read -p "服务器地址 (如: user@example.com): " SERVER_HOST
        read -p "服务器 MySQL 用户名 (默认: root): " SERVER_USER
        SERVER_USER=${SERVER_USER:-root}
        read -p "服务器数据库名 (默认: fastadmin): " SERVER_DB
        SERVER_DB=${SERVER_DB:-fastadmin}

        TEMP_FILE="/tmp/server_fastadmin_$(date +%Y%m%d_%H%M%S).sql"

        echo ""
        echo "从服务器导出数据库..."
        echo "注意: 需要输入服务器 SSH 密码和 MySQL 密码"
        echo ""

        # 通过 SSH 导出并直接下载
        ssh "$SERVER_HOST" "mysqldump -u $SERVER_USER -p $SERVER_DB" > "$TEMP_FILE"

        if [ $? -eq 0 ] && [ -s "$TEMP_FILE" ]; then
            echo -e "${GREEN}✓${NC} 从服务器导出成功"
            echo ""

            read -s -p "请输入本地 MySQL root 密码: " LOCAL_PASSWORD
            echo ""
            echo ""

            echo "导入到本地数据库..."
            mysql -h "$LOCAL_HOST" -P "$LOCAL_PORT" -u "$LOCAL_USER" -p"$LOCAL_PASSWORD" "$LOCAL_DB" < "$TEMP_FILE" 2>/dev/null

            if [ $? -eq 0 ]; then
                echo -e "${GREEN}✓${NC} 数据库导入成功！"
                echo ""
                echo "临时文件已保存: $TEMP_FILE"
                read -p "是否删除临时文件? (y/n): " DELETE_TEMP
                if [[ $DELETE_TEMP =~ ^[Yy]$ ]]; then
                    rm -f "$TEMP_FILE"
                    echo "临时文件已删除"
                fi
            else
                echo -e "${RED}✗${NC} 数据库导入失败"
                exit 1
            fi
        else
            echo -e "${RED}✗${NC} 从服务器导出失败"
            rm -f "$TEMP_FILE"
            exit 1
        fi
        ;;

    3)
        echo ""
        echo "本地数据库状态"
        echo "-----------------------------------------"
        echo ""

        read -s -p "请输入本地 MySQL root 密码: " LOCAL_PASSWORD
        echo ""
        echo ""

        # 检查数据库是否存在
        DB_EXISTS=$(mysql -h "$LOCAL_HOST" -P "$LOCAL_PORT" -u "$LOCAL_USER" -p"$LOCAL_PASSWORD" -e "SHOW DATABASES LIKE '$LOCAL_DB';" 2>/dev/null | grep "$LOCAL_DB")

        if [ -z "$DB_EXISTS" ]; then
            echo -e "${RED}✗${NC} 数据库 '$LOCAL_DB' 不存在"
            exit 1
        fi

        echo -e "${GREEN}✓${NC} 数据库 '$LOCAL_DB' 存在"
        echo ""

        # 显示表列表
        echo "数据库表列表:"
        mysql -h "$LOCAL_HOST" -P "$LOCAL_PORT" -u "$LOCAL_USER" -p"$LOCAL_PASSWORD" "$LOCAL_DB" -e "SHOW TABLES;" 2>/dev/null

        echo ""

        # 显示表统计
        echo "表数据统计:"
        mysql -h "$LOCAL_HOST" -P "$LOCAL_PORT" -u "$LOCAL_USER" -p"$LOCAL_PASSWORD" "$LOCAL_DB" <<EOF 2>/dev/null
SELECT
    table_name AS '表名',
    table_rows AS '行数',
    ROUND(((data_length + index_length) / 1024 / 1024), 2) AS '大小(MB)'
FROM information_schema.TABLES
WHERE table_schema = '$LOCAL_DB'
ORDER BY table_rows DESC
LIMIT 10;
EOF

        echo ""

        # 检查关键表
        echo "检查关键表:"
        TABLES=("fa_admin" "fa_category" "fa_config" "fa_attachment")

        for table in "${TABLES[@]}"; do
            COUNT=$(mysql -h "$LOCAL_HOST" -P "$LOCAL_PORT" -u "$LOCAL_USER" -p"$LOCAL_PASSWORD" "$LOCAL_DB" -se "SELECT COUNT(*) FROM $table;" 2>/dev/null)
            if [ $? -eq 0 ]; then
                echo -e "${GREEN}✓${NC} $table: $COUNT 条记录"
            else
                echo -e "${RED}✗${NC} $table: 不存在或无法访问"
            fi
        done

        exit 0
        ;;

    *)
        echo -e "${RED}无效的选项${NC}"
        exit 1
        ;;
esac

# 验证导入结果
echo ""
echo "========================================="
echo "验证导入结果"
echo "========================================="
echo ""

read -s -p "请输入本地 MySQL root 密码以验证: " LOCAL_PASSWORD
echo ""
echo ""

# 检查表数量
TABLE_COUNT=$(mysql -h "$LOCAL_HOST" -P "$LOCAL_PORT" -u "$LOCAL_USER" -p"$LOCAL_PASSWORD" "$LOCAL_DB" -se "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = '$LOCAL_DB';" 2>/dev/null)

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓${NC} 数据库包含 $TABLE_COUNT 个表"
else
    echo -e "${RED}✗${NC} 无法验证数据库"
    exit 1
fi

# 检查管理员账号
echo ""
echo "管理员账号信息:"
mysql -h "$LOCAL_HOST" -P "$LOCAL_PORT" -u "$LOCAL_USER" -p"$LOCAL_PASSWORD" "$LOCAL_DB" -e "SELECT id, username, email, status FROM fa_admin;" 2>/dev/null

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
echo "使用服务器的管理员账号密码登录"
echo ""
