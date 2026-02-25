"""
Worker for processing Purchasing records for Japan Post Tracking 10.

Queue: japan_post_tracking_10_tracking_number_queue
Redis DB: 6

Selection criteria:
- order_number starts with 'w' (case-insensitive)
- tracking_number extracts to digits with length = 12
- latest_delivery_status NOT IN ['配達完了', 'お届け先にお届け済み']
- last_info_updated_at IS NULL OR < now - N hours (prevent duplicate publish within N hours)
- shipping_method = "JP LOGISTICS GROUP CO., LTD."

This worker queries Purchasing model, constructs Japan Post tracking URLs,
and publishes scraping tasks to WebScraper API (same as japan_post_tracking_10).
"""

import logging
import re
import uuid
import random
from typing import Optional, List, Dict
from urllib.parse import urlencode
from django.db.models import Q

logger = logging.getLogger(__name__)


class JapanPostTracking10TrackingNumberWorker:
    """
    Worker for querying Purchasing model and publishing Japan Post tracking tasks.

    This worker:
    1. Queries Purchasing records matching specific criteria
    2. Extracts tracking numbers (digits with length = 12)
    3. Constructs Japan Post URLs (10 tracking numbers per URL)
    4. Publishes scraping tasks to WebScraper API
    5. Creates TrackingBatch and TrackingJob records
    """
    
    QUEUE_NAME = 'japan_post_tracking_10_tracking_number_queue'
    WORKER_NAME = 'japan_post_tracking_10_tracking_number_worker'
    TASK_NAME = 'japan_post_tracking_10'
    MAX_RECORDS = 10  # Maximum records to process per run
    
    def __init__(self):
        """Initialize the worker."""
        self.logger = logger
    
    def get_matching_records(self) -> List['Purchasing']:
        """
        Query Purchasing model for matching records.

        Selection criteria:
        - order_number starts with 'w' (case-insensitive)
        - tracking_number extracts to digits with length = 12
        - latest_delivery_status NOT IN ['配達完了', 'お届け先にお届け済み']
        - last_info_updated_at IS NULL OR < now - N hours (prevent duplicate publish within N hours)
        - shipping_method = "JP LOGISTICS GROUP CO., LTD."

        Returns:
            List of Purchasing records (max 10)
        """
        from apps.data_aggregation.models import Purchasing
        from apps.data_acquisition.models import TrackingJob
        from django.conf import settings
        from django.utils import timezone
        from datetime import timedelta

        # Get query interval configuration (default 6 hours)
        query_interval_hours = getattr(settings, 'DELIVERY_STATUS_QUERY_INTERVAL_HOURS', 6)
        time_threshold = timezone.now() - timedelta(hours=query_interval_hours)

        # Query records matching basic criteria
        # 防止在 DELIVERY_STATUS_QUERY_INTERVAL_HOURS 内重复发布（基于 last_info_updated_at）
        candidate_records = Purchasing.objects.filter(
            Q(order_number__istartswith='w'),
            ~Q(latest_delivery_status__in=['配達完了', 'お届け先にお届け済み']),
            Q(shipping_method='JP LOGISTICS GROUP CO., LTD.'),
            # 防止重复发布：last_info_updated_at 为空或超过配置的时间间隔
            Q(last_info_updated_at__isnull=True) | Q(last_info_updated_at__lt=time_threshold)
        ).exclude(
            tracking_number__isnull=True
        ).exclude(
            tracking_number=''
        )[:100]  # Get 100 candidates for filtering
        
        self.logger.info(
            f"[{self.WORKER_NAME}] Found {len(candidate_records)} candidate records"
        )
        
        # Filter by tracking_number pattern (digits length = 12)
        # Also exclude records with tracking_number already in recent TrackingJob
        valid_records = []
        skipped_by_tracking_job = 0

        for record in candidate_records:
            # Extract all digits from tracking_number
            digits = re.sub(r'\D', '', record.tracking_number)

            # Check if digits length = 12
            if digits and len(digits) == 12:
                # Check if tracking_number already exists in recent TrackingJob
                # 检查是否在时间阈值内已有相同 tracking_number 的 TrackingJob
                recent_job_exists = TrackingJob.objects.filter(
                    batch__task_name=self.TASK_NAME,
                    batch__created_at__gte=time_threshold,
                    target_url__icontains=digits
                ).exists()

                if recent_job_exists:
                    skipped_by_tracking_job += 1
                    self.logger.debug(
                        f"[{self.WORKER_NAME}] Skipping {record.order_number}: "
                        f"tracking_number {digits} already in recent TrackingJob"
                    )
                    continue

                valid_records.append(record)

                # Stop when we have enough records
                if len(valid_records) >= self.MAX_RECORDS:
                    break

        self.logger.info(
            f"[{self.WORKER_NAME}] Filtered {len(valid_records)} valid records "
            f"with tracking numbers of length 12 "
            f"(skipped {skipped_by_tracking_job} due to recent TrackingJob)"
        )
        
        return valid_records
    
    def construct_url(self, tracking_numbers: List[str]) -> str:
        """
        Construct Japan Post tracking URL for up to 10 tracking numbers.
        
        Args:
            tracking_numbers: List of tracking numbers (max 10)
        
        Returns:
            Constructed URL string
        """
        # Ensure we have at most 10 tracking numbers
        tracking_numbers = tracking_numbers[:10]
        
        # Build parameters
        params = {}
        for i in range(1, 11):
            if i <= len(tracking_numbers):
                params[f'requestNo{i}'] = tracking_numbers[i-1]
            else:
                params[f'requestNo{i}'] = ''
        
        # Add random coordinates (anti-bot)
        params['search.x'] = str(random.randint(1, 173))
        params['search.y'] = str(random.randint(1, 45))
        params['startingUrlPatten'] = ''
        params['locale'] = 'ja'
        
        base_url = 'https://trackings.post.japanpost.jp/services/srv/search'
        url = f"{base_url}?{urlencode(params)}"
        
        return url
    
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
        from apps.data_aggregation.models import Purchasing
        from apps.data_acquisition.models import SyncLog, TrackingBatch, TrackingJob
        from django.conf import settings
        
        self.logger.info(f"[{self.WORKER_NAME}] Starting execution")
        
        try:
            # Step 1: Query matching records
            records = self.get_matching_records()
            
            if not records:
                self.logger.warning(f"[{self.WORKER_NAME}] No matching records found")
                
                SyncLog.objects.create(
                    operation_type='japan_post_tracking_10_tracking_number_completed',
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
            
            # Step 2: Extract tracking numbers
            tracking_data = []
            for record in records:
                digits = re.sub(r'\D', '', record.tracking_number)
                tracking_data.append({
                    'record_id': record.id,
                    'uuid': str(record.uuid),
                    'order_number': record.order_number,
                    'tracking_number': digits
                })
            
            # Step 3: Construct URL (max 10 tracking numbers)
            tracking_numbers = [item['tracking_number'] for item in tracking_data]
            url = self.construct_url(tracking_numbers)
            
            self.logger.info(
                f"[{self.WORKER_NAME}] Constructed URL with {len(tracking_numbers)} tracking numbers"
            )
            
            # Step 4: Create TrackingBatch
            batch_uuid = uuid.uuid4()
            batch_uuid_str = str(batch_uuid)
            batch_short = batch_uuid_str[:8]
            
            batch = TrackingBatch.objects.create(
                file_path=f'purchasing_query_{batch_short}',  # Virtual file path
                task_name=self.TASK_NAME,
                batch_uuid=batch_uuid,
                total_jobs=1,  # Only 1 URL
                status='pending'
            )
            
            self.logger.info(f"[{self.WORKER_NAME}] Created TrackingBatch {batch_short}")
            
            # Step 5: Publish task
            custom_id = f"jpt10-{batch_short}-purchasing"
            
            result = self.publish_task(
                url=url,
                batch_uuid_str=batch_uuid_str,
                custom_id=custom_id,
                index=0
            )

            self.logger.info(
                f"[{self.WORKER_NAME}] Published task: {custom_id} (task_id={result['task_id']})"
            )

            # Step 6: 立即更新所有记录的 last_info_updated_at 并锁定记录，防止重复发布
            from django.utils import timezone
            current_time = timezone.now()

            for record in records:
                record.last_info_updated_at = current_time
                record.is_locked = True
                record.locked_at = current_time
                record.locked_by_worker = 'JPT10'  # japan_post_tracking_10 任务名首字母
                record.save(update_fields=['last_info_updated_at', 'is_locked', 'locked_at', 'locked_by_worker'])

            self.logger.info(
                f"[{self.WORKER_NAME}] Updated last_info_updated_at and locked {len(records)} records"
            )

            # Step 7: Log to SyncLog
            SyncLog.objects.create(
                operation_type='japan_post_tracking_10_tracking_number_completed',
                message=f"Published 1 tracking task with {len(tracking_numbers)} tracking numbers",
                success=True,
                details={
                    'batch_uuid': batch_uuid_str,
                    'total_records': len(records),
                    'tracking_numbers': tracking_numbers,
                    'url': url,
                    'custom_id': custom_id,
                    'task_id': result['task_id']
                }
            )
            
            return {
                'status': 'success',
                'batch_uuid': batch_uuid_str,
                'total_records': len(records),
                'tracking_numbers': tracking_numbers,
                'url': url,
                'custom_id': custom_id,
                'task_id': result['task_id']
            }
        
        except Exception as exc:
            self.logger.error(
                f"[{self.WORKER_NAME}] Execution failed: {exc}",
                exc_info=True
            )
            
            SyncLog.objects.create(
                operation_type='japan_post_tracking_10_tracking_number_completed',
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
