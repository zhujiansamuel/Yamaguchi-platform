"""
iPad Excel exporter.
iPad模型的Excel导出器。
"""
from .base import BaseExcelExporter


class iPadExporter(BaseExcelExporter):
    """
    Excel exporter for iPad model.
    """
    model_name = 'iPad'

    def get_queryset(self):
        """
        Get the queryset for iPad model.
        可以在这里自定义查询集，例如排序、过滤等。
        """
        return super().get_queryset()

    def get_fields(self):
        """
        Explicitly define export fields for iPad model.
        """
        return [
            'id',
            'part_number',
            'model_name',
            'capacity_gb',
            'color',
            'release_date',
            'jan',
            'created_at',
            'updated_at',
            'is_deleted',
        ]

    def get_header_names(self):
        """
        Customize header names for iPad export.
        可以在这里自定义表头名称。
        """
        # 默认使用字段名，可以根据需要自定义
        return {
            'id': 'ID',
            'part_number': 'Part Number',
            'model_name': 'Model Name',
            'capacity_gb': 'Capacity (GB)',
            'color': 'Color',
            'release_date': 'Release Date',
            'jan': 'JAN Code',
            'created_at': 'Created At',
            'updated_at': 'Updated At',
            'is_deleted': 'Is Deleted',
        }
