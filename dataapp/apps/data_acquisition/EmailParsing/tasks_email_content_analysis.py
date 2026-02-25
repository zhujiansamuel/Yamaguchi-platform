"""
Celery tasks for Email Content Analysis Worker.

All tasks here will be processed by the email_content_analysis_queue.
"""

import logging
from .celery_email_content_analysis import app
from .email_content_analysis import EmailContentAnalysisWorker

logger = logging.getLogger(__name__)


@app.task(
    name='apps.data_acquisition.EmailParsing.tasks_email_content_analysis.process_email',
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def process_email(self, **kwargs):
    """
    Process a single email for content analysis and routing.
    
    This task fetches an email, analyzes its content, and creates
    the appropriate handler task.
    
    Args:
        **kwargs: Additional parameters passed to the worker
        
    Returns:
        Dictionary containing processing results
    """
    task_id = self.request.id
    logger.info(f"[Task {task_id}] Starting email content analysis")
    
    try:
        worker = EmailContentAnalysisWorker()
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
    name='apps.data_acquisition.EmailParsing.tasks_email_content_analysis.process_batch',
    bind=True,
)
def process_batch(self, count: int = 10):
    """
    Queue multiple process_email tasks.
    
    Args:
        count: Number of emails to process
        
    Returns:
        List of queued task IDs
    """
    task_id = self.request.id
    logger.info(f"[Task {task_id}] Queuing {count} process_email tasks")
    
    results = []
    for i in range(count):
        result = process_email.delay()
        results.append({'index': i, 'task_id': result.id})
    
    logger.info(f"[Task {task_id}] Queued {len(results)} tasks")
    return results
