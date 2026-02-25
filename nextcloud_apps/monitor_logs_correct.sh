#!/bin/bash

#############################################################################
# OnlyOffice Callback Monitor (Simplified)
#############################################################################

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

NEXTCLOUD_DIR="/opt/docker/nextcloud"
DJANGO_CONTAINER=$(docker ps --format "{{.Names}}" | grep -i django | head -1 || echo "")

[ -z "$DJANGO_CONTAINER" ] && echo -e "${RED}✗ Django container not found${NC}" && exit 1
[ ! -d "$NEXTCLOUD_DIR" ] && echo -e "${RED}✗ Nextcloud directory not found${NC}" && exit 1

echo -e "${CYAN}监控 OnlyOffice 回调 (Ctrl+C 停止)${NC}"
echo ""

# Simplified Django log filter
filter_django() {
    while IFS= read -r line; do
        # Extract timestamp and message
        if echo "$line" | grep -qi "error\|failed\|exception\|unauthorized"; then
            echo -e "${RED}[错误]${NC} $line"
        elif echo "$line" | grep -qi "callback received.*status="; then
            # Extract status from callback
            status=$(echo "$line" | grep -oP 'status=\K[0-9]+' || echo "?")
            file=$(echo "$line" | grep -oP 'file=\K[^,\s]+' || echo "")
            echo -e "${GREEN}[回调] status=$status file=$file${NC}"
        elif echo "$line" | grep -qi "processing.*document save"; then
            echo -e "${GREEN}[处理] 保存文档${NC}"
        elif echo "$line" | grep -qi "forwarded.*nextcloud"; then
            echo -e "${CYAN}[转发] → Nextcloud${NC}"
        elif echo "$line" | grep -qi "health.*200"; then
            echo -e "${GREEN}[健康] OK${NC}"
        fi
    done
}

# Simplified Nextcloud log filter
filter_nextcloud() {
    while IFS= read -r line; do
        if echo "$line" | grep -qi "error\|failed"; then
            echo -e "${RED}[NC错误]${NC} $line"
        elif echo "$line" | grep -qi "callback url.*modified"; then
            echo -e "${GREEN}[拦截] URL已修改${NC}"
        elif echo "$line" | grep -qi "health check.*success"; then
            echo -e "${GREEN}[NC健康] OK${NC}"
        fi
    done
}

# Monitor with simplified filters
(docker logs -f "$DJANGO_CONTAINER" 2>&1 | \
    grep --line-buffered -i -E 'callback received|error|failed|processing.*save|forwarded|health.*200|unauthorized' | \
    filter_django) &
DJANGO_PID=$!

(cd "$NEXTCLOUD_DIR" && docker compose logs -f app 2>&1 | \
    grep --line-buffered -i -E 'callback url.*modified|error|failed|health check' | \
    filter_nextcloud) &
NEXTCLOUD_PID=$!

trap "kill $DJANGO_PID $NEXTCLOUD_PID 2>/dev/null; echo ''; echo '已停止'; exit 0" INT TERM
wait
