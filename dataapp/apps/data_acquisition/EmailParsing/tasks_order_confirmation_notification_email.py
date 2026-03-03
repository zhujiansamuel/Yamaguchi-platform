"""
Celery tasks for Order Confirmation Notification Email Worker.

All tasks here will be processed by the order_confirmation_notification_email_queue.
"""

import logging
from django.utils import timezone
from .celery_order_confirmation_notification_email import app
from .order_confirmation_notification_email import OrderConfirmationNotificationEmailWorker

logger = logging.getLogger(__name__)


@app.task(
    name='apps.data_acquisition.EmailParsing.tasks_order_confirmation_notification_email.process_email',
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def process_email(self, email_data: dict, **kwargs):
    """
    Process an order confirmation notification email.

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
    logger.info(f"[Task {task_id}] Starting order confirmation notification email processing")

    log = EmailProcessingLog.objects.create(
        stage='notification',
        status='running',
        celery_task_id=task_id or '',
        total_items=1,
        detail='生成订单确认通知邮件',
    )

    try:
        worker = OrderConfirmationNotificationEmailWorker()
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
