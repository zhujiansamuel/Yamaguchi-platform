"""
URL configuration for data_aggregation app.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    iPhoneViewSet, iPadViewSet, InventoryViewSet,
    TemporaryChannelViewSet, PurchasingViewSet, OfficialAccountViewSet,
    LegalPersonOfflineViewSet, EcSiteViewSet, GiftCardViewSet, GiftCardPaymentViewSet,
    DebitCardViewSet, DebitCardPaymentViewSet,
    CreditCardViewSet, CreditCardPaymentViewSet, OtherPaymentViewSet,
    export_models_to_excel, batch_encoding_stats, purchasing_stats,
    create_legal_person_offline_with_inventory, export_iphone_inventory_dashboard,
    get_iphone_inventory_dashboard_data, batch_ingest_emails
)

app_name = 'data_aggregation'

router = DefaultRouter()
router.register(r'iphones', iPhoneViewSet, basename='iphone')
router.register(r'ipads', iPadViewSet, basename='ipad')
router.register(r'inventory', InventoryViewSet, basename='inventory')
router.register(r'temporary-channels', TemporaryChannelViewSet, basename='temporary-channel')
router.register(r'official-accounts', OfficialAccountViewSet, basename='official-account')
router.register(r'purchasing', PurchasingViewSet, basename='purchasing')
router.register(r'legal-person-offline', LegalPersonOfflineViewSet, basename='legal-person-offline')
router.register(r'ec-sites', EcSiteViewSet, basename='ec-site')
router.register(r'giftcards', GiftCardViewSet, basename='giftcard')
router.register(r'giftcard-payments', GiftCardPaymentViewSet, basename='giftcard-payment')
router.register(r'debitcards', DebitCardViewSet, basename='debitcard')
router.register(r'debitcard-payments', DebitCardPaymentViewSet, basename='debitcard-payment')
router.register(r'creditcards', CreditCardViewSet, basename='creditcard')
router.register(r'creditcard-payments', CreditCardPaymentViewSet, basename='creditcard-payment')
router.register(r'other-payments', OtherPaymentViewSet, basename='other-payment')

urlpatterns = [
    path('', include(router.urls)),
    path('export-to-excel/', export_models_to_excel, name='export-to-excel'),
    path('v1/historical-data/batch-stats/', batch_encoding_stats, name='batch-encoding-stats'),
    path('v1/historical-data/purchasing-stats/', purchasing_stats, name='purchasing-stats'),
    path('legal-person-offline/create-with-inventory/', create_legal_person_offline_with_inventory, name='create-legal-person-offline-with-inventory'),
    path('export-iphone-inventory-dashboard/', export_iphone_inventory_dashboard, name='export-iphone-inventory-dashboard'),
    path('iphone-inventory-dashboard-data/', get_iphone_inventory_dashboard_data, name='iphone-inventory-dashboard-data'),
    path('emails/ingest/', batch_ingest_emails, name='batch-ingest-emails'),
]
