"""
URL configuration for data_acquisition app.
"""
from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    nextcloud_webhook,
    onlyoffice_callback,
    health_check,
    order_planning,
    WebScraperTrackingViewSet
)

app_name = 'data_acquisition'

router = DefaultRouter()
router.register(r'webscraper', WebScraperTrackingViewSet, basename='webscraper')

urlpatterns = [
    # Nextcloud webhook endpoint
    path('webhook/nextcloud/', nextcloud_webhook, name='nextcloud_webhook'),

    # OnlyOffice callback endpoint (dual-callback architecture)
    path('onlyoffice/callback/', onlyoffice_callback, name='onlyoffice_callback'),

    # Health check endpoint
    path('health/', health_check, name='health_check'),

    # Order planning endpoint
    path('order-planning/', order_planning, name='order_planning'),
] + router.urls
