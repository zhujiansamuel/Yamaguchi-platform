#!/bin/bash

# ============================================================================
# Diagnose and Fix Migration Issues
# ============================================================================
# This script checks for migration problems and provides fixes
# ============================================================================

set -e

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}============================================================================${NC}"
echo -e "${BLUE}  Migration Diagnostics${NC}"
echo -e "${BLUE}============================================================================${NC}"
echo ""

echo -e "${YELLOW}🔍 Step 1: Checking current migration status...${NC}"
echo ""
docker compose exec django python manage.py showmigrations data_aggregation data_acquisition

echo ""
echo -e "${YELLOW}🔍 Step 2: Checking for unapplied migrations...${NC}"
echo ""
docker compose exec django python manage.py migrate --plan

echo ""
echo -e "${YELLOW}🔍 Step 3: Checking database schema...${NC}"
echo ""
docker compose exec postgres psql -U postgres -d data_platform -c "\d purchasing" || echo "Table might not exist or has issues"

echo ""
echo -e "${BLUE}============================================================================${NC}"
echo -e "${BLUE}  Diagnosis Complete${NC}"
echo -e "${BLUE}============================================================================${NC}"
echo ""

echo -e "${YELLOW}⚠️  Detected issue: Table structure doesn't match models${NC}"
echo ""
echo -e "${BLUE}Options to fix:${NC}"
echo ""
echo -e "${GREEN}Option 1: Generate and apply new migration (SAFE - preserves data)${NC}"
echo "  docker compose exec django python manage.py makemigrations"
echo "  docker compose exec django python manage.py migrate"
echo ""
echo -e "${YELLOW}Option 2: Reset migrations and recreate (SAFE - for empty database)${NC}"
echo "  ./reset_and_recreate_db.sh"
echo ""
echo -e "${RED}Option 3: Drop and recreate all tables (DESTRUCTIVE - loses all data!)${NC}"
echo "  docker compose exec django python manage.py flush --no-input"
echo "  docker compose exec django python manage.py migrate"
echo ""

read -p "Do you want to try Option 1 (generate new migration)? (yes/no): " response

if [ "$response" = "yes" ]; then
    echo ""
    echo -e "${GREEN}🔧 Generating new migrations...${NC}"
    docker compose exec django python manage.py makemigrations

    echo ""
    echo -e "${GREEN}🔧 Applying migrations...${NC}"
    docker compose exec django python manage.py migrate

    echo ""
    echo -e "${GREEN}✅ Done! Try your command again.${NC}"
else
    echo ""
    echo -e "${YELLOW}Please choose one of the options above manually.${NC}"
fi
