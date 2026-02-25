#!/bin/bash

# ============================================================================
# Complete Database Rebuild - Nuclear Option
# ============================================================================
# This script completely rebuilds the database when in inconsistent state
# WARNING: This will DELETE ALL DATA!
# ============================================================================

set -e

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${RED}============================================================================${NC}"
echo -e "${RED}  COMPLETE DATABASE REBUILD${NC}"
echo -e "${RED}  This will DELETE ALL DATA and rebuild from scratch!${NC}"
echo -e "${RED}============================================================================${NC}"
echo ""

echo -e "${YELLOW}Current situation:${NC}"
echo "- Some tables exist (aggregation_sources, iphones, ipads, etc.)"
echo "- Some tables are missing (official_accounts, purchasing, etc.)"
echo "- Migration records are inconsistent"
echo ""
echo -e "${RED}This script will:${NC}"
echo "1. Drop ALL tables completely"
echo "2. Clear ALL migration records"
echo "3. Delete and regenerate migration files"
echo "4. Create ALL tables from scratch"
echo ""

read -p "Type 'DELETE EVERYTHING' to confirm: " confirm

if [ "$confirm" != "DELETE EVERYTHING" ]; then
    echo -e "${YELLOW}Cancelled. Database unchanged.${NC}"
    exit 0
fi

echo ""
echo -e "${BLUE}============================================================================${NC}"
echo -e "${BLUE}  Starting Complete Rebuild${NC}"
echo -e "${BLUE}============================================================================${NC}"
echo ""

echo -e "${YELLOW}🔧 Step 1: Dropping ALL tables (including Django system tables)...${NC}"
docker compose exec -T postgres psql -U postgres -d data_platform << 'EOSQL'
DO $$ DECLARE
    r RECORD;
BEGIN
    -- Drop all tables
    FOR r IN (SELECT tablename FROM pg_tables WHERE schemaname = 'public') LOOP
        EXECUTE 'DROP TABLE IF EXISTS ' || quote_ident(r.tablename) || ' CASCADE';
    END LOOP;

    -- Drop all sequences
    FOR r IN (SELECT sequence_name FROM information_schema.sequences WHERE sequence_schema = 'public') LOOP
        EXECUTE 'DROP SEQUENCE IF EXISTS ' || quote_ident(r.sequence_name) || ' CASCADE';
    END LOOP;
END $$;
EOSQL
echo "All tables and sequences dropped"

echo ""
echo -e "${YELLOW}🔧 Step 2: Detecting Django container UID...${NC}"
DJANGO_UID=$(docker compose exec django id -u 2>/dev/null || echo "999")
echo "Django container is running as UID: ${DJANGO_UID}"

echo ""
echo -e "${YELLOW}🔧 Step 3: Backing up and removing old migration files...${NC}"
mkdir -p .migration_backup_$(date +%Y%m%d_%H%M%S)
cp apps/data_aggregation/migrations/*.py .migration_backup_$(date +%Y%m%d_%H%M%S)/ 2>/dev/null || true
cp apps/data_acquisition/migrations/*.py .migration_backup_$(date +%Y%m%d_%H%M%S)/ 2>/dev/null || true

# Fix permissions before deleting
docker compose exec -u root django chown -R ${DJANGO_UID}:${DJANGO_UID} /app/apps/

# Delete migration files inside container
docker compose exec django find /app/apps/data_aggregation/migrations/ -name "*.py" ! -name "__init__.py" -delete
docker compose exec django find /app/apps/data_acquisition/migrations/ -name "*.py" ! -name "__init__.py" -delete
echo "Old migrations removed"

echo ""
echo -e "${YELLOW}🔧 Step 4: Running Django migrate to create system tables...${NC}"
docker compose exec django python manage.py migrate
echo "Django system tables created"

echo ""
echo -e "${YELLOW}🔧 Step 5: Generating fresh migration files...${NC}"
docker compose exec django python manage.py makemigrations data_aggregation
docker compose exec django python manage.py makemigrations data_acquisition

echo ""
echo -e "${YELLOW}🔧 Step 6: Verifying migration files...${NC}"
echo "Checking for OfficialAccount:"
grep -l "OfficialAccount" apps/data_aggregation/migrations/0001_*.py && echo "✓ Found!" || echo "✗ Missing!"

echo ""
echo "Checking for Purchasing:"
grep -l "Purchasing" apps/data_aggregation/migrations/0001_*.py && echo "✓ Found!" || echo "✗ Missing!"

echo ""
echo "Checking for Inventory:"
grep -l "Inventory" apps/data_aggregation/migrations/0001_*.py && echo "✓ Found!" || echo "✗ Missing!"

echo ""
echo -e "${YELLOW}🔧 Step 7: Applying all migrations...${NC}"
docker compose exec django python manage.py migrate

echo ""
echo -e "${YELLOW}🔧 Step 8: Verifying all tables created...${NC}"
echo "Checking critical tables:"

echo -n "official_accounts: "
docker compose exec postgres psql -U postgres -d data_platform -c "\d official_accounts" > /dev/null 2>&1 && echo "✓ EXISTS" || echo "✗ MISSING"

echo -n "purchasing: "
docker compose exec postgres psql -U postgres -d data_platform -c "\d purchasing" > /dev/null 2>&1 && echo "✓ EXISTS" || echo "✗ MISSING"

echo -n "inventory: "
docker compose exec postgres psql -U postgres -d data_platform -c "\d inventory" > /dev/null 2>&1 && echo "✓ EXISTS" || echo "✗ MISSING"

echo -n "iphones: "
docker compose exec postgres psql -U postgres -d data_platform -c "\d iphones" > /dev/null 2>&1 && echo "✓ EXISTS" || echo "✗ MISSING"

echo -n "ipads: "
docker compose exec postgres psql -U postgres -d data_platform -c "\d ipads" > /dev/null 2>&1 && echo "✓ EXISTS" || echo "✗ MISSING"

echo ""
echo -e "${GREEN}============================================================================${NC}"
echo -e "${GREEN}✅ Database rebuild complete!${NC}"
echo -e "${GREEN}============================================================================${NC}"
echo ""

echo -e "${BLUE}📊 Migration status:${NC}"
docker compose exec django python manage.py showmigrations

echo ""
echo -e "${BLUE}🎯 Next steps:${NC}"
echo -e "1. Create superuser: ${YELLOW}docker compose exec django python manage.py createsuperuser${NC}"
echo -e "2. Generate test data: ${YELLOW}./generate_mock_data.sh --docker --count 20${NC}"
echo -e "3. Access admin: ${YELLOW}https://data.yamaguchi.lan/admin/${NC}"
