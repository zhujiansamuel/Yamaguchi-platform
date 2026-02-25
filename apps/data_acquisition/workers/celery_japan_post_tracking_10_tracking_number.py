"""
Celery configuration for Japan Post Tracking 10 Tracking Number Worker.

This worker uses Redis DB 6 for complete isolation.
Queue: japan_post_tracking_10_tracking_number_queue

Start worker:
    celery -A apps.data_acquisition.workers.celery_japan_post_tracking_10_tracking_number worker \
        -Q japan_post_tracking_10_tracking_number_queue -c 1 --loglevel=info
"""

import os
from celery import Celery
from decouple import config

# Set the default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Get Redis configuration
REDIS_HOST = config('REDIS_HOST', default='localhost')
REDIS_PORT = config('REDIS_PORT', default='6379')
REDIS_DB = config('REDIS_DB_JAPAN_POST_TRACKING_10_TRACKING_NUMBER', default='6')

# Create Celery app
app = Celery('japan_post_tracking_10_tracking_number_worker')

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
    task_time_limit=2 * 60,  # 2 minutes
    task_soft_time_limit=110,  # 110 seconds (1:50)
    worker_prefetch_multiplier=1,
    worker_concurrency=1,  # Single-threaded operation
    worker_max_tasks_per_child=100,
    task_routes={
        'apps.data_acquisition.workers.tasks_japan_post_tracking_10_tracking_number.*': {
            'queue': 'japan_post_tracking_10_tracking_number_queue'
        },
    },
    task_default_queue='japan_post_tracking_10_tracking_number_queue',
)

# Auto-discover tasks
app.autodiscover_tasks(
    ['apps.data_acquisition.workers'],
    related_name='tasks_japan_post_tracking_10_tracking_number'
)


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Debug task for testing."""
    print(f'Japan Post Tracking 10 Tracking Number Worker - Request: {self.request!r}')
