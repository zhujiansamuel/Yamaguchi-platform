"""
Celery configuration for data_aggregation app.
This app uses Redis DB 0 for complete isolation from data_acquisition.
"""
import os
from celery import Celery
from decouple import config

# Set the default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Get Redis configuration
REDIS_HOST = config('REDIS_HOST', default='localhost')
REDIS_PORT = config('REDIS_PORT', default='6379')
REDIS_DB = config('REDIS_DB_AGGREGATION', default='0')

# Create Celery app for data aggregation
app = Celery('data_aggregation')

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
    worker_max_tasks_per_child=1000,
    # Broker connection retry configuration
    broker_connection_retry_on_startup=True,  # Celery 6.0+ compatibility
    # Only process tasks from aggregation queue
    task_routes={
        'apps.data_aggregation.tasks.*': {'queue': 'aggregation_queue'},
    },
    task_default_queue='aggregation_queue',
)

# Load task modules from all registered Django apps
app.autodiscover_tasks(['apps.data_aggregation'])

@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Debug task for testing."""
    print(f'Request: {self.request!r}')
