#!/bin/bash

# ============================================================================
# Database Migration Setup Script
# ============================================================================
# This script generates and runs database migrations for the Django project
# ============================================================================

set -e  # Exit on error

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}============================================================================${NC}"
echo -e "${BLUE}  Database Migration Setup${NC}"
echo -e "${BLUE}============================================================================${NC}"
echo ""

# Check if Docker is available
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker command not found!${NC}"
    echo -e "${YELLOW}Please run this script on your host machine, not inside a container.${NC}"
    exit 1
fi

# Check if docker compose is running
if ! docker compose ps | grep -q "django"; then
    echo -e "${YELLOW}⚠️  Django container doesn't appear to be running.${NC}"
    echo -e "${YELLOW}Starting containers...${NC}"
    docker compose up -d
    sleep 5
fi

echo -e "${GREEN}🔧 Step 1: Generating migrations for data_aggregation app...${NC}"
docker compose exec django python manage.py makemigrations data_aggregation

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Failed to generate migrations for data_aggregation${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}🔧 Step 2: Generating migrations for data_acquisition app...${NC}"
docker compose exec django python manage.py makemigrations data_acquisition

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Failed to generate migrations for data_acquisition${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}🔧 Step 3: Running all migrations...${NC}"
docker compose exec django python manage.py migrate

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Failed to run migrations${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}============================================================================${NC}"
echo -e "${GREEN}✅ All migrations completed successfully!${NC}"
echo -e "${GREEN}============================================================================${NC}"
echo ""

echo -e "${BLUE}📊 Database tables created:${NC}"
docker compose exec django python manage.py showmigrations data_aggregation
docker compose exec django python manage.py showmigrations data_acquisition

echo ""
echo -e "${BLUE}🎯 Next step: Generate mock data${NC}"
echo -e "${BLUE}Run: ./generate_mock_data.sh --docker --count 20${NC}"
