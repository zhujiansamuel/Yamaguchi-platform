"""
Celery tasks for Temporary Flexible Capture Worker.

All tasks here will be processed by the temporary_flexible_capture queue.
"""

import logging
from .celery_temporary_flexible_capture import app
from .temporary_flexible_capture import TemporaryFlexibleCaptureWorker

logger = logging.getLogger(__name__)


@app.task(
    name='apps.data_acquisition.workers.tasks_temporary_flexible_capture.process_record',
    bind=True,
    max_retries=0,  # No retry - let the next scheduled run handle failures
)
def process_record(self, filter_dict: dict = None, **kwargs):
    """
    Process Purchasing records with flexible filter conditions and publish tracking tasks.

    This task:
    1. Queries Purchasing model for matching records based on filter_dict
    2. Constructs Apple Store tracking URLs
    3. Publishes scraping tasks to WebScraper API

    Args:
        filter_dict: Dictionary with field names as keys and conditions as values.
                    Supported fields:
                    - confirmed_at: null/notnull
                    - latest_delivery_status: null/notnull/text
                    - batch_encoding: null/notnull/text
                    - batch_level_1: null/notnull/text
                    - batch_level_2: null/notnull/text
                    - batch_level_3: null/notnull/text
                    - estimated_delivery_date: null/notnull
                    - last_info_updated_at: null/notnull
                    - delivery_status_query_time: null/notnull
                    - estimated_website_arrival_date: null/notnull
        **kwargs: Additional parameters passed to the worker

    Returns:
        Dictionary containing processing results
    """
    task_id = self.request.id
    logger.info(f"[Task {task_id}] Starting temporary_flexible_capture processing")
    logger.info(f"[Task {task_id}] Filter dict: {filter_dict}")

    try:
        worker = TemporaryFlexibleCaptureWorker()
        task_data = {'filter_dict': filter_dict or {}}
        task_data.update(kwargs)
        result = worker.run(task_data)

        if result.get('status') == 'error':
            logger.error(f"[Task {task_id}] Processing failed: {result.get('error')}")

        logger.info(f"[Task {task_id}] Processing completed: {result}")
        return result

    except Exception as exc:
        logger.error(f"[Task {task_id}] Task failed: {exc}", exc_info=True)
        raise


@app.task(
    name='apps.data_acquisition.workers.tasks_temporary_flexible_capture.process_batch',
    bind=True,
)
def process_batch(self, filter_dict: dict = None, count: int = 1):
    """
    Queue multiple process_record tasks with the same filter conditions.

    Note: For this worker, typically only 1 task is needed per run
    since it processes up to 20 records internally.

    Args:
        filter_dict: Dictionary with field names and filter conditions
        count: Number of tasks to queue (default: 1)

    Returns:
        List of queued task IDs
    """
    task_id = self.request.id
    logger.info(f"[Task {task_id}] Queuing {count} process_record tasks with filter: {filter_dict}")

    results = []
    for i in range(count):
        result = process_record.delay(filter_dict=filter_dict)
        results.append({'index': i, 'task_id': result.id})

    logger.info(f"[Task {task_id}] Queued {len(results)} tasks")
    return results
