"""
Dashboard serializers for data_aggregation app.
"""
from rest_framework import serializers


class EmailBatchSerializer(serializers.Serializer):
    id = serializers.IntegerField(source='pk')
    created_at = serializers.DateTimeField()
    completed_at = serializers.DateTimeField()
    status = serializers.CharField()
    total_jobs = serializers.IntegerField(source='total_items')
    completed_jobs = serializers.IntegerField(source='completed_items')
    failed_jobs = serializers.IntegerField(source='failed_items')
    source = serializers.SerializerMethodField()
    detail = serializers.CharField()

    def get_source(self, obj):
        return 'email'


class EmailStageGroupSerializer(serializers.Serializer):
    stage = serializers.CharField()
    label = serializers.CharField()
    batches = EmailBatchSerializer(many=True)
