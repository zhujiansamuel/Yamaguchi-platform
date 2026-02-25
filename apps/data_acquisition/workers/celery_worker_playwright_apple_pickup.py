"""
Celery configuration for Playwright Apple Pickup Worker.

This worker uses Redis DB 9 for complete isolation.
Queue: playwright_apple_pickup_queue

This worker processes Apple Store pickup contact updates using Playwright:
- Logs into Apple Store with provided credentials
- Navigates to the specified order
- Updates the pickup contact name
- Each task handles a single order update

Start worker:
    celery -A apps.data_acquisition.workers.celery_worker_playwright_apple_pickup worker \
        -Q playwright_apple_pickup_queue -c 1 --loglevel=info
"""

import os
from celery import Celery
from decouple import config

# Set the default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Get Redis configuration
REDIS_HOST = config('REDIS_HOST', default='localhost')
REDIS_PORT = config('REDIS_PORT', default='6379')
REDIS_DB = config('REDIS_DB_PLAYWRIGHT_APPLE_PICKUP', default='9')

# Create Celery app
app = Celery('playwright_apple_pickup_worker')

# Configure Celery
app.conf.update(
    broker_url=f'redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}',
    result_backend=f'redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}',
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Asia/Tokyo',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=10 * 60,  # 10 minutes
    task_soft_time_limit=9 * 60,  # 9 minutes
    worker_prefetch_multiplier=1,
    worker_concurrency=1,  # Single-threaded operation
    worker_max_tasks_per_child=10,  # Restart after 10 tasks to free browser resources
    task_routes={
        'apps.data_acquisition.workers.tasks_playwright_apple_pickup.process_apple_pickup_contact_update': {
            'queue': 'playwright_apple_pickup_queue'
        },
    },
    task_default_queue='playwright_apple_pickup_queue',
)

# Load task modules explicitly
# autodiscover_tasks only finds 'tasks.py' by default, so we import directly
from apps.data_acquisition.workers import tasks_playwright_apple_pickup  # noqa: F401, E402


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Debug task for testing."""
    print(f'Playwright Apple Pickup Worker - Request: {self.request!r}')
