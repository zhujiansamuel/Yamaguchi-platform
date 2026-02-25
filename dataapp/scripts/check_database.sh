#!/bin/bash

# ============================================================================
# Quick Database Check Script
# ============================================================================
# Checks migration status and database tables
# ============================================================================

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}============================================================================${NC}"
echo -e "${BLUE}  Database Status Check${NC}"
echo -e "${BLUE}============================================================================${NC}"
echo ""

echo -e "${YELLOW}🔍 Step 1: Checking migration files exist...${NC}"
echo "data_aggregation migrations:"
ls -la apps/data_aggregation/migrations/*.py 2>/dev/null | grep -v __pycache__ || echo "No migration files found!"

echo ""
echo "data_acquisition migrations:"
ls -la apps/data_acquisition/migrations/*.py 2>/dev/null | grep -v __pycache__ || echo "No migration files found!"

echo ""
echo -e "${YELLOW}🔍 Step 2: Checking migration status in database...${NC}"
docker compose exec django python manage.py showmigrations data_aggregation data_acquisition

echo ""
echo -e "${YELLOW}🔍 Step 3: Checking what tables exist...${NC}"
docker compose exec postgres psql -U postgres -d data_platform -c "\dt" | head -50

echo ""
echo -e "${YELLOW}🔍 Step 4: Checking specific tables...${NC}"
echo "Checking iphones table:"
docker compose exec postgres psql -U postgres -d data_platform -c "\d iphones" 2>&1 | head -10

echo ""
echo "Checking official_accounts table:"
docker compose exec postgres psql -U postgres -d data_platform -c "\d official_accounts" 2>&1 | head -10

echo ""
echo -e "${BLUE}============================================================================${NC}"
echo -e "${BLUE}  Analysis${NC}"
echo -e "${BLUE}============================================================================${NC}"
echo ""
echo -e "${YELLOW}If you see 'relation does not exist' for official_accounts:${NC}"
echo -e "${RED}→ The migration is incomplete or wasn't fully applied${NC}"
echo ""
echo -e "${GREEN}Solutions:${NC}"
echo -e "1. Generate missing migration: ${YELLOW}docker compose exec django python manage.py makemigrations${NC}"
echo -e "2. Apply migrations: ${YELLOW}docker compose exec django python manage.py migrate${NC}"
echo -e "3. Or run: ${YELLOW}./fix_permissions_and_migrate.sh${NC}"
