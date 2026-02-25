#!/bin/bash
# Script to fix migration records directly in the database
# This runs SQL to manually mark 0002 as applied before Django starts

set -e

echo "================================================"
echo "Fixing migration records in database"
echo "================================================"
echo ""

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Default values if not set
DB_NAME="${DB_NAME:-data_platform}"
DB_USER="${DB_USER:-postgres}"
DB_HOST="${DB_HOST:-postgres}"

echo "Connecting to database: $DB_NAME@$DB_HOST"
echo ""

# Stop all containers first
echo "Step 1: Stopping all containers..."
docker compose down

echo ""
echo "Step 2: Starting only postgres and redis..."
docker compose up -d postgres redis

echo ""
echo "Waiting for postgres to be ready..."
sleep 5

# Check if postgres is ready
until docker compose exec postgres pg_isready -U "$DB_USER" > /dev/null 2>&1; do
    echo "Waiting for postgres..."
    sleep 2
done

echo "Postgres is ready!"
echo ""

echo "Step 3: Applying SQL fix to django_migrations table..."
docker compose exec -T postgres psql -U "$DB_USER" -d "$DB_NAME" << 'EOSQL'
-- Show current data_acquisition migrations
SELECT app, name, applied FROM django_migrations WHERE app = 'data_acquisition' ORDER BY applied;

-- Insert missing 0002 migration
INSERT INTO django_migrations (app, name, applied)
VALUES ('data_acquisition', '0002_historicalsynclog', NOW())
ON CONFLICT DO NOTHING;

-- Verify
SELECT app, name, applied FROM django_migrations WHERE app = 'data_acquisition' ORDER BY applied;
EOSQL

echo ""
echo "Step 4: Starting all containers..."
docker compose up -d

echo ""
echo "Step 5: Waiting for Django to start..."
sleep 10

echo ""
echo "Step 6: Applying remaining migrations..."
docker compose exec django python manage.py migrate --noinput

echo ""
echo "================================================"
echo "Migration fix complete!"
echo "================================================"
echo ""
echo "Checking container status:"
docker compose ps
