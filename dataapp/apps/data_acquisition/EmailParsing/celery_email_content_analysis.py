"""
Celery configuration for Email Content Analysis Worker.

This worker uses Redis DB 10 (shared with other EmailParsing workers).
Queue: email_content_analysis_queue

Start worker:
    celery -A apps.data_acquisition.EmailParsing.celery_email_content_analysis worker \
        -Q email_content_analysis_queue -c 1 --loglevel=info
"""

import os
from celery import Celery
from decouple import config

# Set the default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Get Redis configuration
REDIS_HOST = config('REDIS_HOST', default='localhost')
REDIS_PORT = config('REDIS_PORT', default='6379')
REDIS_DB = config('REDIS_DB_EMAIL_PARSING', default='10')

# Create Celery app
app = Celery('email_content_analysis_worker')

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
    task_soft_time_limit=110,  # 110 seconds
    worker_prefetch_multiplier=1,
    worker_concurrency=1,  # Single-threaded operation
    worker_max_tasks_per_child=100,
    task_routes={
        'apps.data_acquisition.EmailParsing.tasks_email_content_analysis.*': {
            'queue': 'email_content_analysis_queue'
        },
    },
    task_default_queue='email_content_analysis_queue',
)

# Auto-discover tasks
app.autodiscover_tasks(
    ['apps.data_acquisition.EmailParsing'],
    related_name='tasks_email_content_analysis'
)


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Debug task for testing."""
    print(f'Email Content Analysis Worker - Request: {self.request!r}')
