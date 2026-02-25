"""
OfficialAccount Excel exporter.
OfficialAccount模型的Excel导出器。
"""
from .base import BaseExcelExporter


class OfficialAccountExporter(BaseExcelExporter):
    """
    Excel exporter for OfficialAccount model.
    """
    model_name = 'OfficialAccount'

    def get_queryset(self):
        """
        Get the queryset for OfficialAccount model.
        可以在这里自定义查询集，例如排序、过滤等。
        """
        return super().get_queryset()

    def get_fields(self):
        """
        Explicitly define export fields for OfficialAccount model.
        """
        return [
            'id',
            'uuid',
            'account_id',
            'email',
            'name',
            'postal_code',
            'address_line_1',
            'address_line_2',
            'address_line_3',
            'passkey',
            'batch_encoding',
            'created_at',
            'updated_at',
            'is_deleted',
        ]

    def get_header_names(self):
        """
        Customize header names for OfficialAccount export.
        可以在这里自定义表头名称。
        """
        # 默认使用字段名，可以根据需要自定义
        return {
            'id': 'ID',
            'uuid': 'UUID',
            'account_id': 'Account ID',
            'email': 'Email',
            'name': 'Name',
            'postal_code': 'Postal Code',
            'address_line_1': 'Address Line 1',
            'address_line_2': 'Address Line 2',
            'address_line_3': 'Address Line 3',
            'passkey': 'Passkey',
            'batch_encoding': 'Batch Encoding',
            'created_at': 'Created At',
            'updated_at': 'Updated At',
            'is_deleted': 'Is Deleted',
        }
