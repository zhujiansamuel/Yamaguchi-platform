#!/bin/bash

#############################################################################
# OnlyOffice Callback Interceptor - Deployment & Configuration Script
# For docker-compose environment at /opt/docker/nextcloud
#############################################################################

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

APP_NAME="onlyoffice_callback_interceptor"
APP_SOURCE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/${APP_NAME}" && pwd)"
NEXTCLOUD_DIR="/opt/docker/nextcloud"
NEXTCLOUD_APPS_DIR="/var/www/html/custom_apps"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}OnlyOffice Callback Interceptor${NC}"
echo -e "${BLUE}Deployment & Configuration Script${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check source directory
if [ ! -d "$APP_SOURCE_DIR" ]; then
    echo -e "${RED}Error: App source directory not found: $APP_SOURCE_DIR${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Found app source directory${NC}"

# Check docker-compose directory
if [ ! -f "$NEXTCLOUD_DIR/docker-compose.yml" ]; then
    echo -e "${RED}Error: docker-compose.yml not found at $NEXTCLOUD_DIR${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Found docker-compose.yml${NC}"
echo ""

# Change to Nextcloud directory
cd "$NEXTCLOUD_DIR"

# Check if container is running
if ! docker compose ps | grep -q "Up"; then
    echo -e "${RED}Error: Nextcloud containers are not running${NC}"
    echo "Start them with: cd $NEXTCLOUD_DIR && docker compose up -d"
    exit 1
fi

echo -e "${GREEN}✓ Containers are running${NC}"
echo ""

# --- STEP 1: DEPLOY FILES ---
echo -e "${YELLOW}Step 1/3: Deploying app files...${NC}"

# Create a temp directory in container
docker compose exec -T app mkdir -p /tmp/onlyoffice_app_deploy

# Copy files (using tar to preserve structure)
tar -czf - -C "$(dirname "$APP_SOURCE_DIR")" "$APP_NAME" | \
    docker compose exec -T app tar -xzf - -C /tmp/onlyoffice_app_deploy/

# Move to custom_apps
docker compose exec -T app rm -rf "$NEXTCLOUD_APPS_DIR/$APP_NAME"
docker compose exec -T app mv "/tmp/onlyoffice_app_deploy/$APP_NAME" "$NEXTCLOUD_APPS_DIR/"
docker compose exec -T app rm -rf /tmp/onlyoffice_app_deploy

# Set permissions
docker compose exec -T app chown -R www-data:www-data "$NEXTCLOUD_APPS_DIR/$APP_NAME"

echo -e "${GREEN}✓ App files deployed and permissions set${NC}"
echo ""

# --- STEP 2: ENABLE APP ---
echo -e "${YELLOW}Step 2/3: Enabling app...${NC}"
docker compose exec -T -u www-data app php occ app:disable "$APP_NAME" 2>/dev/null || true
docker compose exec -T -u www-data app php occ app:enable "$APP_NAME"

echo -e "${GREEN}✓ App enabled${NC}"
echo ""

# --- STEP 3: CONFIGURE APP ---
echo -e "${YELLOW}Step 3/3: Configuring app settings...${NC}"

# 1. Set path filter (Primary folder)
# Note: Additional tracking paths are automatically monitored in ConfigService.php:
#   - official_website_redirect_to_yamato_tracking (prefix: OWRYT-)
#   - yamato_tracking_10 (prefix: YT10-)
#   - yamato_tracking (prefix: YTO-)
#   - yamato_tracking_only (prefix: YTO-)
#   - japan_post_tracking_only (prefix: JPTO-)
#   - japan_post_tracking (prefix: JPTO-)
#   - japan_post_tracking_10 (prefix: JPT10-)
docker compose exec -T -u www-data app php occ config:app:set $APP_NAME path_filter --value="/data_platform/"

# 2. Detect Django URL
DJANGO_CONTAINER=$(docker ps --format "{{.Names}}" | grep -i django | head -1 || echo "")
if [ -n "$DJANGO_CONTAINER" ]; then
    # Test container name connectivity
    if docker compose exec -T app curl -sf "http://$DJANGO_CONTAINER:8000/api/acquisition/health/" >/dev/null 2>&1; then
        DJANGO_URL="http://$DJANGO_CONTAINER:8000"
    elif docker compose exec -T app curl -sf "http://data.yamaguchi.lan/api/acquisition/health/" >/dev/null 2>&1; then
        DJANGO_URL="http://data.yamaguchi.lan"
    else
        DJANGO_URL="http://data.yamaguchi.lan"
    fi
else
    DJANGO_URL="http://data.yamaguchi.lan"
fi

# 3. Set Django URLs
docker compose exec -T -u www-data app php occ config:app:set $APP_NAME django_callback_url --value="$DJANGO_URL/api/acquisition/onlyoffice/callback/"
docker compose exec -T -u www-data app php occ config:app:set $APP_NAME health_check_url --value="$DJANGO_URL/api/acquisition/health/"

# 4. Set other defaults
docker compose exec -T -u www-data app php occ config:app:set $APP_NAME enabled --value="yes"
docker compose exec -T -u www-data app php occ config:app:set $APP_NAME onlyoffice_secret --value="tDCVy4C0oUPWjEXCvCZ4KnFe7N7z5V"
docker compose exec -T -u www-data app php occ config:app:set $APP_NAME include_user_metadata --value="yes"
docker compose exec -T -u www-data app php occ config:app:set $APP_NAME include_timestamp --value="yes"
docker compose exec -T -u www-data app php occ config:app:set $APP_NAME health_check_enabled --value="yes"
docker compose exec -T -u www-data app php occ config:app:set $APP_NAME health_check_interval --value="300"
docker compose exec -T -u www-data app php occ config:app:set $APP_NAME debug_mode --value="yes"

echo -e "${GREEN}✓ Configuration complete${NC}"
echo ""

# --- FINAL STATUS ---
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Deployment Summary${NC}"
echo -e "${BLUE}========================================${NC}"
echo "Django URL:   $DJANGO_URL"
echo "Path Filter:  /data_platform/ (Primary)"
echo ""
echo "Auto-Monitored Tracking Paths (Built-in):"
echo "  - official_website_redirect_to_yamato_tracking (prefix: OWRYT-)"
echo "  - yamato_tracking_10 (prefix: YT10-)"
echo "  - yamato_tracking (prefix: YTO-)"
echo "  - yamato_tracking_only (prefix: YTO-)"
echo "  - japan_post_tracking_only (prefix: JPTO-)"
echo "  - japan_post_tracking (prefix: JPTO-)"
echo "  - japan_post_tracking_10 (prefix: JPT10-)"
echo ""
echo -e "${GREEN}Deployment Successful!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
