"""
OtherPayment Excel exporter.
OtherPayment模型的Excel导出器。
"""
from .base import BaseExcelExporter


class OtherPaymentExporter(BaseExcelExporter):
    """
    Excel exporter for OtherPayment model.
    """
    model_name = 'OtherPayment'

    def get_queryset(self):
        """
        Get the queryset for OtherPayment model.
        可以在这里自定义查询集，例如排序、过滤等。
        """
        model = self.get_model()
        return model.objects.all()

    def get_fields(self):
        """
        Explicitly define export fields for OtherPayment model.
        """
        return [
            'id',
            'purchasing',
            'payment_info',
            'payment_amount',
            'payment_time',
            'payment_status',
            'created_at',
            'updated_at',
        ]

    def get_header_names(self):
        """
        Customize header names for OtherPayment export.
        可以在这里自定义表头名称。
        """
        # 默认使用字段名，可以根据需要自定义
        return {
            'id': 'ID',
            'purchasing': 'Purchasing Order',
            'payment_info': 'Payment Info',
            'payment_amount': 'Payment Amount',
            'payment_time': 'Payment Time',
            'payment_status': 'Payment Status',
            'created_at': 'Created At',
            'updated_at': 'Updated At',
        }
