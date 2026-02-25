"""
Celery configuration for data_acquisition app.
This app uses Redis DB 1 for complete isolation from data_aggregation.
"""
import os
from celery import Celery
from decouple import config

# Set the default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Get Redis configuration
REDIS_HOST = config('REDIS_HOST', default='localhost')
REDIS_PORT = config('REDIS_PORT', default='6379')
REDIS_DB = config('REDIS_DB_ACQUISITION', default='1')

# Create Celery app for data acquisition
app = Celery('data_acquisition')

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
    # Task routing configuration
    # - Tracking tasks are routed to dedicated queues for isolation
    # - Other acquisition tasks use the default acquisition_queue
    task_routes={
        # Phase 1: Excel 读取和准备（快速完成）
        'apps.data_acquisition.tasks.process_tracking_excel': {'queue': 'tracking_excel_queue'},
        'apps.data_acquisition.tasks.process_japan_post_tracking_10_excel': {'queue': 'tracking_excel_queue'},

        # Phase 1.5: 串行发布任务（独立 worker，单并发，6s 间隔）
        'apps.data_acquisition.tasks.publish_tracking_batch': {'queue': 'publish_tracking_queue'},

        # Yamato 10 本地任务（独立 worker，长超时）
        'apps.data_acquisition.tasks.process_yamato_tracking_10_excel': {'queue': 'yamato_tracking_10_queue'},
        
        # Yamato 10 Tracking Number 任务（从Purchasing模型查询，独立 worker）
        'apps.data_acquisition.tasks.process_yamato_tracking_10_tracking_number': {'queue': 'yamato_tracking_10_tracking_number_queue'},

        # Phase 2: Webhook 回调和数据解析
        'apps.data_acquisition.tasks.process_webscraper_tracking': {'queue': 'tracking_webhook_queue'},
        'apps.data_acquisition.tasks.batch_writeback_tracking_data': {'queue': 'tracking_webhook_queue'},

        # Default queue for other acquisition tasks
        'apps.data_acquisition.tasks.*': {'queue': 'acquisition_queue'},
    },
    task_default_queue='acquisition_queue',
)

# Load task modules from all registered Django apps
app.autodiscover_tasks(['apps.data_acquisition'])

@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Debug task for testing."""
    print(f'Request: {self.request!r}')
