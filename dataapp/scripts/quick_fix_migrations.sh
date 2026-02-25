#!/bin/bash

# Quick fix script for migration issues
# Run this on your host machine

set -e

echo "🔍 Checking migration status..."
echo ""

echo "Current migration status:"
docker compose exec django python manage.py showmigrations data_aggregation data_acquisition || true

echo ""
echo "🔧 Generating migrations..."
echo ""

echo "Step 1: data_aggregation app"
docker compose exec django python manage.py makemigrations data_aggregation

echo ""
echo "Step 2: data_acquisition app"
docker compose exec django python manage.py makemigrations data_acquisition

echo ""
echo "🚀 Running migrations..."
docker compose exec django python manage.py migrate

echo ""
echo "✅ Migration complete! Checking status..."
echo ""

docker compose exec django python manage.py showmigrations data_aggregation data_acquisition

echo ""
echo "🎉 Done! You can now access Django admin."
