#!/bin/bash
# 数据库迁移脚本
# 在容器外执行此脚本来运行 Django 迁移

set -e

# 容器名称（根据实际情况修改）
CONTAINER_NAME="${CONTAINER_NAME:-data-platform-django}"

echo "=== 检查容器状态 ==="
docker ps | grep -E "(data.*web|django)" || {
    echo "未找到运行中的容器，请设置 CONTAINER_NAME 环境变量"
    echo "用法: CONTAINER_NAME=your-container-name ./run_migrations.sh"
    exit 1
}

echo ""
echo "=== 显示待应用的迁移 ==="
docker exec "$CONTAINER_NAME" python manage.py showmigrations data_acquisition

echo ""
echo "=== 应用迁移 ==="
docker exec "$CONTAINER_NAME" python manage.py migrate data_acquisition

echo ""
echo "=== 迁移完成 ==="
docker exec "$CONTAINER_NAME" python manage.py showmigrations data_acquisition
