"""
Celery tasks for Tracking Number Empty Worker.

All tasks here will be processed by the tracking_number_empty queue.
"""

import logging
from .celery_tracking_number_empty import app
from .tracking_number_empty import TrackingNumberEmptyWorker

logger = logging.getLogger(__name__)


@app.task(
    name='apps.data_acquisition.workers.tasks_tracking_number_empty.process_record',
    bind=True,
    max_retries=0,  # No retry - let the next scheduled run handle failures
)
def process_record(self, **kwargs):
    """
    Process Purchasing records and publish Apple Store tracking tasks.

    This task:
    1. Queries Purchasing model for matching records (tracking_number is empty)
    2. Constructs Apple Store tracking URLs
    3. Publishes scraping tasks to WebScraper API

    Args:
        **kwargs: Additional parameters passed to the worker

    Returns:
        Dictionary containing processing results
    """
    task_id = self.request.id
    logger.info(f"[Task {task_id}] Starting tracking_number_empty processing")

    try:
        worker = TrackingNumberEmptyWorker()
        result = worker.run(kwargs)

        if result.get('status') == 'error':
            logger.error(f"[Task {task_id}] Processing failed: {result.get('error')}")

        logger.info(f"[Task {task_id}] Processing completed: {result}")
        return result

    except Exception as exc:
        logger.error(f"[Task {task_id}] Task failed: {exc}", exc_info=True)
        raise


@app.task(
    name='apps.data_acquisition.workers.tasks_tracking_number_empty.process_batch',
    bind=True,
)
def process_batch(self, count: int = 1):
    """
    Queue multiple process_record tasks.

    Note: For this worker, typically only 1 task is needed per run
    since it processes up to 20 records internally.

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
