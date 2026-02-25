#!/bin/bash

# ============================================================================
# Try to Fix Schema Issues Without Data Loss
# ============================================================================
# This script attempts to fix schema mismatches by generating new migrations
# ============================================================================

set -e

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}============================================================================${NC}"
echo -e "${BLUE}  Fix Schema Issues (Safe - Preserves Data)${NC}"
echo -e "${BLUE}============================================================================${NC}"
echo ""

echo -e "${YELLOW}🔍 Checking current state...${NC}"
echo ""

echo "Current migrations:"
docker compose exec django python manage.py showmigrations data_aggregation data_acquisition

echo ""
echo -e "${YELLOW}🔧 Step 1: Detecting Django container UID...${NC}"
DJANGO_UID=$(docker compose exec django id -u 2>/dev/null || echo "999")
echo "Django container is running as UID: ${DJANGO_UID}"

echo ""
echo -e "${YELLOW}🔧 Step 2: Fixing permissions...${NC}"
docker compose exec -u root django chown -R ${DJANGO_UID}:${DJANGO_UID} /app/apps/

echo ""
echo -e "${YELLOW}🔧 Step 3: Checking for model changes...${NC}"
docker compose exec django python manage.py makemigrations --dry-run

echo ""
read -p "Generate new migrations to fix schema? (yes/no): " response

if [ "$response" = "yes" ]; then
    echo ""
    echo -e "${GREEN}🔧 Generating migrations...${NC}"
    docker compose exec django python manage.py makemigrations data_aggregation
    docker compose exec django python manage.py makemigrations data_acquisition

    echo ""
    echo -e "${GREEN}🔧 Applying migrations...${NC}"
    docker compose exec django python manage.py migrate

    echo ""
    echo -e "${GREEN}✅ Done! Schema should be fixed.${NC}"

    echo ""
    echo -e "${BLUE}🎯 Try your command again now.${NC}"
else
    echo ""
    echo -e "${YELLOW}No changes made.${NC}"
    echo ""
    echo -e "${BLUE}If the problem persists, you may need to:${NC}"
    echo -e "${BLUE}  1. Check what migrations exist in apps/*/migrations/${NC}"
    echo -e "${BLUE}  2. Run: ${YELLOW}./reset_and_recreate_db.sh${NC} ${RED}(WARNING: Deletes all data!)${NC}"
fi
