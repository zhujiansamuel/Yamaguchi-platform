"""
CreditCard Excel exporter.
CreditCard模型的Excel导出器。
"""
from .base import BaseExcelExporter


class CreditCardExporter(BaseExcelExporter):
    """
    Excel exporter for CreditCard model.
    """
    model_name = 'CreditCard'

    def get_queryset(self):
        """
        Get the queryset for CreditCard model.
        可以在这里自定义查询集，例如排序、过滤等。
        """
        return super().get_queryset()

    def get_fields(self):
        """
        Explicitly define export fields for CreditCard model.
        """
        return [
            'id',
            'card_number',
            'alternative_name',
            'expiry_month',
            'expiry_year',
            'passkey',
            'last_balance_update',
            'credit_limit',
            'batch_encoding',
            'created_at',
            'updated_at',
            'is_deleted',
        ]

    def get_header_names(self):
        """
        Customize header names for CreditCard export.
        """
        return {
            'id': 'ID',
            'card_number': 'Card Number',
            'alternative_name': 'Alternative Name',
            'expiry_month': 'Expiry Month',
            'expiry_year': 'Expiry Year',
            'passkey': 'Passkey',
            'last_balance_update': 'Last Balance Update',
            'credit_limit': 'Credit Limit',
            'batch_encoding': 'Batch Encoding',
            'created_at': 'Created At',
            'updated_at': 'Updated At',
            'is_deleted': 'Is Deleted',
        }
