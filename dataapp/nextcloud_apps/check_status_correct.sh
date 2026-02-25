#!/bin/bash

#############################################################################
# Quick Status Check (Corrected for docker-compose)
#############################################################################

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

NEXTCLOUD_DIR="/opt/docker/nextcloud"
APP_NAME="onlyoffice_callback_interceptor"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}OnlyOffice Callback System Status${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Find Django container
DJANGO_CONTAINER=$(docker ps --format "{{.Names}}" | grep -i django | head -1 || echo "")

# Check Nextcloud directory
if [ ! -d "$NEXTCLOUD_DIR" ]; then
    echo -e "${RED}✗ Nextcloud directory not found: $NEXTCLOUD_DIR${NC}"
    exit 1
fi

cd "$NEXTCLOUD_DIR"

# 1. Container Status
echo -e "${YELLOW}[1] Container Status${NC}"
echo ""

if docker compose ps | grep -q "Up"; then
    echo -e "  Nextcloud: ${GREEN}✓ Running${NC}"
else
    echo -e "  Nextcloud: ${RED}✗ Not running${NC}"
    echo "  Run: cd $NEXTCLOUD_DIR && docker compose up -d"
    exit 1
fi

if [ -n "$DJANGO_CONTAINER" ] && docker ps | grep -q "$DJANGO_CONTAINER"; then
    echo -e "  Django:    ${GREEN}✓ Running${NC} ($DJANGO_CONTAINER)"
else
    echo -e "  Django:    ${YELLOW}⚠ Not found${NC}"
    DJANGO_CONTAINER=""
fi

# 2. App Status
echo ""
echo -e "${YELLOW}[2] Nextcloud App Status${NC}"
echo ""

APP_STATUS=$(docker compose exec -T -u www-data app php occ app:list 2>/dev/null | grep "$APP_NAME" || echo "")

if echo "$APP_STATUS" | grep -q "$APP_NAME"; then
    echo -e "  App: ${GREEN}✓ Installed${NC}"

    ENABLED=$(docker compose exec -T -u www-data app php occ config:app:get "$APP_NAME" enabled 2>/dev/null)
    if [ "$ENABLED" = "yes" ]; then
        echo -e "  Enabled: ${GREEN}✓ Yes${NC}"
    else
        echo -e "  Enabled: ${YELLOW}⚠ No${NC}"
    fi
else
    echo -e "  App: ${RED}✗ Not installed${NC}"
fi

# 3. Configuration
echo ""
echo -e "${YELLOW}[3] Configuration${NC}"
echo ""

DJANGO_URL=$(docker compose exec -T -u www-data app php occ config:app:get "$APP_NAME" django_callback_url 2>/dev/null)
HEALTH_URL=$(docker compose exec -T -u www-data app php occ config:app:get "$APP_NAME" health_check_url 2>/dev/null)
PATH_FILTER=$(docker compose exec -T -u www-data app php occ config:app:get "$APP_NAME" path_filter 2>/dev/null)
DEBUG_MODE=$(docker compose exec -T -u www-data app php occ config:app:get "$APP_NAME" debug_mode 2>/dev/null)

echo "  Django Callback URL: ${DJANGO_URL:-not set}"
echo "  Health Check URL:    ${HEALTH_URL:-not set}"
echo "  Path Filter:         ${PATH_FILTER:-not set}"
echo "  Debug Mode:          ${DEBUG_MODE:-not set}"

# 4. Connectivity Test
echo ""
echo -e "${YELLOW}[4] Connectivity Test${NC}"
echo ""

if [ -n "$HEALTH_URL" ]; then
    HEALTH_RESPONSE=$(docker compose exec -T app curl -sf "$HEALTH_URL" 2>/dev/null || echo "")

    if echo "$HEALTH_RESPONSE" | grep -q "healthy"; then
        echo -e "  Django Health Check: ${GREEN}✓ PASSED${NC}"
    else
        echo -e "  Django Health Check: ${RED}✗ FAILED${NC}"
        echo "  Response: ${HEALTH_RESPONSE:-no response}"
    fi
else
    echo -e "  Django Health Check: ${YELLOW}⚠ Not configured${NC}"
fi

# 5. Recent Activity
echo ""
echo -e "${YELLOW}[5] Recent Callback Activity${NC}"
echo ""

if [ -n "$DJANGO_CONTAINER" ]; then
    CALLBACK_COUNT=$(docker exec "$DJANGO_CONTAINER" python manage.py shell -c "
from apps.data_acquisition.models import SyncLog
try:
    count = SyncLog.objects.filter(operation_type__icontains='onlyoffice').count()
    print(count)
except:
    print(0)
" 2>/dev/null || echo "0")

    echo "  Total OnlyOffice callbacks: ${CALLBACK_COUNT}"

    if [ "$CALLBACK_COUNT" -gt 0 ]; then
        echo ""
        echo "  Recent callbacks:"
        docker exec "$DJANGO_CONTAINER" python manage.py shell -c "
from apps.data_acquisition.models import SyncLog
try:
    logs = SyncLog.objects.filter(operation_type__icontains='onlyoffice').order_by('-created_at')[:5]
    for log in logs:
        status = '✓' if log.success else '✗'
        print(f'    {status} {log.created_at.strftime(\"%Y-%m-%d %H:%M:%S\")} - {log.operation_type}')
except Exception as e:
    print(f'    Error: {e}')
" 2>/dev/null || echo "    Unable to read logs"
    else
        echo "  No callbacks recorded yet"
    fi
else
    echo "  Django container not available"
fi

# 6. Recommendations
echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Quick Actions${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

ALL_OK=true

if [ -z "$DJANGO_CONTAINER" ]; then
    echo -e "${YELLOW}⚠ Start Django container${NC}"
    ALL_OK=false
fi

if [ "$ENABLED" != "yes" ] || [ -z "$DJANGO_URL" ]; then
    echo -e "${YELLOW}⚠ Configure the app:${NC}"
    echo "  cd ~/Data-consolidation"
    echo "  ./nextcloud_apps/fix_config_correct.sh"
    ALL_OK=false
fi

if [ "$PATH_FILTER" != "/data_platform/" ]; then
    echo -e "${YELLOW}⚠ Path filter should be /data_platform/${NC}"
    echo "  Current: $PATH_FILTER"
    ALL_OK=false
fi

if ! echo "$HEALTH_RESPONSE" | grep -q "healthy" 2>/dev/null; then
    echo -e "${YELLOW}⚠ Fix Django connectivity${NC}"
    ALL_OK=false
fi

if $ALL_OK; then
    echo -e "${GREEN}✓ System is ready!${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Create /data_platform/ folder in Nextcloud"
    echo "2. Upload an Excel file"
    echo "3. Monitor logs:"
    echo "   cd ~/Data-consolidation"
    echo "   ./nextcloud_apps/monitor_logs_correct.sh"
fi

echo ""
