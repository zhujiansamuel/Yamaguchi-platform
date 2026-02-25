"""
AggregatedData Excel exporter.
AggregatedData模型的Excel导出器。
"""
from .base import BaseExcelExporter


class AggregatedDataExporter(BaseExcelExporter):
    """
    Excel exporter for AggregatedData model.
    """
    model_name = 'AggregatedData'

    def get_queryset(self):
        """
        Get the queryset for AggregatedData model.
        可以在这里自定义查询集，例如排序、过滤等。
        """
        model = self.get_model()
        return model.objects.all()

    def get_fields(self):
        """
        Explicitly define export fields for AggregatedData model.
        """
        return [
            'id',
            'source',
            'data',
            'metadata',
            'aggregated_at',
            'created_at',
        ]

    def get_header_names(self):
        """
        Customize header names for AggregatedData export.
        可以在这里自定义表头名称。
        """
        # 默认使用字段名，可以根据需要自定义
        return {
            'id': 'ID',
            'source': 'Aggregation Source',
            'data': 'Aggregated Data',
            'metadata': 'Metadata',
            'aggregated_at': 'Aggregated At',
            'created_at': 'Created At',
        }
