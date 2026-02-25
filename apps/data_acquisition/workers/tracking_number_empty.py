"""
Worker for processing Purchasing records with empty tracking_number.

Queue: tracking_number_empty
Redis DB: 5

Selection criteria:
- order_number starts with 'w' (case-insensitive)
- has related official_account
- official_account.email is not empty
- latest_delivery_status NOT IN ['配達完了', 'お届け先にお届け済み']
- tracking_number is empty
- last_info_updated_at IS NULL OR < now - N hours (prevent duplicate publish within N hours)

This worker queries Purchasing model, constructs Apple Store URLs,
and publishes scraping tasks to WebScraper API (using official_website_redirect_to_yamato_tracking config).
"""

import logging
import uuid
from typing import List, Dict
from django.db.models import Q

logger = logging.getLogger(__name__)


class TrackingNumberEmptyWorker:
    """
    Worker for querying Purchasing model and publishing Apple Store tracking tasks.

    This worker:
    1. Queries Purchasing records matching specific criteria (tracking_number is empty)
    2. Constructs Apple Store URLs using order_number and official_account.email
    3. Publishes scraping tasks to WebScraper API
    4. Creates TrackingBatch and TrackingJob records
    """

    QUEUE_NAME = 'tracking_number_empty'
    WORKER_NAME = 'tracking_number_empty_worker'
    TASK_NAME = 'official_website_redirect_to_yamato_tracking'
    CUSTOM_ID_PREFIX = 'owryt'
    MAX_RECORDS = 20  # Maximum records to process per run

    def __init__(self):
        """Initialize the worker."""
        self.logger = logger

    def get_matching_records(self) -> List['Purchasing']:
        """
        Query Purchasing model for matching records.

        Selection criteria:
        - order_number starts with 'w' (case-insensitive)
        - has related official_account
        - official_account.email is not empty
        - latest_delivery_status NOT IN ['配達完了', 'お届け先にお届け済み']
        - tracking_number is empty
        - last_info_updated_at IS NULL OR < now - N hours (prevent duplicate publish)

        Returns:
            List of Purchasing records (max 20)
        """
        from apps.data_aggregation.models import Purchasing
        from apps.data_acquisition.models import TrackingJob
        from django.conf import settings
        from django.utils import timezone
        from datetime import timedelta

        # Get query interval configuration (default 6 hours)
        query_interval_hours = getattr(settings, 'DELIVERY_STATUS_QUERY_INTERVAL_HOURS', 1)
        time_threshold = timezone.now() - timedelta(hours=query_interval_hours)

        # Query records matching all criteria
        candidate_records = Purchasing.objects.filter(
            # order_number starts with 'w' (case-insensitive)
            Q(order_number__istartswith='w'),
            # has related official_account
            Q(official_account__isnull=False),
            # official_account.email is not empty
            Q(official_account__email__isnull=False),
            ~Q(official_account__email=''),
            # tracking_number is empty
            Q(tracking_number__isnull=True) | Q(tracking_number='') | Q(tracking_number='nan'),
            # 防止重复发布：last_info_updated_at 为空或超过配置的时间间隔
            Q(last_info_updated_at__isnull=True) | Q(last_info_updated_at__lt=time_threshold),
        ).exclude(
            # Exclude completed delivery status
            latest_delivery_status__in=['配達完了', 'お届け先にお届け済み']
        ).select_related(
            'official_account'
        )[:100]  # Get more candidates for filtering

        self.logger.info(
            f"[{self.WORKER_NAME}] Found {len(candidate_records)} candidate records"
        )

        # Filter out records with order_number already in recent TrackingJob
        valid_records = []
        skipped_by_tracking_job = 0

        for record in candidate_records:
            # Check if order_number already exists in recent TrackingJob
            # 检查是否在时间阈值内已有相同 order_number 的 TrackingJob
            recent_job_exists = TrackingJob.objects.filter(
                batch__task_name=self.TASK_NAME,
                batch__created_at__gte=time_threshold,
                target_url__icontains=record.order_number
            ).exists()

            if recent_job_exists:
                skipped_by_tracking_job += 1
                self.logger.debug(
                    f"[{self.WORKER_NAME}] Skipping {record.order_number}: "
                    f"already in recent TrackingJob"
                )
                continue

            valid_records.append(record)

            # Stop when we have enough records
            if len(valid_records) >= self.MAX_RECORDS:
                break

        self.logger.info(
            f"[{self.WORKER_NAME}] Filtered {len(valid_records)} valid records "
            f"(skipped {skipped_by_tracking_job} due to recent TrackingJob)"
        )

        return valid_records

    def construct_url(self, order_number: str, email: str) -> str:
        """
        Construct Apple Store tracking URL.

        URL format: https://store.apple.com/go/jp/vieworder/{order_number}/{email}

        Args:
            order_number: Purchasing order number
            email: Official account email

        Returns:
            Constructed URL string
        """
        return f"https://store.apple.com/go/jp/vieworder/{order_number}/{email}"

    def publish_task(
        self,
        url: str,
        batch_uuid_str: str,
        custom_id: str,
        index: int
    ) -> Dict:
        """
        Publish a single tracking task to WebScraper API.

        Args:
            url: Target URL
            batch_uuid_str: TrackingBatch UUID
            custom_id: Custom task ID
            index: Task index

        Returns:
            Result dictionary
        """
        from apps.data_acquisition.tasks import publish_tracking_batch

        # Dispatch task to publish_tracking_queue
        # Use countdown for rate limiting (2 seconds per task)
        result = publish_tracking_batch.apply_async(
            args=[self.TASK_NAME, url, batch_uuid_str, custom_id, index],
            countdown=index * 2  # 2 second delay per task
        )

        return {
            'status': 'dispatched',
            'custom_id': custom_id,
            'task_id': result.id,
            'url': url,
            'index': index
        }

    def execute(self, task_data: dict) -> dict:
        """
        Execute the worker logic.

        Args:
            task_data: Task parameters (optional)

        Returns:
            Execution result dictionary
        """
        from apps.data_acquisition.models import SyncLog, TrackingBatch

        self.logger.info(f"[{self.WORKER_NAME}] Starting execution")

        try:
            # Step 1: Query matching records
            records = self.get_matching_records()

            if not records:
                self.logger.warning(f"[{self.WORKER_NAME}] No matching records found")

                SyncLog.objects.create(
                    operation_type='tracking_number_empty_completed',
                    message="No matching records found",
                    success=True,
                    details={
                        'total_records': 0
                    }
                )

                return {
                    'status': 'success',
                    'message': 'No matching records found',
                    'total_records': 0
                }

            # Step 2: Create TrackingBatch
            batch_uuid = uuid.uuid4()
            batch_uuid_str = str(batch_uuid)
            batch_short = batch_uuid_str[:8]

            batch = TrackingBatch.objects.create(
                file_path=f'purchasing_query_tracking_number_empty_{batch_short}',
                task_name=self.TASK_NAME,
                batch_uuid=batch_uuid,
                total_jobs=len(records),
                status='pending'
            )

            self.logger.info(
                f"[{self.WORKER_NAME}] Created TrackingBatch {batch_short} "
                f"with {len(records)} jobs"
            )

            # Step 3: Construct URLs and publish tasks
            dispatched_tasks = []
            url_details = []

            from django.utils import timezone
            current_time = timezone.now()

            for idx, record in enumerate(records):
                order_number = record.order_number
                email = record.official_account.email

                # Construct Apple Store URL
                url = self.construct_url(order_number, email)

                # Generate custom_id
                custom_id = f"{self.CUSTOM_ID_PREFIX}-{batch_short}-{idx:04d}"

                # Publish task
                result = self.publish_task(
                    url=url,
                    batch_uuid_str=batch_uuid_str,
                    custom_id=custom_id,
                    index=idx
                )

                # 立即更新 last_info_updated_at 并锁定记录，防止重复发布
                record.last_info_updated_at = current_time
                record.is_locked = True
                record.locked_at = current_time
                record.locked_by_worker = 'OWRYT'  # official_website_redirect_to_yamato_tracking 任务名首字母
                record.save(update_fields=['last_info_updated_at', 'is_locked', 'locked_at', 'locked_by_worker'])

                dispatched_tasks.append(result)
                url_details.append({
                    'record_id': record.id,
                    'uuid': str(record.uuid),
                    'order_number': order_number,
                    'email': email,
                    'url': url,
                    'custom_id': custom_id,
                    'task_id': result['task_id']
                })

                self.logger.info(
                    f"[{self.WORKER_NAME}] Dispatched task {idx+1}/{len(records)}: "
                    f"{custom_id} for order {order_number}"
                )

            # Step 4: Log to SyncLog
            SyncLog.objects.create(
                operation_type='tracking_number_empty_triggered',
                message=f"Dispatched {len(dispatched_tasks)} tracking tasks",
                success=True,
                details={
                    'batch_uuid': batch_uuid_str,
                    'total_records': len(records),
                    'dispatched_count': len(dispatched_tasks),
                    'url_details': url_details
                }
            )

            self.logger.info(
                f"[{self.WORKER_NAME}] Execution complete: "
                f"dispatched {len(dispatched_tasks)} tasks"
            )

            return {
                'status': 'success',
                'batch_uuid': batch_uuid_str,
                'total_records': len(records),
                'dispatched_count': len(dispatched_tasks),
                'custom_ids': [t['custom_id'] for t in dispatched_tasks]
            }

        except Exception as exc:
            self.logger.error(
                f"[{self.WORKER_NAME}] Execution failed: {exc}",
                exc_info=True
            )

            SyncLog.objects.create(
                operation_type='tracking_number_empty_completed',
                message=f"Execution failed: {str(exc)}",
                success=False,
                details={
                    'error': str(exc)
                }
            )

            raise

    def run(self, task_data: dict = None) -> dict:
        """
        Run the worker (entry point).

        Args:
            task_data: Optional task parameters

        Returns:
            Execution result
        """
        task_data = task_data or {}
        return self.execute(task_data)
