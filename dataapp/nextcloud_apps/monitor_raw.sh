#!/bin/bash

#############################################################################
# Raw Log Monitor - No Filtering (For Debugging)
#############################################################################

RED='\033[0;31m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
NC='\033[0m'

NEXTCLOUD_DIR="/opt/docker/nextcloud"
DJANGO_CONTAINER=$(docker ps --format "{{.Names}}" | grep -i django | head -1 || echo "")

[ -z "$DJANGO_CONTAINER" ] && echo -e "${RED}✗ Django container not found${NC}" && exit 1
[ ! -d "$NEXTCLOUD_DIR" ] && echo -e "${RED}✗ Nextcloud directory not found${NC}" && exit 1

echo -e "${CYAN}实时监控所有日志（无过滤）${NC}"
echo -e "${GREEN}Django: $DJANGO_CONTAINER${NC}"
echo -e "${GREEN}Nextcloud: $NEXTCLOUD_DIR${NC}"
echo ""
echo "Ctrl+C 停止"
echo ""

# Monitor Django - ALL logs
(docker logs -f "$DJANGO_CONTAINER" 2>&1 | while IFS= read -r line; do
    echo -e "${CYAN}[DJANGO]${NC} $line"
done) &
DJANGO_PID=$!

# Monitor Nextcloud - ALL logs
(cd "$NEXTCLOUD_DIR" && docker compose logs -f app 2>&1 | while IFS= read -r line; do
    echo -e "${GREEN}[NEXTCLOUD]${NC} $line"
done) &
NEXTCLOUD_PID=$!

trap "kill $DJANGO_PID $NEXTCLOUD_PID 2>/dev/null; echo ''; echo '已停止'; exit 0" INT TERM
wait
