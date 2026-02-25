"""
Celery configuration for Tracking Number Empty Worker.

This worker uses Redis DB 5 for complete isolation.
Queue: tracking_number_empty

Start worker:
    celery -A apps.data_acquisition.workers.celery_tracking_number_empty worker \
        -Q tracking_number_empty -c 1 --loglevel=info
"""

import os
from celery import Celery
from decouple import config

# Set the default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Get Redis configuration
REDIS_HOST = config('REDIS_HOST', default='localhost')
REDIS_PORT = config('REDIS_PORT', default='6379')
REDIS_DB = config('REDIS_DB_TRACKING_NUMBER_EMPTY', default='5')

# Create Celery app
app = Celery('tracking_number_empty_worker')

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
    task_time_limit=2 * 60,  # 2 minutes (no Playwright, just task dispatching)
    task_soft_time_limit=110,  # 110 seconds
    worker_prefetch_multiplier=1,
    worker_concurrency=1,  # Single-threaded operation
    worker_max_tasks_per_child=100,
    task_routes={
        'apps.data_acquisition.workers.tasks_tracking_number_empty.*': {
            'queue': 'tracking_number_empty'
        },
    },
    task_default_queue='tracking_number_empty',
)

# Auto-discover tasks
app.autodiscover_tasks(
    ['apps.data_acquisition.workers'],
    related_name='tasks_tracking_number_empty'
)


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Debug task for testing."""
    print(f'Tracking Number Empty Worker - Request: {self.request!r}')
