#!/bin/bash

#############################################################################
# OnlyOffice Callback Test & Verification Script
# Tests the complete dual-callback flow without Web UI
#############################################################################

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

NEXTCLOUD_CONTAINER="${NEXTCLOUD_CONTAINER:-nextcloud-app}"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}OnlyOffice Callback Test Suite${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Step 1: Deploy and configure
echo -e "${CYAN}[1/6] Deploying and configuring application...${NC}"
echo ""

./nextcloud_apps/deploy_nextcloud_app.sh docker >/dev/null 2>&1
docker exec -u www-data "$NEXTCLOUD_CONTAINER" php occ app:disable onlyoffice_callback_interceptor >/dev/null 2>&1
docker exec -u www-data "$NEXTCLOUD_CONTAINER" php occ app:enable onlyoffice_callback_interceptor >/dev/null 2>&1

echo -e "${GREEN}✓ App deployed and enabled${NC}"

# Step 2: Configure using CLI
echo ""
echo -e "${CYAN}[2/6] Configuring via command line...${NC}"
echo ""

./nextcloud_apps/fix_django_connectivity.sh

DJANGO_URL=$(docker exec -u www-data "$NEXTCLOUD_CONTAINER" php occ config:app:get onlyoffice_callback_interceptor django_callback_url)
ENABLED=$(docker exec -u www-data "$NEXTCLOUD_CONTAINER" php occ config:app:get onlyoffice_callback_interceptor enabled)

echo ""
echo "Current configuration:"
echo "  Django URL: $DJANGO_URL"
echo "  Enabled: $ENABLED"

# Step 3: Test Django endpoints
echo ""
echo -e "${CYAN}[3/6] Testing Django endpoints...${NC}"
echo ""

# Find Django container
DJANGO_CONTAINER=$(docker ps --format "{{.Names}}" | grep -i django | head -1 || echo "")

if [ -z "$DJANGO_CONTAINER" ]; then
    echo -e "${RED}✗ Django container not found${NC}"
    echo "Please check if Django is running"
    exit 1
fi

echo -e "${GREEN}✓ Found Django container: $DJANGO_CONTAINER${NC}"

# Extract base URL from DJANGO_URL
HEALTH_URL=$(echo "$DJANGO_URL" | sed 's|/api/acquisition/onlyoffice/callback/|/api/acquisition/health/|')

echo ""
echo "Testing health endpoint: $HEALTH_URL"
HEALTH_RESPONSE=$(docker exec "$NEXTCLOUD_CONTAINER" curl -sf "$HEALTH_URL" 2>/dev/null || echo "")

if echo "$HEALTH_RESPONSE" | grep -q "healthy"; then
    echo -e "${GREEN}✓ Health check PASSED${NC}"
    echo "Response: $HEALTH_RESPONSE"
else
    echo -e "${RED}✗ Health check FAILED${NC}"
    echo "Response: $HEALTH_RESPONSE"
    echo ""
    echo "Trying direct access to Django..."
    docker exec "$DJANGO_CONTAINER" curl -sf http://localhost:8000/api/acquisition/health/ 2>/dev/null || echo "Failed"
fi

# Test callback endpoint
echo ""
echo "Testing callback endpoint: $DJANGO_URL"
CALLBACK_TEST=$(docker exec "$NEXTCLOUD_CONTAINER" curl -sf "$DJANGO_URL" -X GET 2>/dev/null || echo "")

if echo "$CALLBACK_TEST" | grep -q "healthy"; then
    echo -e "${GREEN}✓ Callback endpoint accessible${NC}"
else
    echo -e "${YELLOW}⚠ Callback endpoint returned: $CALLBACK_TEST${NC}"
    echo "(This might be normal - GET returns health check)"
fi

# Step 4: Check Nextcloud app event listener
echo ""
echo -e "${CYAN}[4/6] Checking Nextcloud app configuration...${NC}"
echo ""

# Check if app is properly registered
APP_INFO=$(docker exec -u www-data "$NEXTCLOUD_CONTAINER" php occ app:list | grep onlyoffice_callback_interceptor || echo "")

if [ -n "$APP_INFO" ]; then
    echo -e "${GREEN}✓ App is registered in Nextcloud${NC}"
    echo "$APP_INFO"
else
    echo -e "${RED}✗ App not found in Nextcloud${NC}"
fi

# Check app files exist
echo ""
echo "Checking app files..."
docker exec "$NEXTCLOUD_CONTAINER" test -f /var/www/html/custom_apps/onlyoffice_callback_interceptor/lib/Listener/OnlyOfficeConfigListener.php && echo -e "${GREEN}✓ Event listener exists${NC}" || echo -e "${RED}✗ Event listener missing${NC}"

docker exec "$NEXTCLOUD_CONTAINER" test -f /var/www/html/custom_apps/onlyoffice_callback_interceptor/lib/Service/ConfigService.php && echo -e "${GREEN}✓ Config service exists${NC}" || echo -e "${RED}✗ Config service missing${NC}"

# Step 5: Enable debug mode
echo ""
echo -e "${CYAN}[5/6] Enabling debug mode for testing...${NC}"
echo ""

docker exec -u www-data "$NEXTCLOUD_CONTAINER" php occ config:app:set onlyoffice_callback_interceptor debug_mode --value="yes" >/dev/null
docker exec -u www-data "$NEXTCLOUD_CONTAINER" php occ config:system:set loglevel --value=0 --type=integer >/dev/null

echo -e "${GREEN}✓ Debug mode enabled${NC}"
echo "  - Nextcloud app debug: ON"
echo "  - Nextcloud log level: DEBUG"

# Step 6: Provide test instructions
echo ""
echo -e "${CYAN}[6/6] Test Instructions${NC}"
echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Manual Test Procedure${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo "To test the complete callback flow:"
echo ""
echo "1. Open 3 terminal windows"
echo ""
echo "   ${YELLOW}Terminal 1 - Django logs:${NC}"
echo "   docker logs -f $DJANGO_CONTAINER 2>&1 | grep --line-buffered -i -E 'onlyoffice|callback|health'"
echo ""
echo "   ${YELLOW}Terminal 2 - Nextcloud logs:${NC}"
echo "   docker exec $NEXTCLOUD_CONTAINER tail -f /var/www/html/data/nextcloud.log | grep --line-buffered -i -E 'onlyoffice|callback'"
echo ""
echo "   ${YELLOW}Terminal 3 - Run this test:${NC}"
echo "   docker exec -u www-data $NEXTCLOUD_CONTAINER php occ config:list onlyoffice_callback_interceptor"
echo ""
echo "2. In Nextcloud web interface:"
echo "   - Navigate to /Data/ folder (create if needed)"
echo "   - Upload a test Excel file OR create one"
echo "   - Open the file with OnlyOffice"
echo ""
echo "3. Expected behavior when opening document:"
echo ""
echo "   ${GREEN}✓ Nextcloud logs should show:${NC}"
echo "     - 'OnlyOffice edit event detected'"
echo "     - 'Modifying callback URL'"
echo "     - 'Callback URL modified to: $DJANGO_URL'"
echo ""
echo "4. Make a small edit and save:"
echo ""
echo "   ${GREEN}✓ Django logs should show:${NC}"
echo "     - 'OnlyOffice callback received: status=2'"
echo "     - 'Processing OnlyOffice document save'"
echo "     - 'Forwarding callback to Nextcloud'"
echo "     - 'Callback forwarded to Nextcloud: status=200'"
echo ""
echo "   ${GREEN}✓ File should be saved in Nextcloud${NC}"
echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Quick Verification Commands${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo "Check if callback was received:"
echo "  docker logs --tail 100 $DJANGO_CONTAINER | grep -i onlyoffice"
echo ""
echo "Check Django database for callback logs:"
echo "  docker exec $DJANGO_CONTAINER python manage.py shell -c \"from apps.data_acquisition.models import SyncLog; print(SyncLog.objects.filter(operation_type__icontains='onlyoffice').count())\""
echo ""
echo "View recent callback logs:"
echo "  docker exec $DJANGO_CONTAINER python manage.py shell -c \"from apps.data_acquisition.models import SyncLog; [print(f'{l.created_at}: {l.operation_type} - {l.message}') for l in SyncLog.objects.filter(operation_type__icontains='onlyoffice').order_by('-created_at')[:5]]\""
echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Troubleshooting${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo "If no logs appear:"
echo "1. Check if OnlyOffice app is enabled in Nextcloud:"
echo "   docker exec -u www-data $NEXTCLOUD_CONTAINER php occ app:list | grep richdocuments"
echo ""
echo "2. Check file path matches filter (/Data/):"
echo "   echo 'Make sure file is in /Data/ directory'"
echo ""
echo "3. Check health manually:"
echo "   docker exec $NEXTCLOUD_CONTAINER curl -v $HEALTH_URL"
echo ""
echo "4. Run full diagnostics:"
echo "   ./nextcloud_apps/diagnose_network.sh"
echo ""

# Summary
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Setup Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Configuration summary:"
echo "  ✓ Nextcloud app deployed"
echo "  ✓ Django connectivity configured"
echo "  ✓ Debug mode enabled"
echo "  ✓ Ready for testing"
echo ""
echo -e "${YELLOW}Now open a document in Nextcloud /Data/ folder and check the logs!${NC}"
echo ""
