#!/bin/bash

#############################################################################
# OnlyOffice Callback Diagnostics
#############################################################################

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

NEXTCLOUD_DIR="/opt/docker/nextcloud"
APP_NAME="onlyoffice_callback_interceptor"

echo -e "${CYAN}=== OnlyOffice 回调诊断 ===${NC}"
echo ""

# 1. 检查应用是否安装
echo -e "${YELLOW}1. 检查应用安装状态${NC}"
cd "$NEXTCLOUD_DIR"
APP_STATUS=$(docker compose exec -T -u www-data app php occ app:list | grep -A5 "Enabled:" | grep "$APP_NAME" || echo "")
if [ -n "$APP_STATUS" ]; then
    echo -e "${GREEN}✓ 应用已启用${NC}"
else
    echo -e "${RED}✗ 应用未启用或未安装${NC}"
    echo "运行部署脚本: ./deploy_app_correct.sh"
    exit 1
fi
echo ""

# 2. 检查应用配置
echo -e "${YELLOW}2. 检查应用配置${NC}"
docker compose exec -T -u www-data app php occ config:app:get "$APP_NAME" enabled
docker compose exec -T -u www-data app php occ config:app:get "$APP_NAME" django_callback_url
docker compose exec -T -u www-data app php occ config:app:get "$APP_NAME" path_filter
docker compose exec -T -u www-data app php occ config:app:get "$APP_NAME" enable_health_check
echo ""

# 3. 检查最近的 Nextcloud 日志（无过滤）
echo -e "${YELLOW}3. Nextcloud 最近日志（最后 20 行）${NC}"
docker compose logs --tail=20 app 2>&1
echo ""

# 4. 检查 Django 日志（无过滤）
echo -e "${YELLOW}4. Django 最近日志（最后 20 行）${NC}"
DJANGO_CONTAINER=$(docker ps --format "{{.Names}}" | grep -i django | head -1)
if [ -n "$DJANGO_CONTAINER" ]; then
    docker logs --tail=20 "$DJANGO_CONTAINER" 2>&1
else
    echo -e "${RED}✗ Django 容器未找到${NC}"
fi
echo ""

# 5. 测试 Django 健康检查
echo -e "${YELLOW}5. 测试 Django 健康检查${NC}"
docker compose exec -T app curl -s http://data-platform-django:8000/api/acquisition/health/ || echo -e "${RED}✗ 无法连接 Django${NC}"
echo ""

# 6. 检查 OnlyOffice 应用是否安装
echo -e "${YELLOW}6. 检查 Nextcloud OnlyOffice 应用${NC}"
RICHDOCUMENTS=$(docker compose exec -T -u www-data app php occ app:list | grep "richdocuments" || echo "")
if [ -n "$RICHDOCUMENTS" ]; then
    echo -e "${GREEN}✓ richdocuments 已安装${NC}"
else
    echo -e "${RED}✗ richdocuments 未安装（OnlyOffice 集成需要）${NC}"
fi
echo ""

# 7. 提示下一步操作
echo -e "${CYAN}=== 诊断建议 ===${NC}"
echo ""
echo "如果应用已启用但没有日志输出："
echo "1. 确保编辑的文件在 /data_platform/ 目录下"
echo "2. 检查 Nextcloud 日志权限：docker compose exec app ls -la /var/www/html/data/"
echo "3. 启用调试模式：docker compose exec -u www-data app php occ config:app:set $APP_NAME debug_mode --value='1'"
echo "4. 清空日志后重试：docker compose exec app truncate -s 0 /var/log/nextcloud.log"
echo ""
echo "实时监控所有日志（无过滤）："
echo "  Django: docker logs -f $DJANGO_CONTAINER"
echo "  Nextcloud: cd $NEXTCLOUD_DIR && docker compose logs -f app"
echo ""
