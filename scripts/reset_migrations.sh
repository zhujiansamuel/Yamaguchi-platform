#!/bin/bash

# Reset Database Migrations Script
# This script will:
# 1. Stop all containers
# 2. Remove database volumes
# 3. Start containers
# 4. Generate fresh migrations
# 5. Apply migrations

set -e

echo "=== Resetting Database Migrations ==="
echo ""

# Stop all containers and remove volumes
echo "Step 1: Stopping containers and removing volumes..."
docker compose down -v

echo ""
echo "Step 2: Starting containers..."
docker compose up -d postgres redis

# Wait for database to be ready
echo ""
echo "Step 3: Waiting for database to be ready..."
sleep 10

echo ""
echo "Step 4: Generating fresh migrations..."
docker compose run --rm django python manage.py makemigrations

echo ""
echo "Step 5: Applying migrations..."
docker compose run --rm django python manage.py migrate

echo ""
echo "Step 6: Starting all services..."
docker compose up -d

echo ""
echo "=== Migration reset complete! ==="
echo ""
echo "You can now check the status with: docker compose logs -f django"
