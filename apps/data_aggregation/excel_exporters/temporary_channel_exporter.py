"""
TemporaryChannel Excel exporter.
TemporaryChannel模型的Excel导出器。
"""
from .base import BaseExcelExporter


class TemporaryChannelExporter(BaseExcelExporter):
    """
    Excel exporter for TemporaryChannel model.
    """
    model_name = 'TemporaryChannel'

    def get_queryset(self):
        """
        Get the queryset for TemporaryChannel model.
        可以在这里自定义查询集，例如排序、过滤等。
        """
        return super().get_queryset()

    def get_fields(self):
        """
        Explicitly define export fields for TemporaryChannel model.
        """
        return [
            'id',
            'created_time',
            'expected_time',
            'record',
            'last_updated',
            'is_deleted',
        ]

    def get_header_names(self):
        """
        Customize header names for TemporaryChannel export.
        可以在这里自定义表头名称。
        """
        # 默认使用字段名，可以根据需要自定义
        return {
            'id': 'ID',
            'created_time': 'Created Time',
            'expected_time': 'Expected Time',
            'record': 'Record',
            'last_updated': 'Last Updated',
            'is_deleted': 'Is Deleted',
        }
