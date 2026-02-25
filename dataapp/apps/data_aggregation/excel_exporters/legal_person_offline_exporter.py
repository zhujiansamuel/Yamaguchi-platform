"""
LegalPersonOffline Excel exporter.
LegalPersonOffline模型的Excel导出器。
"""
from .base import BaseExcelExporter


class LegalPersonOfflineExporter(BaseExcelExporter):
    """
    Excel exporter for LegalPersonOffline model.
    """
    model_name = 'LegalPersonOffline'

    def get_queryset(self):
        """
        Get the queryset for LegalPersonOffline model.
        可以在这里自定义查询集，例如排序、过滤等。
        """
        return super().get_queryset()

    def get_fields(self):
        """
        Explicitly define export fields for LegalPersonOffline model.
        """
        return [
            'id',
            'uuid',
            'username',
            'appointment_time',
            'visit_time',
            'order_created_at',
            'updated_at',
            'is_deleted',
            'creation_source',
        ]

    def get_header_names(self):
        """
        Customize header names for LegalPersonOffline export.
        可以在这里自定义表头名称。
        """
        # 默认使用字段名，可以根据需要自定义
        return {
            'id': 'ID',
            'uuid': 'UUID',
            'username': 'Username',
            'appointment_time': 'Appointment Time',
            'visit_time': 'Visit Time',
            'order_created_at': 'Order Created At',
            'updated_at': 'Updated At',
            'is_deleted': 'Is Deleted',
            'creation_source': 'Creation Source',
        }
