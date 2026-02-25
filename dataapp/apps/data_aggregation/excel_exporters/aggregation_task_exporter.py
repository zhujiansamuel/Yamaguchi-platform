"""
AggregationTask Excel exporter.
AggregationTask模型的Excel导出器。
"""
from .base import BaseExcelExporter


class AggregationTaskExporter(BaseExcelExporter):
    """
    Excel exporter for AggregationTask model.
    """
    model_name = 'AggregationTask'

    def get_queryset(self):
        """
        Get the queryset for AggregationTask model.
        可以在这里自定义查询集，例如排序、过滤等。
        """
        model = self.get_model()
        return model.objects.all()

    def get_fields(self):
        """
        Explicitly define export fields for AggregationTask model.
        """
        return [
            'id',
            'task_id',
            'source',
            'status',
            'result',
            'error_message',
            'started_at',
            'completed_at',
            'created_at',
        ]

    def get_header_names(self):
        """
        Customize header names for AggregationTask export.
        可以在这里自定义表头名称。
        """
        # 默认使用字段名，可以根据需要自定义
        return {
            'id': 'ID',
            'task_id': 'Celery Task ID',
            'source': 'Aggregation Source',
            'status': 'Status',
            'result': 'Task Result',
            'error_message': 'Error Message',
            'started_at': 'Started At',
            'completed_at': 'Completed At',
            'created_at': 'Created At',
        }
