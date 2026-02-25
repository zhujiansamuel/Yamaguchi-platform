"""
GiftCard Excel exporter.
GiftCard模型的Excel导出器。
"""
from .base import BaseExcelExporter


class GiftCardExporter(BaseExcelExporter):
    """
    Excel exporter for GiftCard model.
    """
    model_name = 'GiftCard'

    def get_queryset(self):
        """
        Get the queryset for GiftCard model.
        可以在这里自定义查询集，例如排序、过滤等。
        """
        return super().get_queryset()

    def get_fields(self):
        """
        Explicitly define export fields for GiftCard model.
        """
        return [
            'id',
            'card_number',
            'alternative_name',
            'passkey1',
            'passkey2',
            'balance',
            'batch_encoding',
            'created_at',
            'updated_at',
            'is_deleted',
        ]

    def get_header_names(self):
        """
        Customize header names for GiftCard export.
        """
        return {
            'id': 'ID',
            'card_number': 'Card Number',
            'alternative_name': 'Alternative Name',
            'passkey1': 'Passkey 1',
            'passkey2': 'Passkey 2',
            'balance': 'Balance',
            'batch_encoding': 'Batch Encoding',
            'created_at': 'Created At',
            'updated_at': 'Updated At',
            'is_deleted': 'Is Deleted',
        }
