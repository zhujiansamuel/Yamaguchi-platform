#!/bin/bash

#############################################################################
# Network Diagnostics Script
# Tests connectivity between Nextcloud and Django containers
#############################################################################

set -e

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Network Diagnostics${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Container names
NEXTCLOUD_CONTAINER="${NEXTCLOUD_CONTAINER:-nextcloud-app}"
DJANGO_CONTAINER="${DJANGO_CONTAINER:-data-platform-django}"

echo -e "${YELLOW}Step 1: Checking container status...${NC}"
echo ""

# Check if containers are running
if docker ps | grep -q "$NEXTCLOUD_CONTAINER"; then
    echo -e "${GREEN}✓ Nextcloud container is running: $NEXTCLOUD_CONTAINER${NC}"
else
    echo -e "${RED}✗ Nextcloud container is NOT running: $NEXTCLOUD_CONTAINER${NC}"
    echo "Available containers:"
    docker ps --format "table {{.Names}}\t{{.Status}}"
    exit 1
fi

if docker ps | grep -q "$DJANGO_CONTAINER"; then
    echo -e "${GREEN}✓ Django container is running: $DJANGO_CONTAINER${NC}"
else
    echo -e "${YELLOW}⚠ Django container name might be different${NC}"
    echo "Looking for Django container..."
    DJANGO_CONTAINER=$(docker ps --format "{{.Names}}" | grep -i django | head -1 || echo "")
    if [ -n "$DJANGO_CONTAINER" ]; then
        echo -e "${GREEN}✓ Found Django container: $DJANGO_CONTAINER${NC}"
    else
        echo -e "${RED}✗ No Django container found${NC}"
        echo "Available containers:"
        docker ps --format "table {{.Names}}\t{{.Status}}"
        exit 1
    fi
fi

echo ""
echo -e "${YELLOW}Step 2: Checking networks...${NC}"
echo ""

# Get network information
NEXTCLOUD_NETWORK=$(docker inspect -f '{{range $k, $v := .NetworkSettings.Networks}}{{$k}} {{end}}' "$NEXTCLOUD_CONTAINER" | awk '{print $1}')
DJANGO_NETWORK=$(docker inspect -f '{{range $k, $v := .NetworkSettings.Networks}}{{$k}} {{end}}' "$DJANGO_CONTAINER" | awk '{print $1}')

echo "Nextcloud network: $NEXTCLOUD_NETWORK"
echo "Django network:    $DJANGO_NETWORK"

if [ "$NEXTCLOUD_NETWORK" = "$DJANGO_NETWORK" ]; then
    echo -e "${GREEN}✓ Containers are on the same network${NC}"
else
    echo -e "${YELLOW}⚠ Containers are on different networks${NC}"
    echo "This might cause connectivity issues"
fi

echo ""
echo -e "${YELLOW}Step 3: Getting container IP addresses...${NC}"
echo ""

# Get Django container IP
DJANGO_IP=$(docker inspect -f '{{range.NetworkSettings.Networks}}{{.IPAddress}}{{end}}' "$DJANGO_CONTAINER")
echo "Django IP: $DJANGO_IP"

# Get Nextcloud container IP
NEXTCLOUD_IP=$(docker inspect -f '{{range.NetworkSettings.Networks}}{{.IPAddress}}{{end}}' "$NEXTCLOUD_CONTAINER")
echo "Nextcloud IP: $NEXTCLOUD_IP"

echo ""
echo -e "${YELLOW}Step 4: Testing Django health endpoint from host...${NC}"
echo ""

# Test from host using container name (DNS)
echo "Test 1: From host using 'data.yamaguchi.lan'"
curl -v http://data.yamaguchi.lan/api/acquisition/health/ 2>&1 | head -20 || echo "Failed"

echo ""
echo "Test 2: From host using container IP ($DJANGO_IP)"
curl -v http://$DJANGO_IP:8000/api/acquisition/health/ 2>&1 | head -20 || echo "Failed"

echo ""
echo -e "${YELLOW}Step 5: Testing from Nextcloud container...${NC}"
echo ""

# Test 1: Using hostname
echo "Test 1: From Nextcloud using 'data.yamaguchi.lan'"
docker exec "$NEXTCLOUD_CONTAINER" curl -v http://data.yamaguchi.lan/api/acquisition/health/ 2>&1 | head -20 || echo "Failed"

echo ""
echo "Test 2: From Nextcloud using container name"
docker exec "$NEXTCLOUD_CONTAINER" curl -v http://$DJANGO_CONTAINER:8000/api/acquisition/health/ 2>&1 | head -20 || echo "Failed"

echo ""
echo "Test 3: From Nextcloud using container IP"
docker exec "$NEXTCLOUD_CONTAINER" curl -v http://$DJANGO_IP:8000/api/acquisition/health/ 2>&1 | head -20 || echo "Failed"

echo ""
echo "Test 4: DNS resolution from Nextcloud"
docker exec "$NEXTCLOUD_CONTAINER" nslookup data.yamaguchi.lan 2>&1 || echo "nslookup not available"
docker exec "$NEXTCLOUD_CONTAINER" getent hosts data.yamaguchi.lan 2>&1 || echo "getent not available"
docker exec "$NEXTCLOUD_CONTAINER" ping -c 2 data.yamaguchi.lan 2>&1 || echo "ping failed"

echo ""
echo -e "${YELLOW}Step 6: Checking Django service...${NC}"
echo ""

# Check if Django is listening
docker exec "$DJANGO_CONTAINER" netstat -tlnp 2>/dev/null | grep -E ":(8000|80)" || echo "netstat not available, trying ss..."
docker exec "$DJANGO_CONTAINER" ss -tlnp 2>/dev/null | grep -E ":(8000|80)" || echo "No port 8000/80 found"

echo ""
echo -e "${YELLOW}Step 7: Checking Django logs...${NC}"
echo ""
docker logs --tail 30 "$DJANGO_CONTAINER" | grep -i -E "error|warning|started|running|health" || echo "No relevant log entries found"

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Summary and Recommendations${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Determine the correct URL
if docker exec "$NEXTCLOUD_CONTAINER" curl -s http://$DJANGO_CONTAINER:8000/api/acquisition/health/ 2>&1 | grep -q "healthy"; then
    WORKING_URL="http://$DJANGO_CONTAINER:8000"
    echo -e "${GREEN}✓ Django is accessible via container name: $WORKING_URL${NC}"
    echo ""
    echo "Update Nextcloud app configuration:"
    echo "  docker exec -u www-data $NEXTCLOUD_CONTAINER php occ config:app:set onlyoffice_callback_interceptor django_callback_url --value=\"$WORKING_URL/api/acquisition/onlyoffice/callback/\""
    echo "  docker exec -u www-data $NEXTCLOUD_CONTAINER php occ config:app:set onlyoffice_callback_interceptor health_check_url --value=\"$WORKING_URL/api/acquisition/health/\""
elif docker exec "$NEXTCLOUD_CONTAINER" curl -s http://$DJANGO_IP:8000/api/acquisition/health/ 2>&1 | grep -q "healthy"; then
    WORKING_URL="http://$DJANGO_IP:8000"
    echo -e "${GREEN}✓ Django is accessible via IP: $WORKING_URL${NC}"
    echo ""
    echo "Update Nextcloud app configuration:"
    echo "  docker exec -u www-data $NEXTCLOUD_CONTAINER php occ config:app:set onlyoffice_callback_interceptor django_callback_url --value=\"$WORKING_URL/api/acquisition/onlyoffice/callback/\""
    echo "  docker exec -u www-data $NEXTCLOUD_CONTAINER php occ config:app:set onlyoffice_callback_interceptor health_check_url --value=\"$WORKING_URL/api/acquisition/health/\""
elif docker exec "$NEXTCLOUD_CONTAINER" curl -s http://data.yamaguchi.lan/api/acquisition/health/ 2>&1 | grep -q "healthy"; then
    WORKING_URL="http://data.yamaguchi.lan"
    echo -e "${GREEN}✓ Django is accessible via hostname: $WORKING_URL${NC}"
    echo "Current configuration should work!"
else
    echo -e "${RED}✗ Django is NOT accessible from Nextcloud container${NC}"
    echo ""
    echo "Possible issues:"
    echo "1. Django container is not running"
    echo "2. Django is not listening on the correct port"
    echo "3. Network isolation between containers"
    echo "4. DNS resolution issue for 'data.yamaguchi.lan'"
    echo ""
    echo "Recommended actions:"
    echo "1. Check if Django is running: docker logs $DJANGO_CONTAINER"
    echo "2. Verify Django port: docker port $DJANGO_CONTAINER"
    echo "3. Check docker-compose.yml network configuration"
    echo "4. Try using container name or IP instead of hostname"
fi

echo ""
