"""
DebitCardPayment Excel exporter.
DebitCardPayment模型的Excel导出器。
"""
from .base import BaseExcelExporter


class DebitCardPaymentExporter(BaseExcelExporter):
    """
    Excel exporter for DebitCardPayment model.
    """
    model_name = 'DebitCardPayment'

    def get_queryset(self):
        """
        Get the queryset for DebitCardPayment model.
        可以在这里自定义查询集，例如排序、过滤等。
        """
        return super().get_queryset()

    def get_fields(self):
        """
        Explicitly define export fields for DebitCardPayment model.
        """
        return [
            'id',
            'debit_card',
            'purchasing',
            'payment_amount',
            'payment_time',
            'payment_status',
            'created_at',
            'updated_at',
            'is_deleted',
        ]

    def get_header_names(self):
        """
        Customize header names for DebitCardPayment export.
        可以在这里自定义表头名称。
        """
        # 默认使用字段名，可以根据需要自定义
        return {
            'id': 'ID',
            'debit_card': 'Debit Card',
            'purchasing': 'Purchasing Order',
            'payment_amount': 'Payment Amount',
            'payment_time': 'Payment Time',
            'payment_status': 'Payment Status',
            'created_at': 'Created At',
            'updated_at': 'Updated At',
            'is_deleted': 'Is Deleted',
        }
