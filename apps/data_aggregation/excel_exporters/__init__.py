"""
Excel exporters for data_aggregation models.
数据聚合模型的Excel导出器。
"""
from .base import BaseExcelExporter
from .iphone_exporter import iPhoneExporter
from .ipad_exporter import iPadExporter
from .inventory_exporter import InventoryExporter
from .purchasing_exporter import PurchasingExporter
from .official_account_exporter import OfficialAccountExporter
from .temporary_channel_exporter import TemporaryChannelExporter
from .legal_person_offline_exporter import LegalPersonOfflineExporter
from .ec_site_exporter import EcSiteExporter
from .gift_card_exporter import GiftCardExporter
from .debit_card_exporter import DebitCardExporter
from .debit_card_payment_exporter import DebitCardPaymentExporter
from .credit_card_exporter import CreditCardExporter
from .credit_card_payment_exporter import CreditCardPaymentExporter
from .gift_card_payment_exporter import GiftCardPaymentExporter
from .other_payment_exporter import OtherPaymentExporter
from .aggregation_source_exporter import AggregationSourceExporter
from .aggregated_data_exporter import AggregatedDataExporter
from .aggregation_task_exporter import AggregationTaskExporter
from .iphone_inventory_dashboard_exporter import iPhoneInventoryDashboardExporter

# Exporter registry mapping model names to their exporters
EXPORTER_REGISTRY = {
    'iPhone': iPhoneExporter,
    'iPad': iPadExporter,
    'Inventory': InventoryExporter,
    'Purchasing': PurchasingExporter,
    'OfficialAccount': OfficialAccountExporter,
    'TemporaryChannel': TemporaryChannelExporter,
    'LegalPersonOffline': LegalPersonOfflineExporter,
    'EcSite': EcSiteExporter,
    'GiftCard': GiftCardExporter,
    'DebitCard': DebitCardExporter,
    'DebitCardPayment': DebitCardPaymentExporter,
    'CreditCard': CreditCardExporter,
    'CreditCardPayment': CreditCardPaymentExporter,
    'GiftCardPayment': GiftCardPaymentExporter,
    'OtherPayment': OtherPaymentExporter,
    'AggregationSource': AggregationSourceExporter,
    'AggregatedData': AggregatedDataExporter,
    'AggregationTask': AggregationTaskExporter,
}

# Dashboard exporter registry (separate from model exporters)
DASHBOARD_EXPORTER_REGISTRY = {
    'iPhoneInventoryDashboard': iPhoneInventoryDashboardExporter,
}


def get_exporter(model_name):
    """
    Get the appropriate exporter for a given model name.

    Args:
        model_name (str): Name of the model

    Returns:
        BaseExcelExporter: An instance of the appropriate exporter

    Raises:
        ValueError: If no exporter is found for the model
    """
    exporter_class = EXPORTER_REGISTRY.get(model_name)
    if not exporter_class:
        raise ValueError(f"No exporter found for model '{model_name}'")
    return exporter_class()


def get_dashboard_exporter(dashboard_name):
    """
    Get the appropriate dashboard exporter for a given dashboard name.

    Args:
        dashboard_name (str): Name of the dashboard

    Returns:
        Dashboard exporter instance

    Raises:
        ValueError: If no exporter is found for the dashboard
    """
    exporter_class = DASHBOARD_EXPORTER_REGISTRY.get(dashboard_name)
    if not exporter_class:
        raise ValueError(f"No exporter found for dashboard '{dashboard_name}'")
    return exporter_class()


__all__ = [
    'BaseExcelExporter',
    'iPhoneExporter',
    'iPadExporter',
    'InventoryExporter',
    'PurchasingExporter',
    'OfficialAccountExporter',
    'TemporaryChannelExporter',
    'LegalPersonOfflineExporter',
    'EcSiteExporter',
    'GiftCardExporter',
    'DebitCardExporter',
    'DebitCardPaymentExporter',
    'CreditCardExporter',
    'CreditCardPaymentExporter',
    'GiftCardPaymentExporter',
    'OtherPaymentExporter',
    'AggregationSourceExporter',
    'AggregatedDataExporter',
    'AggregationTaskExporter',
    'iPhoneInventoryDashboardExporter',
    'EXPORTER_REGISTRY',
    'DASHBOARD_EXPORTER_REGISTRY',
    'get_exporter',
    'get_dashboard_exporter',
]
