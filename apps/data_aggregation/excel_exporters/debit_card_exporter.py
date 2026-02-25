"""
DebitCard Excel exporter.
DebitCard模型的Excel导出器。
"""
from .base import BaseExcelExporter


class DebitCardExporter(BaseExcelExporter):
    """
    Excel exporter for DebitCard model.
    """
    model_name = 'DebitCard'

    def get_queryset(self):
        """
        Get the queryset for DebitCard model.
        可以在这里自定义查询集，例如排序、过滤等。
        """
        return super().get_queryset()

    def get_fields(self):
        """
        Explicitly define export fields for DebitCard model.
        """
        return [
            'id',
            'card_number',
            'alternative_name',
            'expiry_month',
            'expiry_year',
            'passkey',
            'last_balance_update',
            'balance',
            'batch_encoding',
            'created_at',
            'updated_at',
            'is_deleted',
        ]

    def get_header_names(self):
        """
        Customize header names for DebitCard export.
        """
        return {
            'id': 'ID',
            'card_number': 'Card Number',
            'alternative_name': 'Alternative Name',
            'expiry_month': 'Expiry Month',
            'expiry_year': 'Expiry Year',
            'passkey': 'Passkey',
            'last_balance_update': 'Last Balance Update',
            'balance': 'Balance',
            'batch_encoding': 'Batch Encoding',
            'created_at': 'Created At',
            'updated_at': 'Updated At',
            'is_deleted': 'Is Deleted',
        }
