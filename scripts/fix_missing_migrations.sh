#!/bin/bash

# ============================================================================
# Fix Missing Migration Files
# ============================================================================
# This script fixes the issue where migration files don't exist but Django
# thinks migrations are already applied
# ============================================================================

set -e

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}============================================================================${NC}"
echo -e "${BLUE}  Fix Missing Migration Files${NC}"
echo -e "${BLUE}============================================================================${NC}"
echo ""

echo -e "${YELLOW}🔍 Step 1: Checking current state...${NC}"
echo "Migration files in data_aggregation:"
ls -la apps/data_aggregation/migrations/*.py 2>/dev/null | grep -v __pycache__ || echo "Only __init__.py found"

echo ""
echo "Migration records in database:"
docker compose exec postgres psql -U postgres -d data_platform -c "SELECT app, name FROM django_migrations WHERE app IN ('data_aggregation', 'data_acquisition') ORDER BY app, id;" 2>/dev/null || echo "Could not query database"

echo ""
echo -e "${RED}⚠️  Problem detected: Migration files are missing but Django thinks they're applied!${NC}"
echo ""

read -p "Do you want to fix this by clearing migration records and regenerating? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo -e "${YELLOW}Cancelled.${NC}"
    exit 0
fi

echo ""
echo -e "${YELLOW}🔧 Step 2: Clearing migration records from database...${NC}"
docker compose exec postgres psql -U postgres -d data_platform -c "DELETE FROM django_migrations WHERE app = 'data_aggregation';"
docker compose exec postgres psql -U postgres -d data_platform -c "DELETE FROM django_migrations WHERE app = 'data_acquisition';"
echo "Migration records cleared"

echo ""
echo -e "${YELLOW}🔧 Step 3: Detecting Django container UID...${NC}"
DJANGO_UID=$(docker compose exec django id -u 2>/dev/null || echo "999")
echo "Django container is running as UID: ${DJANGO_UID}"

echo ""
echo -e "${YELLOW}🔧 Step 4: Fixing permissions...${NC}"
docker compose exec -u root django chown -R ${DJANGO_UID}:${DJANGO_UID} /app/apps/
echo "Permissions fixed"

echo ""
echo -e "${YELLOW}🔧 Step 5: Generating fresh migration files...${NC}"
docker compose exec django python manage.py makemigrations data_aggregation
docker compose exec django python manage.py makemigrations data_acquisition

echo ""
echo -e "${YELLOW}🔧 Step 6: Checking generated files...${NC}"
echo "Migration files created:"
ls -la apps/data_aggregation/migrations/*.py 2>/dev/null | grep -v __pycache__ | grep -v __init__

echo ""
echo "Checking if OfficialAccount is in the migration:"
grep -l "OfficialAccount" apps/data_aggregation/migrations/0001_*.py 2>/dev/null && echo "✓ Found!" || echo "✗ Not found - this is a problem!"

echo ""
echo -e "${YELLOW}🔧 Step 7: Applying migrations with --fake-initial...${NC}"
echo "Using --fake-initial to handle existing tables"
docker compose exec django python manage.py migrate --fake-initial

echo ""
echo -e "${YELLOW}🔧 Step 8: Verifying tables exist...${NC}"
echo "Checking official_accounts table:"
docker compose exec postgres psql -U postgres -d data_platform -c "\d official_accounts" 2>&1 | head -15

echo ""
echo -e "${GREEN}============================================================================${NC}"
echo -e "${GREEN}✅ Migration fix complete!${NC}"
echo -e "${GREEN}============================================================================${NC}"
echo ""
echo -e "${BLUE}🎯 Next step: Generate test data${NC}"
echo -e "${BLUE}Run: ${YELLOW}./generate_mock_data.sh --docker --count 20${NC}"
