"""
Celery tasks for Initial Order Confirmation Email Worker.

All tasks here will be processed by the initial_order_confirmation_email_queue.
"""

import logging
from django.utils import timezone
from .celery_initial_order_confirmation_email import app
from .initial_order_confirmation_email import InitialOrderConfirmationEmailWorker

logger = logging.getLogger(__name__)


@app.task(
    name='apps.data_acquisition.EmailParsing.tasks_initial_order_confirmation_email.process_email',
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def process_email(self, email_data: dict, **kwargs):
    """
    Process an initial order confirmation email.

    This task receives email data from the content analysis worker,
    finds the corresponding Purchasing record, and updates it.

    Args:
        email_data: Dictionary containing email information
        **kwargs: Additional parameters

    Returns:
        Dictionary containing processing results
    """
    from apps.data_aggregation.models import EmailProcessingLog

    task_id = self.request.id
    logger.info(f"[Task {task_id}] Starting initial order confirmation email processing")

    log = EmailProcessingLog.objects.create(
        stage='initial_order',
        status='running',
        celery_task_id=task_id or '',
        total_items=1,
        detail='处理初始订单确认邮件',
    )

    try:
        worker = InitialOrderConfirmationEmailWorker()
        result = worker.run({'email_data': email_data, **kwargs})

        if result.get('status') == 'error':
            logger.error(f"[Task {task_id}] Processing failed: {result.get('error')}")
            log.status = 'error'
            log.error_message = str(result.get('error', ''))
            log.completed_at = timezone.now()
            log.save()
            if self.request.retries < self.max_retries:
                raise self.retry(exc=Exception(result.get('error')))

        log.status = 'success'
        log.completed_items = 1
        log.completed_at = timezone.now()
        log.save()

        logger.info(f"[Task {task_id}] Processing completed: {result}")
        return result

    except Exception as exc:
        logger.error(f"[Task {task_id}] Task failed: {exc}", exc_info=True)
        log.status = 'error'
        log.error_message = str(exc)
        log.completed_at = timezone.now()
        log.save()
        if self.request.retries < self.max_retries:
            logger.info(f"[Task {task_id}] Retrying in {self.default_retry_delay}s...")
            raise self.retry(exc=exc)
        raise
