"""
AggregationSource Excel exporter.
AggregationSource模型的Excel导出器。
"""
from .base import BaseExcelExporter


class AggregationSourceExporter(BaseExcelExporter):
    """
    Excel exporter for AggregationSource model.
    """
    model_name = 'AggregationSource'

    def get_queryset(self):
        """
        Get the queryset for AggregationSource model.
        可以在这里自定义查询集，例如排序、过滤等。
        """
        model = self.get_model()
        return model.objects.all()

    def get_fields(self):
        """
        Explicitly define export fields for AggregationSource model.
        """
        return [
            'id',
            'name',
            'description',
            'status',
            'config',
            'created_at',
            'updated_at',
        ]

    def get_header_names(self):
        """
        Customize header names for AggregationSource export.
        可以在这里自定义表头名称。
        """
        # 默认使用字段名，可以根据需要自定义
        return {
            'id': 'ID',
            'name': 'Source Name',
            'description': 'Description',
            'status': 'Status',
            'config': 'Configuration',
            'created_at': 'Created At',
            'updated_at': 'Updated At',
        }
