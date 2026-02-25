#!/bin/bash
set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   Data Platform - Docker Deployment Script    ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════╝${NC}"
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo -e "${YELLOW}⚠️  .env file not found!${NC}"
    echo -e "${GREEN}Creating .env from template...${NC}"
    cp .env.docker .env
    echo -e "${YELLOW}📝 Please edit .env file with your configuration${NC}"
    echo -e "${YELLOW}Then run this script again.${NC}"
    exit 1
fi

# Check if SSL certs exist
if [ ! -f docker/certs/cert.pem ] || [ ! -f docker/certs/key.pem ]; then
    echo -e "${YELLOW}⚠️  SSL certificates not found!${NC}"
    echo -e "${YELLOW}Please place your certificates in docker/certs/${NC}"
    echo -e "${YELLOW}  - cert.pem (certificate)${NC}"
    echo -e "${YELLOW}  - key.pem (private key)${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Configuration files found${NC}"
echo ""

# Ask for action
echo -e "${BLUE}Select action:${NC}"
echo "  1) Build and start all services"
echo "  2) Start existing services"
echo "  3) Stop all services"
echo "  4) Restart all services"
echo "  5) View logs"
echo "  6) Status check"
echo "  7) Clean up (remove containers and volumes)"
read -p "Enter choice [1-7]: " choice

case $choice in
    1)
        echo -e "${GREEN}🔨 Building Docker images...${NC}"
        docker compose build

        echo -e "${GREEN}🚀 Starting services...${NC}"
        docker compose up -d

        echo -e "${GREEN}⏳ Waiting for services to be ready...${NC}"
        sleep 10

        echo -e "${GREEN}📊 Checking service status...${NC}"
        docker compose ps

        echo ""
        echo -e "${GREEN}✅ Deployment complete!${NC}"
        echo ""
        echo -e "${BLUE}Next steps:${NC}"
        echo "1. Configure Caddy on host: ${YELLOW}sudo nano /etc/caddy/Caddyfile${NC}"
        echo "   (Add configuration from DOCKER_DEPLOYMENT.md)"
        echo "2. Reload Caddy: ${YELLOW}sudo systemctl reload caddy${NC}"
        echo "3. Create superuser: ${YELLOW}docker compose exec django python manage.py createsuperuser${NC}"
        echo "4. Access Django Admin: ${YELLOW}https://data.yamaguchi.lan/admin/${NC}"
        echo "5. Access Flower: ${YELLOW}https://flower.yamaguchi.lan/${NC}"
        echo "6. Configure Nextcloud webhook (see DOCKER_DEPLOYMENT.md)"
        ;;

    2)
        echo -e "${GREEN}🚀 Starting services...${NC}"
        docker compose up -d
        docker compose ps
        ;;

    3)
        echo -e "${YELLOW}🛑 Stopping services...${NC}"
        docker compose down
        echo -e "${GREEN}✓ Services stopped${NC}"
        ;;

    4)
        echo -e "${YELLOW}🔄 Restarting services...${NC}"
        docker compose restart
        docker compose ps
        ;;

    5)
        echo -e "${BLUE}📋 Showing logs (Ctrl+C to exit)...${NC}"
        docker compose logs -f
        ;;

    6)
        echo -e "${BLUE}📊 Service Status:${NC}"
        docker compose ps
        echo ""
        echo -e "${BLUE}🔍 Health Checks:${NC}"
        echo -n "Django: "
        if curl -sf https://data.yamaguchi.lan/api/schema/ > /dev/null 2>&1; then
            echo -e "${GREEN}✓ Healthy${NC}"
        else
            echo -e "${RED}✗ Unhealthy${NC}"
        fi

        echo -n "Flower: "
        if curl -sf https://flower.yamaguchi.lan/ > /dev/null 2>&1; then
            echo -e "${GREEN}✓ Healthy${NC}"
        else
            echo -e "${RED}✗ Unhealthy${NC}"
        fi
        ;;

    7)
        echo -e "${RED}⚠️  WARNING: This will remove all containers and data!${NC}"
        read -p "Are you sure? (yes/no): " confirm
        if [ "$confirm" = "yes" ]; then
            echo -e "${YELLOW}🗑️  Removing containers and volumes...${NC}"
            docker compose down -v
            echo -e "${GREEN}✓ Cleanup complete${NC}"
        else
            echo -e "${YELLOW}Cancelled${NC}"
        fi
        ;;

    *)
        echo -e "${RED}Invalid choice${NC}"
        exit 1
        ;;
esac
