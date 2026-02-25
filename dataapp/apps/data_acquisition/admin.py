"""
Admin configuration for data_acquisition app.
"""
from django.contrib import admin
from apps.core.admin import BaseHistoryAdmin
from .models import (
    DataSource, AcquiredData, AcquisitionTask,
    NextcloudSyncState, SyncConflict, SyncLog,
    TrackingBatch, TrackingJob
)


@admin.register(DataSource)
class DataSourceAdmin(BaseHistoryAdmin):
    list_display = ['name', 'source_type', 'status', 'last_fetched_at', 'created_at']
    list_filter = ['source_type', 'status', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at', 'last_fetched_at']


@admin.register(AcquiredData)
class AcquiredDataAdmin(BaseHistoryAdmin):
    list_display = ['source', 'data_hash', 'acquired_at', 'created_at']
    list_filter = ['source', 'acquired_at']
    search_fields = ['source__name', 'data_hash']
    readonly_fields = ['created_at']
    date_hierarchy = 'acquired_at'


@admin.register(AcquisitionTask)
class AcquisitionTaskAdmin(BaseHistoryAdmin):
    list_display = ['task_id', 'source', 'status', 'records_count', 'started_at', 'completed_at']
    list_filter = ['status', 'created_at']
    search_fields = ['task_id', 'source__name']
    readonly_fields = ['created_at', 'started_at', 'completed_at']


@admin.register(NextcloudSyncState)
class NextcloudSyncStateAdmin(BaseHistoryAdmin):
    list_display = [
        'model_name', 'file_path', 'last_synced_at', 'total_syncs',
        'total_conflicts', 'last_event_user'
    ]
    list_filter = ['model_name', 'last_synced_at']
    search_fields = ['file_path', 'last_event_user']
    readonly_fields = ['created_at', 'updated_at', 'last_synced_at']
    fieldsets = (
        ('File Information', {
            'fields': ('model_name', 'file_path')
        }),
        ('Sync State', {
            'fields': ('last_etag', 'last_modified', 'last_synced_at', 'last_event_user')
        }),
        ('Statistics', {
            'fields': ('total_syncs', 'total_conflicts')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(SyncConflict)
class SyncConflictAdmin(BaseHistoryAdmin):
    list_display = [
        'model_name', 'record_id', 'conflict_type', 'status',
        'detected_at', 'resolved_at'
    ]
    list_filter = ['conflict_type', 'status', 'model_name', 'detected_at']
    search_fields = ['model_name', 'record_id', 'resolution_notes']
    readonly_fields = ['detected_at', 'updated_at']
    date_hierarchy = 'detected_at'
    fieldsets = (
        ('Conflict Information', {
            'fields': ('sync_state', 'conflict_type', 'model_name', 'record_id')
        }),
        ('Version Details', {
            'fields': ('excel_version', 'db_version', 'excel_data', 'db_data')
        }),
        ('Resolution', {
            'fields': ('status', 'resolution_notes', 'resolved_at', 'resolved_by')
        }),
        ('Metadata', {
            'fields': ('detected_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(SyncLog)
class SyncLogAdmin(BaseHistoryAdmin):
    list_display = [
        'operation_type', 'file_path', 'success', 'created_at','message',
        'celery_task_id'
    ]
    list_filter = ['operation_type', 'success', 'created_at']
    search_fields = ['file_path', 'celery_task_id', 'message', 'error_message']
    readonly_fields = ['created_at']
    date_hierarchy = 'created_at'
    fieldsets = (
        ('Log Information', {
            'fields': ('operation_type', 'sync_state', 'success')
        }),
        ('Context', {
            'fields': ('celery_task_id', 'file_path', 'etag')
        }),
        ('Details', {
            'fields': ('message', 'details', 'error_message')
        }),
        ('Metadata', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )


class TrackingJobInline(admin.TabularInline):
    """
    Inline admin for TrackingJob within TrackingBatch.
    """
    model = TrackingJob
    extra = 0
    readonly_fields = ['job_id', 'custom_id', 'target_url', 'index', 'status', 'completed_at', 'created_at']
    fields = ['custom_id', 'job_id', 'target_url', 'index', 'status', 'completed_at']
    show_change_link = True
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(TrackingBatch)
class TrackingBatchAdmin(BaseHistoryAdmin):
    """
    Admin interface for TrackingBatch model.
    追踪批次管理界面。
    """
    list_display = [
        'batch_uuid_short', 'task_name', 'status', 'progress_display',
        'completed_jobs', 'failed_jobs', 'total_jobs', 'created_at', 'completed_at'
    ]
    list_filter = ['task_name', 'status', 'created_at', 'completed_at']
    search_fields = ['batch_uuid', 'task_name', 'file_path', 'celery_task_id']
    readonly_fields = [
        'batch_uuid', 'created_at', 'updated_at', 'completed_at',
        'completed_jobs', 'failed_jobs', 'completion_percentage'
    ]
    inlines = [TrackingJobInline]

    fieldsets = (
        ('Batch Information', {
            'fields': ('batch_uuid', 'task_name', 'file_path', 'celery_task_id')
        }),
        ('Progress', {
            'fields': ('status', 'total_jobs', 'completed_jobs', 'failed_jobs', 'completion_percentage')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'completed_at'),
            'classes': ('collapse',)
        }),
    )

    date_hierarchy = 'created_at'

    def batch_uuid_short(self, obj):
        """Display shortened batch UUID"""
        return str(obj.batch_uuid)[:8] + '...'
    batch_uuid_short.short_description = 'Batch UUID'

    def progress_display(self, obj):
        """Display progress percentage"""
        return f"{obj.completion_percentage}%"
    progress_display.short_description = 'Progress'


@admin.register(TrackingJob)
class TrackingJobAdmin(BaseHistoryAdmin):
    """
    Admin interface for TrackingJob model.
    追踪任务管理界面。
    """
    list_display = [
        'custom_id', 'job_id', 'batch_link', 'status', 'index',
        'target_url_short', 'created_at', 'completed_at'
    ]
    list_filter = ['status', 'batch__task_name', 'created_at', 'completed_at']
    search_fields = ['job_id', 'custom_id', 'target_url', 'batch__batch_uuid']
    readonly_fields = ['created_at', 'completed_at']
    raw_id_fields = ['batch']

    fieldsets = (
        ('Job Information', {
            'fields': ('batch', 'job_id', 'custom_id', 'index')
        }),
        ('Target', {
            'fields': ('target_url',)
        }),
        ('Status', {
            'fields': ('status', 'error_message')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'completed_at'),
            'classes': ('collapse',)
        }),
    )

    date_hierarchy = 'created_at'

    def batch_link(self, obj):
        """Display batch UUID with link"""
        return str(obj.batch.batch_uuid)[:8] + '...'
    batch_link.short_description = 'Batch'

    def target_url_short(self, obj):
        """Display shortened target URL"""
        if len(obj.target_url) > 50:
            return obj.target_url[:50] + '...'
        return obj.target_url
    target_url_short.short_description = 'Target URL'
