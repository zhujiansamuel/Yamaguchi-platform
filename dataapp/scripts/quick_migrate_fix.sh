#!/bin/bash

# ============================================================================
# Quick Migration Fix - Regenerate and apply migrations
# ============================================================================

set -e

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}============================================================================${NC}"
echo -e "${BLUE}  Quick Migration Fix${NC}"
echo -e "${BLUE}============================================================================${NC}"
echo ""

echo -e "${YELLOW}🔧 Step 1: Checking current migration status...${NC}"
docker compose exec django python manage.py showmigrations data_aggregation | tail -5

echo ""
echo -e "${YELLOW}🔧 Step 2: Detecting Django container UID...${NC}"
DJANGO_UID=$(docker compose exec django id -u 2>/dev/null || echo "999")
echo "Django container is running as UID: ${DJANGO_UID}"

echo ""
echo -e "${YELLOW}🔧 Step 3: Fixing permissions...${NC}"
docker compose exec -u root django chown -R ${DJANGO_UID}:${DJANGO_UID} /app/apps/

echo ""
echo -e "${YELLOW}🔧 Step 4: Generating new migrations (if needed)...${NC}"
docker compose exec django python manage.py makemigrations data_aggregation
docker compose exec django python manage.py makemigrations data_acquisition

echo ""
echo -e "${YELLOW}🔧 Step 5: Applying all migrations...${NC}"
docker compose exec django python manage.py migrate

echo ""
echo -e "${YELLOW}🔧 Step 6: Verifying official_accounts table exists...${NC}"
docker compose exec postgres psql -U postgres -d data_platform -c "\d official_accounts" | head -10

echo ""
echo -e "${GREEN}============================================================================${NC}"
echo -e "${GREEN}✅ Migration fix complete!${NC}"
echo -e "${GREEN}============================================================================${NC}"
echo ""
echo -e "${BLUE}You can now run: ${YELLOW}./generate_mock_data.sh --docker --count 20${NC}"
