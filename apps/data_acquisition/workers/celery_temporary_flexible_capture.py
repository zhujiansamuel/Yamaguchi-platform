"""
Celery configuration for Temporary Flexible Capture Worker.

This worker uses Redis DB 7 for complete isolation.
Queue: temporary_flexible_capture

Start worker:
    celery -A apps.data_acquisition.workers.celery_temporary_flexible_capture worker \
        -Q temporary_flexible_capture -c 1 --loglevel=info
"""

import os
from celery import Celery
from decouple import config

# Set the default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Get Redis configuration
REDIS_HOST = config('REDIS_HOST', default='localhost')
REDIS_PORT = config('REDIS_PORT', default='6379')
REDIS_DB = config('REDIS_DB_TEMPORARY_FLEXIBLE_CAPTURE', default='7')

# Create Celery app
app = Celery('temporary_flexible_capture_worker')

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
    worker_max_tasks_per_child=100,
    task_routes={
        'apps.data_acquisition.workers.tasks_temporary_flexible_capture.*': {
            'queue': 'temporary_flexible_capture'
        },
    },
    task_default_queue='temporary_flexible_capture',
)

# Auto-discover tasks
app.autodiscover_tasks(
    ['apps.data_acquisition.workers'],
    related_name='tasks_temporary_flexible_capture'
)


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Debug task for testing."""
    print(f'Temporary Flexible Capture Worker - Request: {self.request!r}')
