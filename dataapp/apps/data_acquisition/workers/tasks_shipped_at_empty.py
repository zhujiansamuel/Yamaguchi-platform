"""
Celery tasks for Shipped At Empty Worker.

All tasks here will be processed by the shipped_at_empty queue.
"""

import logging
from .celery_shipped_at_empty import app
from .shipped_at_empty import ShippedAtEmptyWorker

logger = logging.getLogger(__name__)


@app.task(
    name='apps.data_acquisition.workers.tasks_shipped_at_empty.process_record',
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def process_record(self, **kwargs):
    """
    Process a single Purchasing record with empty shipped_at.

    This task acquires a record, processes it, and releases the lock.

    Args:
        **kwargs: Additional parameters passed to the worker

    Returns:
        Dictionary containing processing results
    """
    task_id = self.request.id
    logger.info(f"[Task {task_id}] Starting shipped_at_empty processing")

    try:
        worker = ShippedAtEmptyWorker()
        result = worker.run(kwargs)

        if result.get('status') == 'error':
            logger.error(f"[Task {task_id}] Processing failed: {result.get('error')}")
            if self.request.retries < self.max_retries:
                raise self.retry(exc=Exception(result.get('error')))

        logger.info(f"[Task {task_id}] Processing completed: {result}")
        return result

    except Exception as exc:
        logger.error(f"[Task {task_id}] Task failed: {exc}", exc_info=True)
        if self.request.retries < self.max_retries:
            logger.info(f"[Task {task_id}] Retrying in {self.default_retry_delay}s...")
            raise self.retry(exc=exc)
        raise


@app.task(
    name='apps.data_acquisition.workers.tasks_shipped_at_empty.process_batch',
    bind=True,
)
def process_batch(self, count: int = 10):
    """
    Queue multiple process_record tasks.

    Args:
        count: Number of records to process

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
