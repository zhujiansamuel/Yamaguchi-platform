"""
Dashboard serializers for data_acquisition app.
"""
from rest_framework import serializers


class NextcloudSyncEventSerializer(serializers.Serializer):
    id = serializers.IntegerField(source='pk')
    direction = serializers.SerializerMethodField()
    timestamp = serializers.DateTimeField(source='created_at')
    record_count = serializers.SerializerMethodField()
    conflict_count = serializers.SerializerMethodField()
    trigger = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    detail = serializers.SerializerMethodField()

    def get_direction(self, obj):
        if obj.operation_type in ('sync_completed', 'sync_failed'):
            return 'in'
        return 'out'

    def get_record_count(self, obj):
        return obj.details.get('record_count', 0) if obj.details else 0

    def get_conflict_count(self, obj):
        return obj.details.get('conflict_count', 0) if obj.details else 0

    def get_trigger(self, obj):
        return obj.details.get('trigger', 'unknown') if obj.details else 'unknown'

    def get_status(self, obj):
        return 'success' if obj.success else 'error'

    def get_detail(self, obj):
        if obj.details:
            return obj.details.get('detail', '')
        return ''


class NextcloudSyncGroupSerializer(serializers.Serializer):
    model_name = serializers.CharField()
    events = NextcloudSyncEventSerializer(many=True)


class TrackingBatchEventSerializer(serializers.Serializer):
    id = serializers.UUIDField(source='batch_uuid')
    created_at = serializers.DateTimeField()
    completed_at = serializers.DateTimeField()
    status = serializers.SerializerMethodField()
    total_jobs = serializers.IntegerField()
    completed_jobs = serializers.IntegerField()
    failed_jobs = serializers.IntegerField()
    source = serializers.CharField(source='source_type')
    detail = serializers.SerializerMethodField()

    STATUS_MAP = {
        'pending': 'pending',
        'processing': 'running',
        'completed': 'success',
        'partial': 'error',
    }

    def get_status(self, obj):
        return self.STATUS_MAP.get(obj.status, obj.status)

    def get_detail(self, obj):
        prefix = obj.file_path.split('/')[-1].split('.')[0] if obj.file_path else obj.task_name
        date_str = obj.created_at.strftime('%Y%m%d') if obj.created_at else ''
        return f"{prefix}-{date_str} 共 {obj.total_jobs} 条"


class TrackingBatchGroupSerializer(serializers.Serializer):
    task_name = serializers.CharField()
    source_type = serializers.CharField()
    label = serializers.CharField()
    batches = TrackingBatchEventSerializer(many=True)
