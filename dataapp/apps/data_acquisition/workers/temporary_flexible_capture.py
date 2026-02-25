"""
Worker for processing Purchasing records with flexible filter conditions.

Queue: temporary_flexible_capture
Redis DB: 7

Selection criteria (dynamic):
- has related official_account (implicit condition)
- official_account.email is not empty (implicit condition)
- Dynamic filter conditions passed as dictionary (OR relationship)
- last_info_updated_at IS NULL OR < now - N hours (prevent duplicate publish)

Supported filter fields:
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
- tracking_number: null/notnull/text

This worker queries Purchasing model, constructs Apple Store URLs,
and publishes scraping tasks to WebScraper API (using official_website_redirect_to_yamato_tracking config).
"""

import logging
import uuid
from typing import List, Dict, Optional
from django.db.models import Q

logger = logging.getLogger(__name__)


# Mapping from command parameter names to model field names
FIELD_MAPPING = {
    'confirmed_at': 'confirmed_at',
    'latest_delivery_status': 'latest_delivery_status',
    'batch_encoding': 'batch_encoding',
    'batch_level_1': 'batch_level_1',
    'batch_level_2': 'batch_level_2',
    'batch_level_3': 'batch_level_3',
    'estimated_delivery_date': 'estimated_delivery_date',
    'last_info_updated_at': 'last_info_updated_at',
    'delivery_status_query_time': 'delivery_status_query_time',
    'estimated_website_arrival_date': 'estimated_website_arrival_date',
    'tracking_number': 'tracking_number',
}

# Fields that only support null/notnull (datetime/date fields)
DATE_ONLY_FIELDS = {
    'confirmed_at',
    'estimated_delivery_date',
    'last_info_updated_at',
    'delivery_status_query_time',
    'estimated_website_arrival_date',
}

# Fields that support null/notnull and text matching (CharField fields)
TEXT_FIELDS = {
    'latest_delivery_status',
    'batch_encoding',
    'batch_level_1',
    'batch_level_2',
    'batch_level_3',
    'tracking_number',
}


class TemporaryFlexibleCaptureWorker:
    """
    Worker for querying Purchasing model with flexible filters and publishing tracking tasks.

    This worker:
    1. Queries Purchasing records matching dynamic filter conditions (OR relationship)
    2. Applies implicit conditions (has official_account with email)
    3. Constructs Apple Store URLs using order_number and official_account.email
    4. Publishes scraping tasks to WebScraper API
    5. Creates TrackingBatch and TrackingJob records
    """

    QUEUE_NAME = 'temporary_flexible_capture'
    WORKER_NAME = 'temporary_flexible_capture_worker'
    TASK_NAME = 'temporary_flexible_capture'
    CUSTOM_ID_PREFIX = 'tfc'
    MAX_RECORDS = 20  # Maximum records to process per run

    def __init__(self):
        """Initialize the worker."""
        self.logger = logger

    def build_filter_query(self, filter_dict: Dict[str, str]) -> Optional[Q]:
        """
        Build Django Q object from filter dictionary.

        Filter conditions are combined with OR relationship.

        Args:
            filter_dict: Dictionary with field names as keys and conditions as values.
                        Values can be 'null', 'notnull', or text for exact match.

        Returns:
            Q object representing the combined filter conditions, or None if empty.
        """
        if not filter_dict:
            return None

        conditions = []

        for field, value in filter_dict.items():
            if field not in FIELD_MAPPING:
                self.logger.warning(
                    f"[{self.WORKER_NAME}] Unknown field '{field}', skipping"
                )
                continue

            model_field = FIELD_MAPPING[field]
            value_lower = value.lower() if isinstance(value, str) else value

            if value_lower == 'null':
                # Field is NULL or empty string
                if field in TEXT_FIELDS:
                    # For text fields, check both NULL and empty string
                    conditions.append(
                        Q(**{f'{model_field}__isnull': True}) | Q(**{model_field: ''})
                    )
                else:
                    # For date/datetime fields, only check NULL
                    conditions.append(Q(**{f'{model_field}__isnull': True}))

            elif value_lower == 'notnull':
                # Field is NOT NULL and not empty string
                if field in TEXT_FIELDS:
                    # For text fields, check both NOT NULL and not empty
                    conditions.append(
                        Q(**{f'{model_field}__isnull': False}) & ~Q(**{model_field: ''})
                    )
                else:
                    # For date/datetime fields, only check NOT NULL
                    conditions.append(Q(**{f'{model_field}__isnull': False}))

            else:
                # Exact text match (only for TEXT_FIELDS)
                if field in TEXT_FIELDS:
                    conditions.append(Q(**{model_field: value}))
                else:
                    self.logger.warning(
                        f"[{self.WORKER_NAME}] Field '{field}' only supports null/notnull, "
                        f"ignoring value '{value}'"
                    )

        if not conditions:
            return None

        # Combine conditions with OR
        combined = conditions[0]
        for condition in conditions[1:]:
            combined = combined | condition

        return combined

    def get_matching_records(self, filter_dict: Dict[str, str]) -> List['Purchasing']:
        """
        Query Purchasing model for matching records.

        Implicit conditions (always applied):
        - has related official_account
        - official_account.email is not empty
        - last_info_updated_at IS NULL OR < now - N hours (prevent duplicate publish)

        Dynamic conditions (OR relationship):
        - Based on filter_dict parameter

        Args:
            filter_dict: Dictionary with field names and filter conditions

        Returns:
            List of Purchasing records (max MAX_RECORDS)
        """
        from apps.data_aggregation.models import Purchasing
        from apps.data_acquisition.models import TrackingJob
        from django.conf import settings
        from django.utils import timezone
        from datetime import timedelta

        # Build dynamic filter query
        dynamic_filter = self.build_filter_query(filter_dict)

        if dynamic_filter is None:
            self.logger.warning(
                f"[{self.WORKER_NAME}] No valid filter conditions provided"
            )
            return []

        # Get query interval configuration (default 1 hour)
        query_interval_hours = getattr(settings, 'DELIVERY_STATUS_QUERY_INTERVAL_HOURS', 1)
        time_threshold = timezone.now() - timedelta(hours=query_interval_hours)

        # Query records matching implicit conditions + dynamic conditions
        candidate_records = Purchasing.objects.filter(
            # Implicit condition: has related official_account
            Q(official_account__isnull=False),
            # Implicit condition: official_account.email is not empty
            Q(official_account__email__isnull=False),
            ~Q(official_account__email=''),
            # Implicit condition: prevent duplicate publish
            Q(last_info_updated_at__isnull=True) | Q(last_info_updated_at__lt=time_threshold),
        ).filter(
            # Dynamic conditions (OR relationship)
            dynamic_filter
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
            task_data: Task parameters containing 'filter_dict'

        Returns:
            Execution result dictionary
        """
        from apps.data_acquisition.models import SyncLog, TrackingBatch

        filter_dict = task_data.get('filter_dict', {})

        self.logger.info(
            f"[{self.WORKER_NAME}] Starting execution with filters: {filter_dict}"
        )

        try:
            # Step 1: Query matching records
            records = self.get_matching_records(filter_dict)

            if not records:
                self.logger.warning(f"[{self.WORKER_NAME}] No matching records found")

                SyncLog.objects.create(
                    operation_type='temporary_flexible_capture_completed',
                    message="No matching records found",
                    success=True,
                    details={
                        'total_records': 0,
                        'filter_dict': filter_dict
                    }
                )

                return {
                    'status': 'success',
                    'message': 'No matching records found',
                    'total_records': 0,
                    'filter_dict': filter_dict
                }

            # Step 2: Create TrackingBatch
            batch_uuid = uuid.uuid4()
            batch_uuid_str = str(batch_uuid)
            batch_short = batch_uuid_str[:8]

            batch = TrackingBatch.objects.create(
                file_path=f'purchasing_query_temporary_flexible_capture_{batch_short}',
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

                # Update last_info_updated_at and lock record to prevent duplicate publish
                record.last_info_updated_at = current_time
                record.is_locked = True
                record.locked_at = current_time
                record.locked_by_worker = 'TFC'  # temporary_flexible_capture
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
                operation_type='temporary_flexible_capture_triggered',
                message=f"Dispatched {len(dispatched_tasks)} tracking tasks",
                success=True,
                details={
                    'batch_uuid': batch_uuid_str,
                    'total_records': len(records),
                    'dispatched_count': len(dispatched_tasks),
                    'filter_dict': filter_dict,
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
                'filter_dict': filter_dict,
                'custom_ids': [t['custom_id'] for t in dispatched_tasks]
            }

        except Exception as exc:
            self.logger.error(
                f"[{self.WORKER_NAME}] Execution failed: {exc}",
                exc_info=True
            )

            SyncLog.objects.create(
                operation_type='temporary_flexible_capture_completed',
                message=f"Execution failed: {str(exc)}",
                success=False,
                details={
                    'error': str(exc),
                    'filter_dict': filter_dict
                }
            )

            raise

    def run(self, task_data: dict = None) -> dict:
        """
        Run the worker (entry point).

        Args:
            task_data: Task parameters containing 'filter_dict'

        Returns:
            Execution result
        """
        task_data = task_data or {}
        return self.execute(task_data)
