"""
Celery configuration for Yamato Tracking 10 Tracking Number Worker.

This worker uses Redis DB 8 for complete isolation.
Queue: yamato_tracking_10_tracking_number_queue

This worker processes Yamato tracking queries from Purchasing model records:
- Queries records with order_number starting with 'w'
- Filters tracking_number with 12 digits starting with 4
- Excludes records with latest_delivery_status='配達完了'
- Queries up to 10 tracking numbers per batch

Start worker:
    celery -A apps.data_acquisition.workers.celery_worker_yamato_tracking_10_tracking_number worker \
        -Q yamato_tracking_10_tracking_number_queue -c 1 --loglevel=info
"""

import os
from celery import Celery
from decouple import config

# Set the default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Get Redis configuration
REDIS_HOST = config('REDIS_HOST', default='localhost')
REDIS_PORT = config('REDIS_PORT', default='6379')
REDIS_DB = config('REDIS_DB_YAMATO_TRACKING_10_TRACKING_NUMBER', default='8')

# Create Celery app
app = Celery('yamato_tracking_10_tracking_number_worker')

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
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    worker_concurrency=1,  # Single-threaded operation
    worker_max_tasks_per_child=100,
    task_routes={
        'apps.data_acquisition.tasks.process_yamato_tracking_10_tracking_number': {
            'queue': 'yamato_tracking_10_tracking_number_queue'
        },
    },
    task_default_queue='yamato_tracking_10_tracking_number_queue',
)

# Load task modules from data_acquisition app
app.autodiscover_tasks(['apps.data_acquisition'])


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Debug task for testing."""
    print(f'Yamato Tracking 10 Tracking Number Worker - Request: {self.request!r}')
