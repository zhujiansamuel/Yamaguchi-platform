#!/bin/bash

# ============================================================================
# Reset and Recreate Database Schema
# ============================================================================
# This script safely resets the database schema when tables are incomplete
# WARNING: This will delete all data in the database!
# ============================================================================

set -e

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${RED}============================================================================${NC}"
echo -e "${RED}  WARNING: This will DELETE ALL DATA in the database!${NC}"
echo -e "${RED}============================================================================${NC}"
echo ""

read -p "Are you sure you want to continue? Type 'YES' to confirm: " confirm

if [ "$confirm" != "YES" ]; then
    echo -e "${YELLOW}Cancelled.${NC}"
    exit 0
fi

echo ""
echo -e "${BLUE}============================================================================${NC}"
echo -e "${BLUE}  Reset and Recreate Database Schema${NC}"
echo -e "${BLUE}============================================================================${NC}"
echo ""

echo -e "${YELLOW}🔧 Step 1: Backing up current migration files...${NC}"
mkdir -p .migration_backup
cp apps/data_aggregation/migrations/*.py .migration_backup/ 2>/dev/null || true
cp apps/data_acquisition/migrations/*.py .migration_backup/ 2>/dev/null || true
echo "Backup saved to .migration_backup/"

echo ""
echo -e "${YELLOW}🔧 Step 2: Detecting Django container UID...${NC}"
DJANGO_UID=$(docker compose exec django id -u 2>/dev/null || echo "999")
echo "Django container is running as UID: ${DJANGO_UID}"

echo ""
echo -e "${YELLOW}🔧 Step 3: Fixing file permissions before deletion...${NC}"
docker compose exec -u root django chown -R ${DJANGO_UID}:${DJANGO_UID} /app/apps/
echo "Permissions fixed"

echo ""
echo -e "${YELLOW}🔧 Step 4: Removing old migration files (inside container)...${NC}"
docker compose exec django find /app/apps/data_aggregation/migrations/ -name "*.py" ! -name "__init__.py" -delete
docker compose exec django find /app/apps/data_acquisition/migrations/ -name "*.py" ! -name "__init__.py" -delete
echo "Old migrations removed"

echo ""
echo -e "${YELLOW}🔧 Step 5: Dropping all tables...${NC}"
docker compose exec django python manage.py flush --no-input
echo "All tables dropped"

echo ""
echo -e "${YELLOW}🔧 Step 6: Generating fresh migrations...${NC}"
docker compose exec django python manage.py makemigrations data_aggregation
docker compose exec django python manage.py makemigrations data_acquisition

echo ""
echo -e "${YELLOW}🔧 Step 7: Creating all tables...${NC}"
docker compose exec django python manage.py migrate

echo ""
echo -e "${GREEN}============================================================================${NC}"
echo -e "${GREEN}✅ Database schema recreated successfully!${NC}"
echo -e "${GREEN}============================================================================${NC}"
echo ""

echo -e "${BLUE}📊 Checking migration status:${NC}"
docker compose exec django python manage.py showmigrations

echo ""
echo -e "${BLUE}🎯 Next steps:${NC}"
echo -e "${BLUE}  1. Create superuser: ${YELLOW}docker compose exec django python manage.py createsuperuser${NC}"
echo -e "${BLUE}  2. Generate test data: ${YELLOW}./generate_mock_data.sh --docker --count 20${NC}"
echo -e "${BLUE}  3. Access admin: ${YELLOW}https://data.yamaguchi.lan/admin/${NC}"
