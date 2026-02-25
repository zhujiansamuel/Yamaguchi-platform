#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Django Application Startup ===${NC}"

# Wait for PostgreSQL
echo -e "${YELLOW}Waiting for PostgreSQL...${NC}"
while ! pg_isready -h $DB_HOST -p $DB_PORT -U $DB_USER > /dev/null 2>&1; do
    echo "PostgreSQL is unavailable - sleeping"
    sleep 1
done
echo -e "${GREEN}PostgreSQL is up!${NC}"




# Wait for Redis
echo -e "${YELLOW}Waiting for Redis...${NC}"
while ! timeout 1 bash -c "cat < /dev/null > /dev/tcp/$REDIS_HOST/$REDIS_PORT" 2>/dev/null; do
    echo "Redis is unavailable - sleeping"
    sleep 1
done
echo -e "${GREEN}Redis is up!${NC}"

# Determine which service to run
SERVICE=${1:-gunicorn}

case "$SERVICE" in
    gunicorn)
        echo -e "${YELLOW}Running database migrations...${NC}"
        python manage.py migrate --noinput

        echo -e "${YELLOW}Collecting static files...${NC}"
        python manage.py collectstatic --noinput --clear

        echo -e "${GREEN}Starting Gunicorn server...${NC}"
        exec gunicorn config.wsgi:application \
            --bind 0.0.0.0:8000 \
            --workers 4 \
            --threads 2 \
            --worker-class gthread \
            --worker-tmp-dir /dev/shm \
            --timeout 120 \
            --graceful-timeout 30 \
            --keep-alive 5 \
            --max-requests 1000 \
            --max-requests-jitter 50 \
            --access-logfile - \
            --error-logfile - \
            --log-level info
        ;;

    celery_worker_acquisition)
        echo -e "${GREEN}Starting Celery Worker (Acquisition Queue)...${NC}"
        exec celery -A apps.data_acquisition.celery worker \
            --loglevel=info \
            --concurrency=4 \
            --queues=acquisition_queue \
            --hostname=acquisition@%h \
            --max-tasks-per-child=100 \
            --time-limit=300 \
            --soft-time-limit=270
        ;;

    celery_worker_aggregation)
        echo -e "${GREEN}Starting Celery Worker (Aggregation Queue)...${NC}"
        exec celery -A apps.data_aggregation.celery worker \
            --loglevel=info \
            --concurrency=4 \
            --queues=aggregation_queue \
            --hostname=aggregation@%h \
            --max-tasks-per-child=100 \
            --time-limit=300 \
            --soft-time-limit=270
        ;;

    celery_worker_tracking_phase1)
        echo -e "${GREEN}Starting Celery Worker (Tracking Excel Queue - Phase 1)...${NC}"
        # Note: Large Excel files (500+ rows) with 6s API delay need ~1 hour
        # --max-tasks-per-child=1 ensures worker restarts after each task to free memory
        exec celery -A apps.data_acquisition.celery worker \
            --loglevel=info \
            --concurrency=1 \
            --queues=tracking_excel_queue \
            --hostname=tracking_phase1@%h \
            --max-tasks-per-child=1 \
            --time-limit=7200 \
            --soft-time-limit=7000
        ;;

    celery_worker_tracking_phase2)
        echo -e "${GREEN}Starting Celery Worker (Tracking Webhook Queue - Phase 2)...${NC}"
        exec celery -A apps.data_acquisition.celery worker \
            --loglevel=info \
            --concurrency=2 \
            --queues=tracking_webhook_queue \
            --hostname=tracking_phase2@%h \
            --max-tasks-per-child=100 \
            --time-limit=300 \
            --soft-time-limit=270
        ;;

    celery_worker_publish_tracking_batch)
        echo -e "${GREEN}Starting Celery Worker (Publish Tracking Queue - Phase 1.5)...${NC}"
        # Serial publishing with 6s sleep after each task
        # 1-minute timeout per task
        exec celery -A apps.data_acquisition.celery worker \
            --loglevel=info \
            --concurrency=1 \
            --queues=publish_tracking_queue \
            --hostname=publish_tracking@%h \
            --max-tasks-per-child=100 \
            --time-limit=60 \
            --soft-time-limit=55
        ;;

    celery_worker_yamato_tracking_10)
        echo -e "${GREEN}Starting Celery Worker (Yamato Tracking 10 - Local Task)...${NC}"
        # Long-running local task (5 hours timeout)
        exec celery -A apps.data_acquisition.celery worker \
            --loglevel=info \
            --concurrency=1 \
            --queues=yamato_tracking_10_queue \
            --hostname=yamato_tracking_10@%h \
            --max-tasks-per-child=1 \
            --time-limit=18000 \
            --soft-time-limit=17900
        ;;

    celery_worker_yamato_tracking_10_tracking_number)
        echo -e "${GREEN}Starting Celery Worker (Yamato Tracking 10 Tracking Number - Query from Purchasing)...${NC}"
        # Query Purchasing model for Yamato tracking (30 minutes timeout)
        exec celery -A apps.data_acquisition.workers.celery_worker_yamato_tracking_10_tracking_number worker \
            --loglevel=info \
            --concurrency=1 \
            --queues=yamato_tracking_10_tracking_number_queue \
            --hostname=yamato_tracking_10_tracking_number@%h \
            --max-tasks-per-child=100 \
            --time-limit=1800 \
            --soft-time-limit=1500
        ;;

    celery_worker_japan_post_tracking_10_tracking_number)
        echo -e "${GREEN}Starting Celery Worker (Japan Post Tracking 10 Tracking Number - Query from Purchasing)...${NC}"
        # Query Purchasing model for Japan Post tracking (2 minutes timeout)
        exec celery -A apps.data_acquisition.workers.celery_japan_post_tracking_10_tracking_number worker \
            --loglevel=info \
            --concurrency=1 \
            --queues=japan_post_tracking_10_tracking_number_queue \
            --hostname=japan_post_tracking_10_tracking_number@%h \
            --max-tasks-per-child=100 \
            --time-limit=120 \
            --soft-time-limit=110
        ;;

    celery_worker_tracking_number_empty)
        echo -e "${GREEN}Starting Celery Worker (Tracking Number Empty - Query from Purchasing)...${NC}"
        # Query Purchasing model for empty tracking numbers, publish to WebScraper (2 minutes timeout)
        exec celery -A apps.data_acquisition.workers.celery_tracking_number_empty worker \
            --loglevel=info \
            --concurrency=1 \
            --queues=tracking_number_empty \
            --hostname=tracking_number_empty@%h \
            --max-tasks-per-child=100 \
            --time-limit=120 \
            --soft-time-limit=110
        ;;

    celery_worker_email_content_analysis)
        echo -e "${GREEN}Starting Celery Worker (Email Content Analysis)...${NC}"
        exec celery -A apps.data_acquisition.EmailParsing.celery_email_content_analysis worker \
            --loglevel=info \
            --concurrency=1 \
            --queues=email_content_analysis_queue \
            --hostname=email_content_analysis@%h \
            --max-tasks-per-child=100 \
            --time-limit=120 \
            --soft-time-limit=110
        ;;

    celery_worker_initial_order_confirmation_email)
        echo -e "${GREEN}Starting Celery Worker (Initial Order Confirmation Email)...${NC}"
        exec celery -A apps.data_acquisition.EmailParsing.celery_initial_order_confirmation_email worker \
            --loglevel=info \
            --concurrency=1 \
            --queues=initial_order_confirmation_email_queue \
            --hostname=initial_order_confirmation_email@%h \
            --max-tasks-per-child=100 \
            --time-limit=60 \
            --soft-time-limit=55
        ;;

    celery_worker_order_confirmation_notification_email)
        echo -e "${GREEN}Starting Celery Worker (Order Confirmation Notification Email)...${NC}"
        exec celery -A apps.data_acquisition.EmailParsing.celery_order_confirmation_notification_email worker \
            --loglevel=info \
            --concurrency=1 \
            --queues=order_confirmation_notification_email_queue \
            --hostname=order_confirmation_notification_email@%h \
            --max-tasks-per-child=100 \
            --time-limit=60 \
            --soft-time-limit=55
        ;;

    celery_worker_send_notification_email)
        echo -e "${GREEN}Starting Celery Worker (Send Notification Email)...${NC}"
        exec celery -A apps.data_acquisition.EmailParsing.celery_send_notification_email worker \
            --loglevel=info \
            --concurrency=1 \
            --queues=send_notification_email_queue \
            --hostname=send_notification_email@%h \
            --max-tasks-per-child=100 \
            --time-limit=60 \
            --soft-time-limit=55
        ;;

    celery_worker_playwright_apple_pickup)
        echo -e "${GREEN}Starting Celery Worker (Playwright Apple Pickup - Browser Automation)...${NC}"
        # Browser automation task for Apple Store pickup contact updates (10 minutes timeout)
        exec celery -A apps.data_acquisition.workers.celery_worker_playwright_apple_pickup worker \
            --loglevel=info \
            --concurrency=1 \
            --queues=playwright_apple_pickup_queue \
            --hostname=playwright_apple_pickup@%h \
            --max-tasks-per-child=10 \
            --time-limit=600 \
            --soft-time-limit=540
        ;;

    celery_beat)
        echo -e "${GREEN}Starting Celery Beat...${NC}"
        # Remove old celerybeat schedule file
        rm -f /app/celerybeat-schedule.db
        exec celery -A config.celery beat \
            --loglevel=info \
            --scheduler django_celery_beat.schedulers:DatabaseScheduler
        ;;

    flower)
        echo -e "${GREEN}Starting Flower (Celery Monitoring)...${NC}"
        exec celery -A config.celery flower \
            --port=5555 \
            --broker=redis://${REDIS_HOST}:${REDIS_PORT}/0 \
            --basic_auth=${FLOWER_USER}:${FLOWER_PASSWORD}
        ;;

    *)
        echo -e "${RED}Unknown service: $SERVICE${NC}"
        echo "Available services: gunicorn, celery_worker_acquisition, celery_worker_aggregation, celery_worker_tracking_phase1, celery_worker_publish_tracking_batch, celery_worker_yamato_tracking_10, celery_worker_yamato_tracking_10_tracking_number, celery_worker_tracking_phase2, celery_worker_email_content_analysis, celery_worker_initial_order_confirmation_email, celery_worker_order_confirmation_notification_email, celery_worker_send_notification_email, celery_worker_playwright_apple_pickup, celery_beat, flower"
        exit 1
        ;;
esac
