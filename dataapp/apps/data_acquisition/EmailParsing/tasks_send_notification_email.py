"""
Celery tasks for Send Notification Email Worker.

All tasks here will be processed by the send_notification_email_queue.
"""

import logging
from .celery_send_notification_email import app
from .send_notification_email import SendNotificationEmailWorker

logger = logging.getLogger(__name__)


@app.task(
    name='apps.data_acquisition.EmailParsing.tasks_send_notification_email.process_email',
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def process_email(self, email_data: dict, **kwargs):
    """
    Process a send notification email.
    
    This task receives email data from the content analysis worker,
    finds the corresponding Purchasing record, and updates it.
    
    Args:
        email_data: Dictionary containing email information
        **kwargs: Additional parameters
        
    Returns:
        Dictionary containing processing results
    """
    task_id = self.request.id
    logger.info(f"[Task {task_id}] Starting send notification email processing")
    
    try:
        worker = SendNotificationEmailWorker()
        result = worker.run({'email_data': email_data, **kwargs})
        
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
