#!/bin/bash

# Development environment startup script

echo "🚀 Starting Data Consolidation Platform - Development Mode"
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Start PostgreSQL and Redis
echo "📦 Starting PostgreSQL and Redis containers..."
docker-compose up -d

# Wait for databases to be ready
echo "⏳ Waiting for databases to be ready..."
sleep 5

# Run migrations
echo "🔄 Running database migrations..."
python manage.py migrate

echo ""
echo "✅ Development environment is ready!"
echo ""
echo "📋 Next steps:"
echo "1. Start Django server:"
echo "   python manage.py runserver"
echo ""
echo "2. Start Celery Worker - Data Acquisition:"
echo "   celery -A apps.data_acquisition.celery worker -Q acquisition_queue -n acquisition_worker@%h --loglevel=info"
echo ""
echo "3. Start Celery Worker - Data Aggregation:"
echo "   celery -A apps.data_aggregation.celery worker -Q aggregation_queue -n aggregation_worker@%h --loglevel=info"
echo ""
echo "4. (Optional) Start Celery Beat:"
echo "   celery -A config beat --loglevel=info"
echo ""
echo "🌐 Access points:"
echo "   - Django: http://localhost:8000"
echo "   - Admin: http://localhost:8000/admin/"
echo "   - API Docs: http://localhost:8000/api/docs/"
