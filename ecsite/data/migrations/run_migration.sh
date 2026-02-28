#!/bin/bash
# 个人/法人双轨会员资料 - 数据库迁移执行脚本
# 从项目根目录 .env 读取数据库配置并执行迁移

cd "$(dirname "$0")/../.." || exit 1
ENV_FILE=".env"
SQL_FILE="data/migrations/personal_corporate_profile.sql"

if [ ! -f "$ENV_FILE" ]; then
    echo "错误: 未找到 $ENV_FILE，请先配置数据库连接。"
    exit 1
fi

if [ ! -f "$SQL_FILE" ]; then
    echo "错误: 未找到迁移文件 $SQL_FILE"
    exit 1
fi

# 从 .env 解析 [database] 配置
get_env() {
    awk '/\[database\]/{found=1;next} found && /^\[/{found=0} found' "$ENV_FILE" 2>/dev/null | grep -E "^\s*$1\s*=" | head -1 | sed 's/^[^=]*=\s*//' | sed 's/^ *//;s/ *$//'
}

hostname=$(get_env "hostname")
database=$(get_env "database")
username=$(get_env "username")
password=$(get_env "password")
hostport=$(get_env "hostport")

[ -z "$hostname" ] && hostname="127.0.0.1"
[ -z "$database" ] && database="fastadmin"
[ -z "$username" ] && username="root"
[ -z "$hostport" ] && hostport="3306"

echo "执行迁移: $SQL_FILE"
echo "连接: $username@$hostname:$hostport/$database"

if [ -n "$password" ]; then
    mysql -h "$hostname" -P "$hostport" -u "$username" -p"$password" "$database" < "$SQL_FILE"
else
    mysql -h "$hostname" -P "$hostport" -u "$username" -p "$database" < "$SQL_FILE"
fi

if [ $? -eq 0 ]; then
    echo "迁移完成。"
else
    echo "迁移失败，请检查数据库连接及 SQL 文件。"
    exit 1
fi
