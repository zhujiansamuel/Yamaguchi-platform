"""
Models for data_acquisition app.
"""
from django.db import models
from django.utils import timezone
from apps.core.history import HistoricalRecordsWithSource


class DataSource(models.Model):
    """
    Represents an external data source for acquisition.
    """
    SOURCE_TYPE_CHOICES = [
        ('api', 'API'),
        ('database', 'Database'),
        ('file', 'File'),
        ('websocket', 'WebSocket'),
        ('other', 'Other'),
    ]

    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('error', 'Error'),
    ]

    name = models.CharField(max_length=255, unique=True, verbose_name='Source Name')
    source_type = models.CharField(max_length=20, choices=SOURCE_TYPE_CHOICES)
    description = models.TextField(blank=True, verbose_name='Description')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')

    # Connection configuration (API endpoint, DB credentials, etc.)
    config = models.JSONField(default=dict, verbose_name='Configuration')

    # Scheduling configuration
    fetch_interval = models.IntegerField(
        default=3600,
        help_text='Fetch interval in seconds'
    )
    last_fetched_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    history = HistoricalRecordsWithSource()

    class Meta:
        db_table = 'data_sources'
        verbose_name = 'Data Source'
        verbose_name_plural = 'Data Sources'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.source_type})"


class AcquiredData(models.Model):
    """
    Stores raw data acquired from external sources.
    """
    source = models.ForeignKey(
        DataSource,
        on_delete=models.CASCADE,
        related_name='acquired_data'
    )
    raw_data = models.JSONField(verbose_name='Raw Data')
    metadata = models.JSONField(default=dict, blank=True, verbose_name='Metadata')
    data_hash = models.CharField(max_length=64, blank=True, verbose_name='Data Hash')

    acquired_at = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)

    history = HistoricalRecordsWithSource()

    class Meta:
        db_table = 'acquired_data'
        verbose_name = 'Acquired Data'
        verbose_name_plural = 'Acquired Data'
        ordering = ['-acquired_at']
        indexes = [
            models.Index(fields=['-acquired_at']),
            models.Index(fields=['source', '-acquired_at']),
            models.Index(fields=['data_hash']),
        ]

    def __str__(self):
        return f"{self.source.name} - {self.acquired_at}"


class AcquisitionTask(models.Model):
    """
    Tracks data acquisition task execution.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    task_id = models.CharField(max_length=255, unique=True, verbose_name='Celery Task ID')
    source = models.ForeignKey(
        DataSource,
        on_delete=models.CASCADE,
        related_name='tasks',
        null=True,
        blank=True
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    result = models.JSONField(null=True, blank=True, verbose_name='Task Result')
    error_message = models.TextField(blank=True, verbose_name='Error Message')
    records_count = models.IntegerField(default=0, verbose_name='Records Acquired')

    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    history = HistoricalRecordsWithSource()

    class Meta:
        db_table = 'acquisition_tasks'
        verbose_name = 'Acquisition Task'
        verbose_name_plural = 'Acquisition Tasks'
        ordering = ['-created_at']

    def __str__(self):
        return f"Task {self.task_id} - {self.status}"


class NextcloudSyncState(models.Model):
    """
    Tracks synchronization state for Nextcloud Excel files.
    Records etag and last sync information for idempotency and deduplication.
    """
    MODEL_CHOICES = [
        ('Purchasing', 'Purchasing'),
        ('OfficialAccount', 'OfficialAccount'),
        ('GiftCard', 'GiftCard'),
        ('DebitCard', 'DebitCard'),
        ('CreditCard', 'CreditCard'),
        ('TemporaryChannel', 'TemporaryChannel'),
    ]

    # File identification
    model_name = models.CharField(
        max_length=50,
        choices=MODEL_CHOICES,
        verbose_name='Model Name',
        help_text='Django model being synced'
    )
    file_path = models.CharField(
        max_length=500,
        unique=True,
        verbose_name='File Path',
        help_text='Nextcloud file path (e.g., /Data/Purchasing_abc123.xlsx)'
    )

    # ETag tracking for idempotency
    last_etag = models.CharField(
        max_length=255,
        blank=True,
        verbose_name='Last ETag',
        help_text='ETag from last successful sync (for deduplication)'
    )
    last_modified = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Last Modified',
        help_text='File last modified timestamp from WebDAV'
    )

    # Sync tracking
    last_synced_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Last Synced At',
        help_text='Timestamp of last successful sync'
    )
    last_event_user = models.CharField(
        max_length=255,
        blank=True,
        verbose_name='Last Event User',
        help_text='Nextcloud user who triggered last event'
    )

    # Statistics
    total_syncs = models.IntegerField(
        default=0,
        verbose_name='Total Syncs',
        help_text='Total number of successful syncs'
    )
    total_conflicts = models.IntegerField(
        default=0,
        verbose_name='Total Conflicts',
        help_text='Total number of conflicts detected'
    )

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    history = HistoricalRecordsWithSource()

    class Meta:
        db_table = 'nextcloud_sync_states'
        verbose_name = 'Nextcloud Sync State'
        verbose_name_plural = 'Nextcloud Sync States'
        ordering = ['-last_synced_at']
        indexes = [
            models.Index(fields=['model_name']),
            models.Index(fields=['file_path']),
            models.Index(fields=['last_etag']),
            models.Index(fields=['-last_synced_at']),
        ]

    def __str__(self):
        return f"{self.model_name} - {self.file_path}"


class SyncConflict(models.Model):
    """
    Records version conflicts when Excel version doesn't match DB version.
    Requires manual resolution.
    """
    CONFLICT_TYPE_CHOICES = [
        ('version_mismatch', 'Version Mismatch'),
        ('concurrent_edit', 'Concurrent Edit'),
        ('validation_error', 'Validation Error'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending Resolution'),
        ('resolved', 'Resolved'),
        ('ignored', 'Ignored'),
    ]

    # Conflict identification
    sync_state = models.ForeignKey(
        NextcloudSyncState,
        on_delete=models.CASCADE,
        related_name='conflicts',
        verbose_name='Sync State'
    )
    conflict_type = models.CharField(
        max_length=30,
        choices=CONFLICT_TYPE_CHOICES,
        default='version_mismatch',
        verbose_name='Conflict Type'
    )

    # Record identification
    model_name = models.CharField(
        max_length=50,
        verbose_name='Model Name'
    )
    record_id = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='Record ID',
        help_text='Primary key of conflicting record'
    )

    # Conflict details
    excel_version = models.CharField(
        max_length=100,
        verbose_name='Excel Version',
        help_text='Version from Excel file'
    )
    db_version = models.CharField(
        max_length=100,
        verbose_name='DB Version',
        help_text='Version from database'
    )
    excel_data = models.JSONField(
        verbose_name='Excel Data',
        help_text='Data from Excel row'
    )
    db_data = models.JSONField(
        null=True,
        blank=True,
        verbose_name='DB Data',
        help_text='Current data in database'
    )

    # Resolution
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name='Status'
    )
    resolution_notes = models.TextField(
        blank=True,
        verbose_name='Resolution Notes'
    )
    resolved_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Resolved At'
    )
    resolved_by = models.CharField(
        max_length=255,
        blank=True,
        verbose_name='Resolved By'
    )

    # Metadata
    detected_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    history = HistoricalRecordsWithSource()

    class Meta:
        db_table = 'sync_conflicts'
        verbose_name = 'Sync Conflict'
        verbose_name_plural = 'Sync Conflicts'
        ordering = ['-detected_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['model_name', 'record_id']),
            models.Index(fields=['-detected_at']),
        ]

    def __str__(self):
        return f"{self.model_name} #{self.record_id} - {self.get_conflict_type_display()}"


class SyncLog(models.Model):
    """
    Logs all sync operations for audit trail and debugging.
    """
    OPERATION_TYPE_CHOICES = [
        ('webhook_received', 'Webhook Received'),
        ('sync_started', 'Sync Started'),
        ('sync_completed', 'Sync Completed'),
        ('sync_failed', 'Sync Failed'),
        ('record_created', 'Record Created'),
        ('record_updated', 'Record Updated'),
        ('record_deleted', 'Record Deleted'),
        ('conflict_detected', 'Conflict Detected'),
        ('excel_writeback', 'Excel Writeback'),
        ('writeback_skipped', 'Writeback Skipped'),
        ('onlyoffice_callback', 'OnlyOffice Callback'),
        ('onlyoffice_document_processed', 'OnlyOffice Document Processed'),
        ('onlyoffice_process_failed', 'OnlyOffice Process Failed'),
        ('onlyoffice_import_skipped', 'OnlyOffice Import Skipped'),
        ('onlyoffice_import_completed', 'OnlyOffice Import Completed'),
        ('onlyoffice_missing_url', 'OnlyOffice Missing URL'),
        ('nextcloud_forward_failed', 'Nextcloud Forward Failed'),
        # Tracking task operation types
        ('official_website_redirect_to_yamato_tracking_triggered', 'OWRYT Tracking Triggered'),
        ('official_website_redirect_to_yamato_tracking_completed', 'OWRYT Tracking Completed'),
        ('redirect_to_japan_post_tracking_triggered', 'Redirect to Japan Post Tracking Triggered'),
        ('redirect_to_japan_post_tracking_completed', 'Redirect to Japan Post Tracking Completed'),
        ('official_website_tracking_triggered', 'Official Website Tracking Triggered'),
        ('official_website_tracking_completed', 'Official Website Tracking Completed'),
        ('yamato_tracking_only_triggered', 'Yamato Tracking Only Triggered'),
        ('yamato_tracking_only_completed', 'Yamato Tracking Only Completed'),
        ('japan_post_tracking_only_triggered', 'Japan Post Tracking Only Triggered'),
        ('japan_post_tracking_only_completed', 'Japan Post Tracking Only Completed'),
    ]

    # Log details
    sync_state = models.ForeignKey(
        NextcloudSyncState,
        on_delete=models.CASCADE,
        related_name='logs',
        null=True,
        blank=True,
        verbose_name='Sync State'
    )
    operation_type = models.CharField(
        max_length=60,
        choices=OPERATION_TYPE_CHOICES,
        verbose_name='Operation Type'
    )

    # Context
    celery_task_id = models.CharField(
        max_length=255,
        blank=True,
        verbose_name='Celery Task ID'
    )
    file_path = models.CharField(
        max_length=500,
        blank=True,
        verbose_name='File Path'
    )
    etag = models.CharField(
        max_length=255,
        blank=True,
        verbose_name='ETag'
    )

    # Details
    message = models.TextField(
        verbose_name='Message',
        help_text='Log message'
    )
    details = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='Details',
        help_text='Additional details (JSON)'
    )

    # Status
    success = models.BooleanField(
        default=True,
        verbose_name='Success'
    )
    error_message = models.TextField(
        blank=True,
        verbose_name='Error Message'
    )

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)

    history = HistoricalRecordsWithSource()

    class Meta:
        db_table = 'sync_logs'
        verbose_name = 'Sync Log'
        verbose_name_plural = 'Sync Logs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['operation_type']),
            models.Index(fields=['success']),
            models.Index(fields=['-created_at']),
            models.Index(fields=['celery_task_id']),
        ]

    def __str__(self):
        status = "✓" if self.success else "✗"
        return f"{status} {self.get_operation_type_display()} - {self.created_at.strftime('%Y-%m-%d %H:%M:%S')}"


class TrackingBatch(models.Model):
    """
    追踪批次模型

    用于追踪一个 Excel 文件中所有 URL 的爬取任务完成状态。
    每当用户在 Nextcloud 保存一个追踪 Excel 文件时，系统会：
    1. 创建一个 TrackingBatch 记录（阶段二）
    2. 为每个 URL 创建一个 TrackingJob 记录
    3. 当 WebScraper 完成爬取并回调时，更新对应的 TrackingJob（阶段五）
    4. 系统自动计算批次完成度

    示例场景：
    - 用户上传包含 100 个 URL 的 OWRYT-20260108-001.xlsx
    - 系统创建 1 个 TrackingBatch + 100 个 TrackingJob
    - 可实时查询：已完成 85/100 (85%)
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),           # 刚创建，爬虫任务正在创建中
        ('processing', 'Processing'),     # 至少有一个 job 已完成
        ('completed', 'Completed'),       # 所有 job 都已完成
        ('partial', 'Partial Complete'),  # 部分 job 完成，但有失败的
    ]

    # 批次标识
    batch_uuid = models.UUIDField(
        unique=True,
        db_index=True,
        verbose_name='Batch UUID',
        help_text='批次唯一标识符'
    )

    # 任务信息
    task_name = models.CharField(
        max_length=100,
        db_index=True,
        verbose_name='Task Name',
        help_text='任务类型（如 official_website_redirect_to_yamato_tracking）'
    )
    file_path = models.CharField(
        max_length=500,
        verbose_name='File Path',
        help_text='Nextcloud 文件路径'
    )
    celery_task_id = models.CharField(
        max_length=255,
        blank=True,
        verbose_name='Celery Task ID',
        help_text='阶段二的 Celery 任务 ID'
    )

    # 进度统计
    total_jobs = models.IntegerField(
        default=0,
        verbose_name='Total Jobs',
        help_text='总任务数（成功创建的爬虫任务数）'
    )
    completed_jobs = models.IntegerField(
        default=0,
        verbose_name='Completed Jobs',
        help_text='已完成任务数'
    )
    failed_jobs = models.IntegerField(
        default=0,
        verbose_name='Failed Jobs',
        help_text='失败任务数'
    )

    # 状态
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        db_index=True,
        verbose_name='Status'
    )

    # 时间戳
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        verbose_name='Created At'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Updated At'
    )
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Completed At',
        help_text='所有任务完成的时间'
    )

    # Excel 回写状态
    writeback_triggered = models.BooleanField(
        default=False,
        verbose_name='Writeback Triggered',
        help_text='是否已触发批量回写任务'
    )
    writeback_completed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Writeback Completed At',
        help_text='批量回写完成时间'
    )

    history = HistoricalRecordsWithSource()

    class Meta:
        db_table = 'acquisition_tracking_batch'
        verbose_name = 'Tracking Batch'
        verbose_name_plural = 'Tracking Batches'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['task_name', 'status', '-created_at']),
            models.Index(fields=['status', '-created_at']),
        ]

    def __str__(self):
        return f"{self.task_name} - {self.batch_uuid} ({self.completed_jobs}/{self.total_jobs})"

    def update_progress(self):
        """
        更新批次进度和状态

        此方法会：
        1. 重新计算 completed_jobs 和 failed_jobs
        2. 考虑 redirected 任务的完成状态
        3. 更新 status
        4. 如果全部完成，设置 completed_at
        5. 每 10 个任务完成时触发一次批量回写
        6. 批次完成时触发最后一次回写（处理不满 10 个的情况）
        """
        from django.db.models import Q
        import logging

        logger = logging.getLogger(__name__)

        # 保存旧的 completed_jobs，用于判断是否跨越了 10 的倍数里程碑
        old_completed = self.completed_jobs

        # 计算直接完成的任务数
        direct_completed = self.jobs.filter(status='completed').count()

        # 计算 redirected 任务中，对应的 japan_post 任务已完成的数量
        redirected_jobs = self.jobs.filter(status='redirected')
        redirected_completed = 0

        for redirected_job in redirected_jobs:
            # 构建对应的 japan_post 任务的 custom_id
            jpt_custom_id = f"jpt-from-owryt-{redirected_job.custom_id}"
            # 查找对应的 japan_post 任务
            jpt_job = self.jobs.filter(custom_id=jpt_custom_id, status='completed').first()
            if jpt_job:
                redirected_completed += 1

        # 有效完成数 = 直接完成 + redirected中对应japan_post已完成
        new_completed = direct_completed + redirected_completed
        self.completed_jobs = new_completed
        self.failed_jobs = self.jobs.filter(status='failed').count()

        # 更新状态
        batch_just_completed = False
        if self.completed_jobs + self.failed_jobs >= self.total_jobs and self.total_jobs > 0:
            if self.failed_jobs == 0:
                self.status = 'completed'
            else:
                self.status = 'partial'
            if not self.completed_at:
                self.completed_at = timezone.now()
                batch_just_completed = True
        elif self.completed_jobs > 0 or self.failed_jobs > 0:
            self.status = 'processing'

        self.save()

        # ============================================================================
        # 批量回写逻辑：每 10 个任务完成时触发一次，批次完成时触发最后一次
        # 写入顺序示例：25 个任务 → 10 → 20 → 25（完成时）
        # ============================================================================
        # 检查是否跨越了新的 10 的倍数里程碑
        crossed_milestone = (new_completed // 10 > old_completed // 10) and new_completed > 0

        if crossed_milestone or batch_just_completed:
            trigger_reason = "milestone_10" if crossed_milestone else "batch_completed"

            # 只有当 file_path 不为空时才触发 Excel 回写
            # yamato_tracking_10_tracking_number 等直接更新数据库的任务不需要 Excel 回写
            if self.file_path and self.file_path.strip():
                logger.info(
                    f"Batch {self.batch_uuid}: triggering writeback at {new_completed} completed "
                    f"(reason: {trigger_reason}, old: {old_completed}, file: {self.file_path})"
                )

                # 异步触发批量回写任务
                from .tasks import batch_writeback_tracking_data
                batch_writeback_tracking_data.apply_async(
                    args=[str(self.batch_uuid)],
                    countdown=5  # 延迟 5 秒执行，确保所有数据已经落库
                )

                # 如果是批次完成，标记 writeback_triggered
                if batch_just_completed:
                    self.writeback_triggered = True
                    self.save(update_fields=['writeback_triggered'])
            else:
                logger.info(
                    f"Batch {self.batch_uuid}: skipping writeback at {new_completed} completed "
                    f"(reason: {trigger_reason}, no file_path, task handles data directly)"
                )

    @property
    def completion_percentage(self):
        """完成百分比"""
        if self.total_jobs == 0:
            return 0.0
        return round((self.completed_jobs / self.total_jobs) * 100, 2)

    @property
    def pending_jobs(self):
        """待处理任务数"""
        return self.total_jobs - self.completed_jobs - self.failed_jobs

    @property
    def is_completed(self):
        """是否已完成（包括全部成功或部分失败）"""
        return self.status in ['completed', 'partial']


class TrackingJob(models.Model):
    """
    单个追踪任务模型

    代表一个 WebScraper 爬虫任务。
    关联到一个 TrackingBatch，记录单个 URL 的爬取状态。

    生命周期：
    1. 阶段二：创建时 status='pending'
    2. 阶段五：WebScraper 回调时更新为 'completed' 或 'failed'
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),      # 等待 WebScraper 完成
        ('completed', 'Completed'),  # 已完成并成功处理
        ('failed', 'Failed'),        # 处理失败
        ('redirected', 'Redirected'), # 已重定向到其他追踪任务
    ]

    # 关联
    batch = models.ForeignKey(
        TrackingBatch,
        related_name='jobs',
        on_delete=models.CASCADE,
        verbose_name='Batch',
        help_text='所属批次'
    )

    # 任务标识
    job_id = models.CharField(
        max_length=100,
        unique=True,
        db_index=True,
        null=True,
        blank=True,
        verbose_name='WebScraper Job ID',
        help_text='WebScraper 返回的 job_id（如果 API 返回了）'
    )
    custom_id = models.CharField(
        max_length=200,
        db_index=True,
        verbose_name='Custom ID',
        help_text='自定义 ID，格式：{prefix}-{batch_uuid_short}-{序号}'
    )

    # 目标信息
    target_url = models.TextField(
        verbose_name='Target URL',
        help_text='要爬取的目标 URL'
    )
    index = models.IntegerField(
        verbose_name='Index',
        help_text='在 Excel 中的序号（从 0 开始）'
    )

    # 状态
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        db_index=True,
        verbose_name='Status'
    )
    error_message = models.TextField(
        blank=True,
        verbose_name='Error Message',
        help_text='错误信息（如果失败）'
    )

    # Excel 回写数据
    writeback_data = models.TextField(
        blank=True,
        verbose_name='Writeback Data',
        help_text='提取的回写数据（用｜｜｜分隔）'
    )

    # 时间戳
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Created At'
    )
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Completed At',
        help_text='完成时间（成功或失败）'
    )

    history = HistoricalRecordsWithSource()

    class Meta:
        db_table = 'acquisition_tracking_job'
        verbose_name = 'Tracking Job'
        verbose_name_plural = 'Tracking Jobs'
        ordering = ['batch', 'index']
        indexes = [
            models.Index(fields=['batch', 'status']),
            models.Index(fields=['custom_id']),
        ]

    def __str__(self):
        return f"Job {self.custom_id} - {self.status}"

    def mark_completed(self):
        """标记为已完成"""
        self.status = 'completed'
        if not self.completed_at:
            self.completed_at = timezone.now()
        self.save()

        # 更新批次进度
        self.batch.update_progress()

    def mark_failed(self, error_message=''):
        """标记为失败"""
        self.status = 'failed'
        self.error_message = error_message
        if not self.completed_at:
            self.completed_at = timezone.now()
        self.save()

        # 更新批次进度
        self.batch.update_progress()

    def mark_redirected(self):
        """标记为已重定向"""
        self.status = 'redirected'
        if not self.completed_at:
            self.completed_at = timezone.now()
        self.save()

        # 更新批次进度
        self.batch.update_progress()
