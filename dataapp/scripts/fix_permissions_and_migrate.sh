#!/bin/bash

# ============================================================================
# Fix Permissions and Generate Migrations
# ============================================================================
# This script fixes file permissions in Docker and generates migrations
# ============================================================================

set -e

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}============================================================================${NC}"
echo -e "${BLUE}  Fix Permissions and Generate Migrations${NC}"
echo -e "${BLUE}============================================================================${NC}"
echo ""

echo -e "${YELLOW}🔧 Step 1: Detecting Django container user...${NC}"
echo ""

# Detect the user ID running in Django container
DJANGO_UID=$(docker compose exec django id -u 2>/dev/null || echo "999")
echo "Django container is running as UID: ${DJANGO_UID}"

echo ""
echo -e "${YELLOW}🔧 Step 2: Fixing file permissions...${NC}"
echo ""

# Fix permissions for migrations directories
echo "Fixing data_aggregation migrations directory..."
docker compose exec -u root django chown -R ${DJANGO_UID}:${DJANGO_UID} /app/apps/data_aggregation/migrations/

echo "Fixing data_acquisition migrations directory..."
docker compose exec -u root django chown -R ${DJANGO_UID}:${DJANGO_UID} /app/apps/data_acquisition/migrations/

# Also fix the entire app directories to prevent future issues
echo "Fixing app directories permissions..."
docker compose exec -u root django chown -R ${DJANGO_UID}:${DJANGO_UID} /app/apps/ || true

echo ""
echo -e "${GREEN}✅ Permissions fixed for UID ${DJANGO_UID}!${NC}"
echo ""

echo -e "${YELLOW}🔧 Step 3: Generating migrations for data_aggregation...${NC}"
docker compose exec django python manage.py makemigrations data_aggregation

echo ""
echo -e "${YELLOW}🔧 Step 4: Generating migrations for data_acquisition...${NC}"
docker compose exec django python manage.py makemigrations data_acquisition

echo ""
echo -e "${YELLOW}🔧 Step 5: Running all migrations...${NC}"
docker compose exec django python manage.py migrate

echo ""
echo -e "${GREEN}============================================================================${NC}"
echo -e "${GREEN}✅ All done! Checking migration status...${NC}"
echo -e "${GREEN}============================================================================${NC}"
echo ""

docker compose exec django python manage.py showmigrations data_aggregation data_acquisition

echo ""
echo -e "${BLUE}🎯 Next steps:${NC}"
echo -e "${BLUE}  1. Refresh your Django Admin page${NC}"
echo -e "${BLUE}  2. Generate mock data: ${YELLOW}./generate_mock_data.sh --docker --count 20${NC}"
echo -e "${BLUE}  3. Access admin: ${YELLOW}https://data.yamaguchi.lan/admin/${NC}"
