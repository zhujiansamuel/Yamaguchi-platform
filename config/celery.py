"""
Main Celery configuration for the project.
This is used for Celery Beat (scheduler) only.
Worker tasks are handled by app-specific Celery configurations.
"""
import os
from celery import Celery
from decouple import config

# Set the default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Get Redis configuration
REDIS_HOST = config('REDIS_HOST', default='localhost')
REDIS_PORT = config('REDIS_PORT', default='6379')

# Create Celery app for beat scheduler
app = Celery('data_platform')

# Use string here for broker and backend (Beat uses DB 0 by default)
app.config_from_object('django.conf:settings', namespace='CELERY')

# Configure broker and backend
app.conf.update(
    broker_url=f'redis://{REDIS_HOST}:{REDIS_PORT}/0',
    result_backend=f'redis://{REDIS_HOST}:{REDIS_PORT}/0',
)

# Auto-discover tasks from all installed apps
app.autodiscover_tasks()

# Celery Beat schedule (for periodic tasks)
app.conf.beat_schedule = {
    # Example: Run aggregation task every 30 minutes
    # 'aggregate-data-every-30-minutes': {
    #     'task': 'apps.data_aggregation.tasks.aggregate_from_sources',
    #     'schedule': 1800.0,  # 30 minutes in seconds
    #     'args': ([],)
    # },
    # Example: Fetch data every hour
    # 'fetch-data-hourly': {
    #     'task': 'apps.data_acquisition.tasks.fetch_data_from_source',
    #     'schedule': 3600.0,  # 1 hour in seconds
    #     'args': ({},)
    # },
}
