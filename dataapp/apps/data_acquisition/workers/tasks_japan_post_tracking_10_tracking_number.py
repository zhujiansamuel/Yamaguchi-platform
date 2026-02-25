"""
Celery tasks for Japan Post Tracking 10 Tracking Number Worker.

All tasks here will be processed by the japan_post_tracking_10_tracking_number_queue.
"""

import logging
from .celery_japan_post_tracking_10_tracking_number import app
from .japan_post_tracking_10_tracking_number import JapanPostTracking10TrackingNumberWorker

logger = logging.getLogger(__name__)


@app.task(
    name='apps.data_acquisition.workers.tasks_japan_post_tracking_10_tracking_number.process_record',
    bind=True,
    max_retries=0,  # No retry
)
def process_record(self, **kwargs):
    """
    Process Purchasing records and publish Japan Post tracking tasks.
    
    This task:
    1. Queries Purchasing model for matching records
    2. Constructs Japan Post tracking URLs
    3. Publishes scraping tasks to WebScraper API
    
    Args:
        **kwargs: Additional parameters passed to the worker
    
    Returns:
        Dictionary containing processing results
    """
    task_id = self.request.id
    logger.info(f"[Task {task_id}] Starting japan_post_tracking_10_tracking_number processing")
    
    try:
        worker = JapanPostTracking10TrackingNumberWorker()
        result = worker.run(kwargs)
        
        if result.get('status') == 'error':
            logger.error(f"[Task {task_id}] Processing failed: {result.get('error')}")
        
        logger.info(f"[Task {task_id}] Processing completed: {result}")
        return result
    
    except Exception as exc:
        logger.error(f"[Task {task_id}] Task failed: {exc}", exc_info=True)
        raise


@app.task(
    name='apps.data_acquisition.workers.tasks_japan_post_tracking_10_tracking_number.process_batch',
    bind=True,
)
def process_batch(self, count: int = 1):
    """
    Queue multiple process_record tasks.
    
    Note: For this worker, typically only 1 task is needed per run
    since it processes up to 10 records internally.
    
    Args:
        count: Number of tasks to queue (default: 1)
    
    Returns:
        List of queued task IDs
    """
    task_id = self.request.id
    logger.info(f"[Task {task_id}] Queuing {count} process_record tasks")
    
    results = []
    for i in range(count):
        result = process_record.delay()
        results.append({'index': i, 'task_id': result.id})
    
    logger.info(f"[Task {task_id}] Queued {len(results)} tasks")
    return results
