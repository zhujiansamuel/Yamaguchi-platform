"""
EcSite Excel exporter.
EcSite模型的Excel导出器。
"""
from .base import BaseExcelExporter


class EcSiteExporter(BaseExcelExporter):
    """
    Excel exporter for EcSite model.
    """
    model_name = 'EcSite'

    def get_queryset(self):
        """
        Get the queryset for EcSite model.
        可以在这里自定义查询集，例如排序、过滤等。
        """
        return super().get_queryset()

    def get_fields(self):
        """
        Explicitly define export fields for EcSite model.
        """
        return [
            'id',
            'reservation_number',
            'username',
            'method',
            'reservation_time',
            'visit_time',
            'order_created_at',
            'info_updated_at',
            'order_detail_url',
            'created_at',
            'updated_at',
            'is_deleted',
        ]

    def get_header_names(self):
        """
        Customize header names for EcSite export.
        可以在这里自定义表头名称。
        """
        # 默认使用字段名，可以根据需要自定义
        return {
            'id': 'ID',
            'reservation_number': 'Reservation Number',
            'username': 'Username',
            'method': 'Method',
            'reservation_time': 'Reservation Time',
            'visit_time': 'Visit Time',
            'order_created_at': 'Order Created At',
            'info_updated_at': 'Info Updated At',
            'order_detail_url': 'Order Detail URL',
            'created_at': 'Created At',
            'updated_at': 'Updated At',
            'is_deleted': 'Is Deleted',
        }
