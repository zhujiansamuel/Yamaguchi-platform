#!/bin/bash

#############################################################################
# Quick Fix Script for Django Connectivity
#############################################################################

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Django Connectivity Quick Fix${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

NEXTCLOUD_CONTAINER="${NEXTCLOUD_CONTAINER:-nextcloud-app}"

echo -e "${YELLOW}Testing different Django URLs...${NC}"
echo ""

# Find Django container
DJANGO_CONTAINER=$(docker ps --format "{{.Names}}" | grep -i django | head -1 || echo "")
if [ -z "$DJANGO_CONTAINER" ]; then
    echo -e "${RED}✗ Django container not found${NC}"
    echo "Please set DJANGO_CONTAINER environment variable"
    exit 1
fi

echo -e "${GREEN}Found Django container: $DJANGO_CONTAINER${NC}"

# Get Django IP
DJANGO_IP=$(docker inspect -f '{{range.NetworkSettings.Networks}}{{.IPAddress}}{{end}}' "$DJANGO_CONTAINER")
echo -e "${GREEN}Django IP: $DJANGO_IP${NC}"
echo ""

# Test different URLs
declare -A URLS=(
    ["Container Name"]="http://$DJANGO_CONTAINER:8000"
    ["Container IP"]="http://$DJANGO_IP:8000"
    ["Hostname"]="http://data.yamaguchi.lan"
)

WORKING_URL=""

for name in "${!URLS[@]}"; do
    url="${URLS[$name]}"
    echo -n "Testing $name ($url)... "

    if docker exec "$NEXTCLOUD_CONTAINER" curl -sf "$url/api/acquisition/health/" >/dev/null 2>&1; then
        echo -e "${GREEN}✓ Works!${NC}"
        WORKING_URL="$url"
        break
    else
        echo -e "${RED}✗ Failed${NC}"
    fi
done

echo ""

if [ -n "$WORKING_URL" ]; then
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}Found working URL: $WORKING_URL${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
    echo "Updating Nextcloud app configuration..."

    # Update configuration
    docker exec -u www-data "$NEXTCLOUD_CONTAINER" php occ config:app:set onlyoffice_callback_interceptor django_callback_url --value="$WORKING_URL/api/acquisition/onlyoffice/callback/"

    docker exec -u www-data "$NEXTCLOUD_CONTAINER" php occ config:app:set onlyoffice_callback_interceptor health_check_url --value="$WORKING_URL/api/acquisition/health/"

    echo ""
    echo -e "${GREEN}✓ Configuration updated!${NC}"
    echo ""

    # Test again
    echo "Testing health check..."
    docker exec "$NEXTCLOUD_CONTAINER" curl -s "$WORKING_URL/api/acquisition/health/" | head -5

    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}Success!${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
    echo "Django Callback URL: $WORKING_URL/api/acquisition/onlyoffice/callback/"
    echo "Health Check URL: $WORKING_URL/api/acquisition/health/"
    echo ""
    echo "You can now test by opening an Excel file in /Data/ directory"

else
    echo -e "${RED}========================================${NC}"
    echo -e "${RED}No working URL found${NC}"
    echo -e "${RED}========================================${NC}"
    echo ""
    echo "Django is not accessible from Nextcloud container"
    echo ""
    echo "Possible solutions:"
    echo ""
    echo "1. Check if Django is running:"
    echo "   docker ps | grep django"
    echo "   docker logs $DJANGO_CONTAINER"
    echo ""
    echo "2. Restart Django container:"
    echo "   docker restart $DJANGO_CONTAINER"
    echo ""
    echo "3. Check Django is listening on correct port:"
    echo "   docker exec $DJANGO_CONTAINER netstat -tlnp | grep 8000"
    echo ""
    echo "4. Check docker-compose.yml network settings"
    echo ""
    echo "5. Run full diagnostics:"
    echo "   ./nextcloud_apps/diagnose_network.sh"
fi

echo ""
