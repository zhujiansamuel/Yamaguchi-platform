"""
Purchasing Excel exporter.
Purchasing模型的Excel导出器。
"""
from .base import BaseExcelExporter


class PurchasingExporter(BaseExcelExporter):
    """
    Excel exporter for Purchasing model.
    """
    model_name = 'Purchasing'

    def get_queryset(self):
        """
        Get the queryset for Purchasing model.
        可以在这里自定义查询集，例如排序、过滤等。
        """
        return super().get_queryset()

    def get_fields(self):
        """
        Explicitly define export fields for Purchasing model.
        """
        return [
            'id',
            'uuid',
            'order_number',
            'official_account',
            'batch_encoding',
            'batch_level_1',
            'batch_level_2',
            'batch_level_3',
            'created_at',
            'confirmed_at',
            'shipped_at',
            'estimated_website_arrival_date',
            'estimated_website_arrival_date_2',
            'tracking_number',
            'estimated_delivery_date',
            'delivery_status',
            'latest_delivery_status',
            'delivery_status_query_time',
            'delivery_status_query_source',
            'official_query_url',
            'shipping_method',
            'last_info_updated_at',
            'account_used',
            'payment_method',
            'is_locked',
            'locked_at',
            'locked_by_worker',
            'updated_at',
            'is_deleted',
            'creation_source',
        ]

    def get_header_names(self):
        """
        Customize header names for Purchasing export.
        """
        return {
            'id': 'ID',
            'uuid': 'UUID',
            'order_number': 'Order Number',
            'official_account': 'Official Account',
            'batch_encoding': 'Batch Encoding',
            'batch_level_1': 'Batch Level 1',
            'batch_level_2': 'Batch Level 2',
            'batch_level_3': 'Batch Level 3',
            'confirmed_at': 'Confirmed At',
            'shipped_at': 'Shipped At',
            'estimated_website_arrival_date': 'Estimated Website Arrival Date',
            'estimated_website_arrival_date_2': 'Estimated Website Arrival Date 2',
            'tracking_number': 'Tracking Number',
            'estimated_delivery_date': 'Estimated Delivery Date',
            'delivery_status': 'Delivery Status',
            'latest_delivery_status': 'Latest Delivery Status',
            'delivery_status_query_time': 'Delivery Status Query Time',
            'delivery_status_query_source': 'Delivery Status Query Source',
            'official_query_url': 'Official Query URL',
            'shipping_method': 'Shipping Method',
            'account_used': 'Account Used',
            'payment_method': 'Payment Method',
            'is_locked': 'Is Locked',
            'locked_by_worker': 'Locked By Worker',
            'locked_at': 'Locked At',
            'last_info_updated_at': 'Last Info Updated At',
            'created_at': 'Created At',
            'updated_at': 'Updated At',
            'is_deleted': 'Is Deleted',
            'creation_source': 'Creation Source',
        }
