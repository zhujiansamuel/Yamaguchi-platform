"""
Inventory Excel exporter.
Inventory模型的Excel导出器。
"""
from .base import BaseExcelExporter


class InventoryExporter(BaseExcelExporter):
    """
    Excel exporter for Inventory model.
    """
    model_name = 'Inventory'

    def get_queryset(self):
        """
        Get the queryset for Inventory model.
        可以在这里自定义查询集，例如排序、过滤等。
        """
        return super().get_queryset()

    def get_fields(self):
        """
        Explicitly define export fields for Inventory model.
        """
        return [
            'id',
            'uuid',
            'flag',
            'iphone',
            'ipad',
            'imei',
            'batch_level_1',
            'batch_level_2',
            'batch_level_3',
            'source1',
            'source2',
            'source3',
            'source4',
            'transaction_confirmed_at',
            'scheduled_arrival_at',
            'checked_arrival_at_1',
            'checked_arrival_at_2',
            'actual_arrival_at',
            'status',
            'created_at',
            'updated_at',
            'is_deleted',
        ]

    def get_header_names(self):
        """
        Customize header names for Inventory export.
        可以在这里自定义表头名称。
        """
        # 默认使用字段名，可以根据需要自定义
        return {
            'id': 'ID',
            'uuid': 'UUID',
            'flag': 'Flag',
            'iphone': 'iPhone Product',
            'ipad': 'iPad Product',
            'imei': 'IMEI',
            'batch_level_1': 'Batch Level 1',
            'batch_level_2': 'Batch Level 2',
            'batch_level_3': 'Batch Level 3',
            'source1': 'Source 1 (EC Site)',
            'source2': 'Source 2 (Purchasing)',
            'source3': 'Source 3 (Legal Person Offline)',
            'source4': 'Source 4 (Temporary Channel)',
            'transaction_confirmed_at': 'Transaction Confirmed At',
            'scheduled_arrival_at': 'Scheduled Arrival At',
            'checked_arrival_at_1': 'Checked Arrival Time 1',
            'checked_arrival_at_2': 'Checked Arrival Time 2',
            'actual_arrival_at': 'Actual Arrival At',
            'status': 'Status',
            'created_at': 'Created At',
            'updated_at': 'Updated At',
            'is_deleted': 'Is Deleted',
        }
