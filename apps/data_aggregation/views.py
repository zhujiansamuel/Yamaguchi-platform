"""
Views for data_aggregation app.
"""
from rest_framework import viewsets, filters, status
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
from drf_spectacular.types import OpenApiTypes
from .models import (
    iPhone, iPad, Inventory, Purchasing, OfficialAccount,
    TemporaryChannel, LegalPersonOffline, EcSite, GiftCard, GiftCardPayment,
    DebitCard, DebitCardPayment, CreditCard, CreditCardPayment,
    OtherPayment, HistoricalData, MailAccount, MailThread, MailLabel,
    MailMessage, MailMessageBody, MailMessageLabel, MailAttachment
)
from .serializers import (
    iPhoneSerializer, iPadSerializer, InventorySerializer, PurchasingSerializer, OfficialAccountSerializer,
    TemporaryChannelSerializer, LegalPersonOfflineSerializer, EcSiteSerializer, GiftCardSerializer,
    DebitCardSerializer, DebitCardPaymentSerializer, CreditCardSerializer, CreditCardPaymentSerializer,
    GiftCardPaymentSerializer, OtherPaymentSerializer,
    CreateLegalPersonOfflineWithInventorySerializer, CreateLegalPersonOfflineWithInventoryResponseSerializer,
    ExportIPhoneInventoryDashboardResponseSerializer,
    GetIPhoneInventoryDashboardDataResponseSerializer,
    EmailBatchIngestRequestSerializer, EmailBatchIngestResponseSerializer
)
from .authentication import SimpleTokenAuthentication, QueryParamTokenAuthentication
from .utils import get_all_model_names, export_model_to_excel, upload_excel_files
from datetime import datetime


class AuthenticatedModelViewSet(viewsets.ModelViewSet):
    """
    Base ViewSet with SimpleTokenAuthentication.
    所有需要认证的 ViewSet 的基类。
    
    Authentication:
    - Uses BATCH_STATS_API_TOKEN via Authorization header
    - Format: Authorization: Bearer <BATCH_STATS_API_TOKEN>
    """
    authentication_classes = [SimpleTokenAuthentication]


class iPhoneViewSet(AuthenticatedModelViewSet):
    """
    API endpoint for iPhone management.

    Supports:
    - List all iPhones (GET /api/aggregation/iphones/)
    - Create new iPhone (POST /api/aggregation/iphones/)
    - Retrieve specific iPhone (GET /api/aggregation/iphones/{id}/)
    - Update iPhone (PUT/PATCH /api/aggregation/iphones/{id}/)
    - Delete iPhone (DELETE /api/aggregation/iphones/{id}/)

    Filtering:
    - Filter by model_name: ?model_name=iPhone 17
    - Filter by capacity: ?capacity_gb=256
    - Filter by color: ?color=ブラック

    Search:
    - Search in part_number, model_name, color: ?search=iPhone

    Ordering:
    - Order by any field: ?ordering=-release_date
    """
    queryset = iPhone.objects.all()
    serializer_class = iPhoneSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]

    # Fields that can be filtered
    filterset_fields = ['model_name', 'capacity_gb', 'color', 'release_date']

    # Fields that can be searched
    search_fields = ['part_number', 'model_name', 'color', 'jan']

    # Fields that can be used for ordering
    ordering_fields = ['release_date', 'model_name', 'capacity_gb', 'created_at']
    ordering = ['-release_date']  # Default ordering


class iPadViewSet(AuthenticatedModelViewSet):
    """
    API endpoint for iPad management.

    Supports:
    - List all iPads (GET /api/aggregation/ipads/)
    - Create new iPad (POST /api/aggregation/ipads/)
    - Retrieve specific iPad (GET /api/aggregation/ipads/{id}/)
    - Update iPad (PUT/PATCH /api/aggregation/ipads/{id}/)
    - Delete iPad (DELETE /api/aggregation/ipads/{id}/)

    Filtering:
    - Filter by model_name: ?model_name=iPad Pro 12.9
    - Filter by capacity: ?capacity_gb=256
    - Filter by color: ?color=スペースグレイ

    Search:
    - Search in part_number, model_name, color: ?search=iPad

    Ordering:
    - Order by any field: ?ordering=-release_date
    """
    queryset = iPad.objects.all()
    serializer_class = iPadSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]

    # Fields that can be filtered
    filterset_fields = ['model_name', 'capacity_gb', 'color', 'release_date']

    # Fields that can be searched
    search_fields = ['part_number', 'model_name', 'color', 'jan']

    # Fields that can be used for ordering
    ordering_fields = ['release_date', 'model_name', 'capacity_gb', 'created_at']
    ordering = ['-release_date']  # Default ordering


class TemporaryChannelViewSet(AuthenticatedModelViewSet):
    """
    API endpoint for TemporaryChannel management.

    Supports:
    - List all temporary channels (GET /api/aggregation/temporary-channels/)
    - Create new temporary channel (POST /api/aggregation/temporary-channels/)
    - Retrieve specific temporary channel (GET /api/aggregation/temporary-channels/{id}/)
    - Update temporary channel (PUT/PATCH /api/aggregation/temporary-channels/{id}/)
    - Delete temporary channel (DELETE /api/aggregation/temporary-channels/{id}/)

    Filtering:
    - Filter by expected_time: ?expected_time=2025-01-01

    Search:
    - Search in record: ?search=keyword

    Ordering:
    - Order by any field: ?ordering=-created_time
    """
    queryset = TemporaryChannel.objects.all()
    serializer_class = TemporaryChannelSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]

    # Fields that can be filtered
    filterset_fields = ['expected_time']

    # Fields that can be searched
    search_fields = ['record']

    # Fields that can be used for ordering
    ordering_fields = ['created_time', 'expected_time', 'last_updated']
    ordering = ['-created_time']  # Default ordering


class InventoryViewSet(AuthenticatedModelViewSet):
    """
    API endpoint for Inventory management.

    Supports:
    - List all inventory items (GET /api/aggregation/inventory/)
    - Create new inventory (POST /api/aggregation/inventory/)
    - Retrieve specific inventory (GET /api/aggregation/inventory/{id}/)
    - Update inventory (PUT/PATCH /api/aggregation/inventory/{id}/)
    - Delete inventory (DELETE /api/aggregation/inventory/{id}/)

    Filtering:
    - Filter by status: ?status=in_transit
    - Filter by product type: ?iphone={id} or ?ipad={id}

    Search:
    - Search in uuid, flag: ?search=xyz

    Ordering:
    - Order by any field: ?ordering=-created_at
    """
    queryset = Inventory.objects.all()
    serializer_class = InventorySerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]

    # Fields that can be filtered
    filterset_fields = [
        'status',
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
        'is_deleted',
    ]

    # Fields that can be searched
    search_fields = ['uuid', 'flag', 'imei']

    # Fields that can be used for ordering
    ordering_fields = [
        'created_at',
        'updated_at',
        'transaction_confirmed_at',
        'scheduled_arrival_at',
        'checked_arrival_at_1',
        'checked_arrival_at_2',
        'actual_arrival_at',
        'status',
    ]
    ordering = ['-created_at']  # Default ordering


class OfficialAccountViewSet(AuthenticatedModelViewSet):
    """
    API endpoint for Official Account management.
    官方账号管理的API端点。

    Supports:
    - List all official accounts (GET /api/aggregation/official-accounts/)
    - Create new official account (POST /api/aggregation/official-accounts/)
    - Retrieve specific account (GET /api/aggregation/official-accounts/{id}/)
    - Update account (PUT/PATCH /api/aggregation/official-accounts/{id}/)
    - Delete account (DELETE /api/aggregation/official-accounts/{id}/)

    Filtering:
    - Filter by account_id: ?account_id=ACC123
    - Filter by email: ?email=user@example.com
    - Filter by name: ?name=张三

    Search:
    - Search in uuid, account_id, email, name: ?search=user123

    Ordering:
    - Order by any field: ?ordering=-created_at
    """
    queryset = OfficialAccount.objects.all()
    serializer_class = OfficialAccountSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]

    # Fields that can be filtered
    filterset_fields = [
        'account_id',
        'email',
        'name',
    ]

    # Fields that can be searched
    search_fields = [
        'uuid',
        'account_id',
        'email',
        'name',
        'postal_code',
    ]

    # Fields that can be used for ordering
    ordering_fields = [
        'created_at',
        'updated_at',
        'email',
        'name',
    ]
    ordering = ['-created_at']  # Default ordering


class PurchasingViewSet(AuthenticatedModelViewSet):
    """
    API endpoint for Purchasing order management.
    采购订单管理的API端点。

    Supports:
    - List all purchasing orders (GET /api/aggregation/purchasing/)
    - Create new purchasing order (POST /api/aggregation/purchasing/)
    - Retrieve specific order (GET /api/aggregation/purchasing/{id}/)
    - Update order (PUT/PATCH /api/aggregation/purchasing/{id}/)
    - Delete order (DELETE /api/aggregation/purchasing/{id}/)

    Filtering:
    - Filter by delivery_status: ?delivery_status=shipped
    - Filter by payment_method: ?payment_method=credit_card
    - Filter by order_number: ?order_number=ORD123
    - Filter by official_account: ?official_account={id}

    Search:
    - Search in uuid, order_number, tracking_number, account_used: ?search=ORD123

    Ordering:
    - Order by any field: ?ordering=-created_at

    Additional Fields:
    - inventory_count: Number of inventory items associated with this purchasing order
    - inventory_items: Detailed list of inventory items (id, uuid, flag, status, product_type, created_at)
    """
    queryset = Purchasing.objects.all()
    serializer_class = PurchasingSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]

    # Fields that can be filtered
    filterset_fields = [
        'delivery_status',
        'payment_method',
        'order_number',
        'official_account',
        'tracking_number',
        'batch_encoding',
        'batch_level_1',
        'batch_level_2',
        'batch_level_3',
        'creation_source',
        'is_locked',
        'is_deleted',
    ]

    # Fields that can be searched
    search_fields = [
        'uuid',
        'order_number',
        'tracking_number',
        'account_used',
        'batch_encoding',
    ]

    # Fields that can be used for ordering
    ordering_fields = [
        'created_at',
        'updated_at',
        'confirmed_at',
        'shipped_at',
        'estimated_delivery_date',
        'delivery_status',
        'delivery_status_query_time',
        'last_info_updated_at',
    ]
    ordering = ['-created_at']  # Default ordering


class LegalPersonOfflineViewSet(AuthenticatedModelViewSet):
    """
    API endpoint for Legal Person Offline management.

    Supports:
    - List all legal person offline records (GET /api/aggregation/legal-person-offline/)
    - Create new record (POST /api/aggregation/legal-person-offline/)
    - Retrieve specific record (GET /api/aggregation/legal-person-offline/{id}/)
    - Update record (PUT/PATCH /api/aggregation/legal-person-offline/{id}/)
    - Delete record (DELETE /api/aggregation/legal-person-offline/{id}/)

    Filtering:
    - Filter by username: ?username=张三
    - Filter by visit time: ?visit_time=2025-01-01

    Search:
    - Search in uuid, username: ?search=user123

    Ordering:
    - Order by any field: ?ordering=-order_created_at
    """
    queryset = LegalPersonOffline.objects.all()
    serializer_class = LegalPersonOfflineSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]

    # Fields that can be filtered
    filterset_fields = ['username', 'visit_time', 'appointment_time']

    # Fields that can be searched
    search_fields = ['uuid', 'username']

    # Fields that can be used for ordering
    ordering_fields = ['order_created_at', 'updated_at', 'visit_time', 'appointment_time']
    ordering = ['-order_created_at']  # Default ordering


class EcSiteViewSet(AuthenticatedModelViewSet):
    """
    API endpoint for EcSite management.

    Supports:
    - List all EC site orders (GET /api/aggregation/ec-sites/)
    - Create new EC site order (POST /api/aggregation/ec-sites/)
    - Retrieve specific EC site order (GET /api/aggregation/ec-sites/{id}/)
    - Update EC site order (PUT/PATCH /api/aggregation/ec-sites/{id}/)
    - Delete EC site order (DELETE /api/aggregation/ec-sites/{id}/)

    Filtering:
    - Filter by username: ?username=user123
    - Filter by method: ?method=online
    - Filter by order_created_at: ?order_created_at=2025-01-01

    Search:
    - Search in reservation_number, username: ?search=RES123

    Ordering:
    - Order by any field: ?ordering=-order_created_at
    """
    queryset = EcSite.objects.all()
    serializer_class = EcSiteSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]

    # Fields that can be filtered
    filterset_fields = ['username', 'method', 'order_created_at', 'visit_time']

    # Fields that can be searched
    search_fields = ['reservation_number', 'username', 'order_detail_url']

    # Fields that can be used for ordering
    ordering_fields = ['order_created_at', 'visit_time', 'reservation_time', 'created_at']
    ordering = ['-order_created_at']  # Default ordering


class GiftCardViewSet(AuthenticatedModelViewSet):
    """
    API endpoint for Gift Card management.
    礼品卡管理的API端点。

    Supports:
    - List all gift cards (GET /api/aggregation/giftcards/)
    - Create new gift card (POST /api/aggregation/giftcards/)
    - Retrieve specific gift card (GET /api/aggregation/giftcards/{id}/)
    - Update gift card (PUT/PATCH /api/aggregation/giftcards/{id}/)
    - Delete gift card (DELETE /api/aggregation/giftcards/{id}/)

    Filtering:
    - Filter by card_number: ?card_number=CARD123
    - Filter by balance: ?balance=1000

    Search:
    - Search in card_number: ?search=CARD123

    Ordering:
    - Order by any field: ?ordering=-created_at
    """
    queryset = GiftCard.objects.all()
    serializer_class = GiftCardSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]

    # Fields that can be filtered
    filterset_fields = ['card_number', 'balance']

    # Fields that can be searched
    search_fields = ['card_number']

    # Fields that can be used for ordering
    ordering_fields = ['created_at', 'updated_at', 'balance']
    ordering = ['-created_at']  # Default ordering


class DebitCardPaymentViewSet(AuthenticatedModelViewSet):
    """
    API endpoint for Debit Card Payment management.
    借记卡支付管理的API端点。

    Supports:
    - List all debit card payments (GET /api/aggregation/debitcard-payments/)
    - Create new debit card payment (POST /api/aggregation/debitcard-payments/)
    - Retrieve specific debit card payment (GET /api/aggregation/debitcard-payments/{id}/)
    - Update debit card payment (PUT/PATCH /api/aggregation/debitcard-payments/{id}/)
    - Delete debit card payment (DELETE /api/aggregation/debitcard-payments/{id}/)

    Filtering:
    - Filter by payment_status: ?payment_status=completed
    - Filter by debit_card: ?debit_card=1
    - Filter by purchasing: ?purchasing=1

    Search:
    - Search in payment_status: ?search=completed

    Ordering:
    - Order by any field: ?ordering=-payment_time
    """
    queryset = DebitCardPayment.objects.all()
    serializer_class = DebitCardPaymentSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]

    # Fields that can be filtered
    filterset_fields = ['payment_status', 'debit_card', 'purchasing']

    # Fields that can be searched
    search_fields = ['payment_status']

    # Fields that can be used for ordering
    ordering_fields = ['payment_time', 'payment_amount', 'created_at', 'updated_at']
    ordering = ['-payment_time']  # Default ordering


class DebitCardViewSet(AuthenticatedModelViewSet):
    """
    API endpoint for Debit Card management.
    借记卡管理的API端点。

    Supports:
    - List all debit cards (GET /api/aggregation/debitcards/)
    - Create new debit card (POST /api/aggregation/debitcards/)
    - Retrieve specific debit card (GET /api/aggregation/debitcards/{id}/)
    - Update debit card (PUT/PATCH /api/aggregation/debitcards/{id}/)
    - Delete debit card (DELETE /api/aggregation/debitcards/{id}/)

    Filtering:
    - Filter by card_number: ?card_number=1234567890123456
    - Filter by balance: ?balance=1000.00
    - Filter by expiry_year: ?expiry_year=2025
    - Filter by expiry_month: ?expiry_month=12

    Search:
    - Search in card_number: ?search=1234

    Ordering:
    - Order by any field: ?ordering=-created_at
    """
    queryset = DebitCard.objects.all()
    serializer_class = DebitCardSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]

    # Fields that can be filtered
    filterset_fields = ['card_number', 'balance', 'expiry_year', 'expiry_month']

    # Fields that can be searched
    search_fields = ['card_number']

    # Fields that can be used for ordering
    ordering_fields = ['created_at', 'updated_at', 'balance', 'last_balance_update']
    ordering = ['-created_at']  # Default ordering


class CreditCardPaymentViewSet(AuthenticatedModelViewSet):
    """
    API endpoint for Credit Card Payment management.
    信用卡支付管理的API端点。

    Supports:
    - List all credit card payments (GET /api/aggregation/creditcard-payments/)
    - Create new credit card payment (POST /api/aggregation/creditcard-payments/)
    - Retrieve specific credit card payment (GET /api/aggregation/creditcard-payments/{id}/)
    - Update credit card payment (PUT/PATCH /api/aggregation/creditcard-payments/{id}/)
    - Delete credit card payment (DELETE /api/aggregation/creditcard-payments/{id}/)

    Filtering:
    - Filter by payment_status: ?payment_status=completed
    - Filter by credit_card: ?credit_card=1
    - Filter by purchasing: ?purchasing=1

    Search:
    - Search in payment_status: ?search=completed

    Ordering:
    - Order by any field: ?ordering=-payment_time
    """
    queryset = CreditCardPayment.objects.all()
    serializer_class = CreditCardPaymentSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]

    # Fields that can be filtered
    filterset_fields = ['payment_status', 'credit_card', 'purchasing']

    # Fields that can be searched
    search_fields = ['payment_status']

    # Fields that can be used for ordering
    ordering_fields = ['payment_time', 'payment_amount', 'created_at', 'updated_at']
    ordering = ['-payment_time']  # Default ordering


class CreditCardViewSet(AuthenticatedModelViewSet):
    """
    API endpoint for Credit Card management.
    信用卡管理的API端点。

    Supports:
    - List all credit cards (GET /api/aggregation/creditcards/)
    - Create new credit card (POST /api/aggregation/creditcards/)
    - Retrieve specific credit card (GET /api/aggregation/creditcards/{id}/)
    - Update credit card (PUT/PATCH /api/aggregation/creditcards/{id}/)
    - Delete credit card (DELETE /api/aggregation/creditcards/{id}/)

    Filtering:
    - Filter by card_number: ?card_number=1234567890123456
    - Filter by credit_limit: ?credit_limit=10000.00
    - Filter by expiry_year: ?expiry_year=2025
    - Filter by expiry_month: ?expiry_month=12

    Search:
    - Search in card_number: ?search=1234

    Ordering:
    - Order by any field: ?ordering=-created_at
    """
    queryset = CreditCard.objects.all()
    serializer_class = CreditCardSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]

    # Fields that can be filtered
    filterset_fields = ['card_number', 'credit_limit', 'expiry_year', 'expiry_month']

    # Fields that can be searched
    search_fields = ['card_number']

    # Fields that can be used for ordering
    ordering_fields = ['created_at', 'updated_at', 'credit_limit', 'last_balance_update']
    ordering = ['-created_at']  # Default ordering


class GiftCardPaymentViewSet(AuthenticatedModelViewSet):
    """
    API endpoint for Gift Card Payment management.
    礼品卡支付管理的API端点。

    Supports:
    - List all gift card payments (GET /api/aggregation/giftcard-payments/)
    - Create new gift card payment (POST /api/aggregation/giftcard-payments/)
    - Retrieve specific gift card payment (GET /api/aggregation/giftcard-payments/{id}/)
    - Update gift card payment (PUT/PATCH /api/aggregation/giftcard-payments/{id}/)
    - Delete gift card payment (DELETE /api/aggregation/giftcard-payments/{id}/)

    Filtering:
    - Filter by payment_status: ?payment_status=completed
    - Filter by gift_card: ?gift_card=1
    - Filter by purchasing: ?purchasing=1

    Search:
    - Search in payment_status: ?search=completed

    Ordering:
    - Order by any field: ?ordering=-payment_time
    """
    queryset = GiftCardPayment.objects.all()
    serializer_class = GiftCardPaymentSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]

    # Fields that can be filtered
    filterset_fields = ['payment_status', 'gift_card', 'purchasing']

    # Fields that can be searched
    search_fields = ['payment_status']

    # Fields that can be used for ordering
    ordering_fields = ['payment_time', 'payment_amount', 'created_at', 'updated_at']
    ordering = ['-payment_time']  # Default ordering


class OtherPaymentViewSet(AuthenticatedModelViewSet):
    """
    API endpoint for Other Payment management.
    其他支付方式管理的API端点。

    Supports:
    - List all other payments (GET /api/aggregation/other-payments/)
    - Create new other payment (POST /api/aggregation/other-payments/)
    - Retrieve specific other payment (GET /api/aggregation/other-payments/{id}/)
    - Update other payment (PUT/PATCH /api/aggregation/other-payments/{id}/)
    - Delete other payment (DELETE /api/aggregation/other-payments/{id}/)

    Filtering:
    - Filter by payment_status: ?payment_status=completed
    - Filter by purchasing: ?purchasing=1

    Search:
    - Search in payment_info, payment_status: ?search=completed

    Ordering:
    - Order by any field: ?ordering=-payment_time
    """
    queryset = OtherPayment.objects.all()
    serializer_class = OtherPaymentSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]

    # Fields that can be filtered
    filterset_fields = ['payment_status', 'purchasing']

    # Fields that can be searched
    search_fields = ['payment_info', 'payment_status']

    # Fields that can be used for ordering
    ordering_fields = ['payment_time', 'payment_amount', 'created_at', 'updated_at']
    ordering = ['-payment_time']  # Default ordering


@extend_schema(
    summary="Export models to Excel",
    description="""
    Export data_aggregation models to Excel and upload to Nextcloud.
    导出data_aggregation模型数据到Excel并上传到Nextcloud。

    This endpoint now supports dual-file export:
    1. Timestamped tracking: {ModelName}_test_{timestamp}.xlsx in No_aggregated_raw_data/ (always)
    2. Latest version: {ModelName}_test.xlsx in data_platform/ (if enabled, overwrites)

    GET request: List all available model names
    POST request: Export specified models to Excel
    """,
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'models': {
                    'type': 'array',
                    'items': {'type': 'string'},
                    'description': 'List of model names to export. Optional, if not provided, exports all models.',
                    'example': ['iPhone', 'iPad', 'Inventory']
                }
            }
        }
    },
    responses={
        200: {
            'type': 'object',
            'properties': {
                'status': {'type': 'string', 'example': 'success'},
                'message': {'type': 'string'},
                'available_models': {
                    'type': 'array',
                    'items': {'type': 'string'},
                    'description': 'Only for GET requests'
                },
                'results': {
                    'type': 'array',
                    'items': {
                        'type': 'object',
                        'properties': {
                            'model': {'type': 'string'},
                            'non_historical_file': {'type': 'string'},
                            'historical_file': {'type': 'string'},
                            'upload_status': {'type': 'string'},
                            'non_historical_upload': {'type': 'object'},
                            'historical_upload': {'type': 'object'}
                        }
                    },
                    'description': 'Only for POST requests'
                },
                'errors': {
                    'type': 'array',
                    'items': {
                        'type': 'object',
                        'properties': {
                            'model': {'type': 'string'},
                            'error': {'type': 'string'}
                        }
                    }
                }
            }
        },
        400: {
            'type': 'object',
            'properties': {
                'status': {'type': 'string', 'example': 'error'},
                'message': {'type': 'string'}
            }
        }
    },
    examples=[
        OpenApiExample(
            'Export specific models',
            value={'models': ['iPhone', 'iPad', 'Inventory']},
            request_only=True,
        ),
    ],
)
@api_view(['GET', 'POST'])
@authentication_classes([SimpleTokenAuthentication])
def export_models_to_excel(request):
    """
    Export data_aggregation models to Excel and upload to Nextcloud.
    导出data_aggregation模型数据到Excel并上传到Nextcloud。

    This endpoint now supports dual-file export:
    1. Timestamped tracking: {ModelName}_test_{timestamp}.xlsx in No_aggregated_raw_data/ (always)
    2. Latest version: {ModelName}_test.xlsx in data_platform/ (if enabled, overwrites)

    GET request: List all available model names
    POST request: Export specified models to Excel

    Request body for POST:
    {
        "models": ["iPhone", "iPad", "Inventory"]  // Optional, if not provided, exports all models
    }

    Response:
    {
        "status": "success",
        "message": "...",
        "results": [
            {
                "model": "iPhone",
                "non_historical_file": "iPhone_test.xlsx",
                "historical_file": "iPhone_test_20250101_120000.xlsx",
                "upload_status": "success",
                "non_historical_upload": {...},
                "historical_upload": {...}
            }
        ]
    }
    """
    if request.method == 'GET':
        # Return list of available models
        available_models = get_all_model_names()
        return Response({
            'status': 'success',
            'available_models': available_models,
            'message': f'Found {len(available_models)} models available for export'
        })

    elif request.method == 'POST':
        # Get models to export from request data
        models_to_export = request.data.get('models', None)

        # If no models specified, export all models
        if not models_to_export:
            models_to_export = get_all_model_names()

        if not isinstance(models_to_export, list):
            return Response(
                {
                    'status': 'error',
                    'message': 'models must be a list of model names'
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        results = []
        errors = []

        # Export each model
        for model_name in models_to_export:
            try:
                # Generate timestamp for historical file
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

                # Export model to Excel
                excel_file = export_model_to_excel(model_name)

                # Upload to both directories
                upload_results = upload_excel_files(
                    excel_file.getvalue(),
                    model_name,
                    timestamp=timestamp
                )

                # Prepare result entry
                result_entry = {
                    'model': model_name,
                    'timestamped_file': f"{model_name}_test_{timestamp}.xlsx",
                    'upload_status': upload_results['overall_status'],
                    'timestamped_upload': upload_results['non_historical'],
                    'latest_upload': upload_results['historical']
                }

                # Add latest filename if it was uploaded
                if upload_results['historical']['status'] != 'skipped':
                    result_entry['latest_file'] = f"{model_name}_test.xlsx"

                results.append(result_entry)

            except ValueError as e:
                errors.append({
                    'model': model_name,
                    'error': str(e)
                })
            except Exception as e:
                errors.append({
                    'model': model_name,
                    'error': f'Unexpected error: {str(e)}'
                })

        # Prepare response
        response_data = {
            'status': 'success' if not errors else 'partial_success' if results else 'error',
            'message': f'Exported {len(results)} model(s) successfully',
            'results': results
        }

        if errors:
            response_data['errors'] = errors

        return Response(response_data, status=status.HTTP_200_OK)


@extend_schema(
    summary="Get batch encoding statistics",
    description="""
    Get statistics for batch_encoding field across CreditCard, DebitCard, GiftCard, and OfficialAccount models.
    获取 CreditCard、DebitCard、GiftCard 和 OfficialAccount 模型中 batch_encoding 字段的统计信息。

    This endpoint:
    1. Counts records for each unique batch_encoding value in each model
    2. Records the statistics to HistoricalData model with slug format: batch:{batch_encoding_value}
    3. Returns the statistics data

    Authentication: Query parameter token required (?token=xxx)
    """,
    parameters=[
        OpenApiParameter(
            name='token',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            required=True,
            description='API authentication token'
        )
    ],
    responses={
        200: {
            'type': 'object',
            'properties': {
                'status': {'type': 'string', 'example': 'success'},
                'data': {
                    'type': 'object',
                    'description': 'Statistics grouped by model name',
                    'example': {
                        'CreditCard': {'batch_001': 5, 'batch_002': 3},
                        'DebitCard': {'batch_001': 2},
                        'GiftCard': {},
                        'OfficialAccount': {'batch_001': 10}
                    }
                },
                'historical_records_created': {'type': 'integer', 'example': 10}
            }
        },
        401: {
            'type': 'object',
            'properties': {
                'detail': {'type': 'string', 'example': 'Invalid token'}
            }
        }
    }
)
@api_view(['GET'])
@authentication_classes([QueryParamTokenAuthentication])
def batch_encoding_stats(request):
    """
    Get batch encoding statistics and record to HistoricalData.
    获取 batch_encoding 统计信息并记录到 HistoricalData。

    Counts records for each unique batch_encoding value in:
    - CreditCard
    - DebitCard
    - GiftCard
    - OfficialAccount

    Records are saved to HistoricalData with:
    - model: Model name (e.g., 'CreditCard')
    - slug: 'batch:{batch_encoding_value}'
    - value: Count of records with that batch_encoding
    """
    from django.db.models import Count

    # Models to analyze
    models_to_check = [
        ('CreditCard', CreditCard),
        ('DebitCard', DebitCard),
        ('GiftCard', GiftCard),
        ('OfficialAccount', OfficialAccount),
    ]

    result_data = {}
    historical_records_created = 0

    for model_name, model_class in models_to_check:
        # Get batch_encoding counts
        batch_counts = (
            model_class.objects
            .exclude(batch_encoding='')
            .exclude(batch_encoding__isnull=True)
            .values('batch_encoding')
            .annotate(count=Count('id'))
            .order_by('batch_encoding')
        )

        model_stats = {}
        for item in batch_counts:
            batch_value = item['batch_encoding']
            count = item['count']
            model_stats[batch_value] = count

            # Create HistoricalData record
            HistoricalData.objects.create(
                model=model_name,
                slug=f"batch:{batch_value}",
                value=count
            )
            historical_records_created += 1

        result_data[model_name] = model_stats

    return Response({
        'status': 'success',
        'data': result_data,
        'historical_records_created': historical_records_created
    }, status=status.HTTP_200_OK)


@extend_schema(
    summary="Get Purchasing stage statistics",
    description="""
    Get statistics for Purchasing model records at different processing stages.
    获取 Purchasing 模型中不同处理阶段的记录数统计。

    Stages:
    1. confirmed_at_empty: confirmed_at is empty, and shipped_at, estimated_website_arrival_date, tracking_number, estimated_delivery_date are all empty
    2. shipped_at_empty: shipped_at is empty, and estimated_website_arrival_date, tracking_number, estimated_delivery_date are all empty, but confirmed_at is not empty
    3. estimated_website_arrival_date_empty: estimated_website_arrival_date is empty, and tracking_number, estimated_delivery_date are all empty, but shipped_at, confirmed_at are not empty
    4. tracking_number_empty: tracking_number is empty, and estimated_delivery_date is empty, but shipped_at, confirmed_at, estimated_website_arrival_date are not empty
    5. estimated_delivery_date_empty: estimated_delivery_date is empty, but shipped_at, confirmed_at, estimated_website_arrival_date, tracking_number are not empty
       (Note: Former Worker 5 has been replaced by JapanPostTracking10TrackingNumberWorker and YamatoTracking10TrackingNumberWorker)
    6. other: Records that don't match any of the above conditions

    Authentication: Query parameter token required (?token=xxx)
    """,
    parameters=[
        OpenApiParameter(
            name='token',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            required=True,
            description='API authentication token'
        )
    ],
    responses={
        200: {
            'type': 'object',
            'properties': {
                'status': {'type': 'string', 'example': 'success'},
                'data': {
                    'type': 'object',
                    'example': {
                        'confirmed_at_empty': 10,
                        'shipped_at_empty': 5,
                        'estimated_website_arrival_date_empty': 3,
                        'tracking_number_empty': 2,
                        'estimated_delivery_date_empty': 1,
                        'other': 8
                    }
                },
                'total': {'type': 'integer', 'example': 29},
                'historical_records_created': {'type': 'integer', 'example': 6}
            }
        },
        401: {
            'type': 'object',
            'properties': {
                'detail': {'type': 'string', 'example': 'Invalid token'}
            }
        }
    }
)
@api_view(['GET'])
@authentication_classes([QueryParamTokenAuthentication])
def purchasing_stats(request):
    """
    Get Purchasing stage statistics and record to HistoricalData.
    获取 Purchasing 阶段统计信息并记录到 HistoricalData。

    Records are saved to HistoricalData with:
    - model: 'Purchasing'
    - slug: 'stage:{stage_name}'
    - value: Count of records at that stage
    """
    from django.db.models import Q

    # Helper function to check if tracking_number is empty (NULL or '')
    def tracking_number_empty_q():
        return Q(tracking_number__isnull=True) | Q(tracking_number='')

    def tracking_number_not_empty_q():
        return Q(tracking_number__isnull=False) & ~Q(tracking_number='')

    # Stage 1: confirmed_at_empty
    # confirmed_at is empty, and shipped_at, estimated_website_arrival_date, tracking_number, estimated_delivery_date are all empty
    stage1_count = Purchasing.objects.filter(
        confirmed_at__isnull=True,
        shipped_at__isnull=True,
        estimated_website_arrival_date__isnull=True,
        estimated_delivery_date__isnull=True
    ).filter(tracking_number_empty_q()).count()

    # Stage 2: shipped_at_empty
    # shipped_at is empty, and estimated_website_arrival_date, tracking_number, estimated_delivery_date are all empty, but confirmed_at is not empty
    stage2_count = Purchasing.objects.filter(
        confirmed_at__isnull=False,
        shipped_at__isnull=True,
        estimated_website_arrival_date__isnull=True,
        estimated_delivery_date__isnull=True
    ).filter(tracking_number_empty_q()).count()

    # Stage 3: estimated_website_arrival_date_empty
    # estimated_website_arrival_date is empty, and tracking_number, estimated_delivery_date are all empty, but shipped_at, confirmed_at are not empty
    stage3_count = Purchasing.objects.filter(
        confirmed_at__isnull=False,
        shipped_at__isnull=False,
        estimated_website_arrival_date__isnull=True,
        estimated_delivery_date__isnull=True
    ).filter(tracking_number_empty_q()).count()

    # Stage 4: tracking_number_empty
    # tracking_number is empty, and estimated_delivery_date is empty, but shipped_at, confirmed_at, estimated_website_arrival_date are not empty
    stage4_count = Purchasing.objects.filter(
        confirmed_at__isnull=False,
        shipped_at__isnull=False,
        estimated_website_arrival_date__isnull=False,
        estimated_delivery_date__isnull=True
    ).filter(tracking_number_empty_q()).count()

    # Stage 5: estimated_delivery_date_empty
    # estimated_delivery_date is empty, but shipped_at, confirmed_at, estimated_website_arrival_date, tracking_number are not empty
    stage5_count = Purchasing.objects.filter(
        confirmed_at__isnull=False,
        shipped_at__isnull=False,
        estimated_website_arrival_date__isnull=False,
        estimated_delivery_date__isnull=True
    ).filter(tracking_number_not_empty_q()).count()

    # Stage 6: other (doesn't match any of the above)
    total_count = Purchasing.objects.count()
    stage6_count = total_count - (stage1_count + stage2_count + stage3_count + stage4_count + stage5_count)

    # Prepare result data
    result_data = {
        'confirmed_at_empty': stage1_count,
        'shipped_at_empty': stage2_count,
        'estimated_website_arrival_date_empty': stage3_count,
        'tracking_number_empty': stage4_count,
        'estimated_delivery_date_empty': stage5_count,
        'other': stage6_count
    }

    # Create HistoricalData records
    historical_records_created = 0
    for stage_name, count in result_data.items():
        HistoricalData.objects.create(
            model='Purchasing',
            slug=f"stage:{stage_name}",
            value=count
        )
        historical_records_created += 1

    return Response({
        'status': 'success',
        'data': result_data,
        'total': total_count,
        'historical_records_created': historical_records_created
    }, status=status.HTTP_200_OK)


@extend_schema(
    request=CreateLegalPersonOfflineWithInventorySerializer,
    responses={
        201: CreateLegalPersonOfflineWithInventoryResponseSerializer,
        207: CreateLegalPersonOfflineWithInventoryResponseSerializer,
        400: OpenApiTypes.OBJECT,
    },
    description="""
    Create a LegalPersonOffline instance with associated inventory items.

    This endpoint creates a new LegalPersonOffline record and optionally creates
    associated inventory items based on the provided JAN and IMEI data.

    **Required Fields:**
    - username: Customer username

    **Optional Fields:**
    - appointment_time: Scheduled appointment time (ISO 8601 format)
    - visit_time: Actual visit time (ISO 8601 format)
    - inventory_data: List of inventory items with JAN and IMEI
    - inventory_times: Optional time fields for all inventory items
    - batch_level_1: First level batch identifier (applied to all inventory items)
    - batch_level_2: Second level batch identifier (applied to all inventory items)
    - batch_level_3: Third level batch identifier (applied to all inventory items)

    **Inventory Time Fields (optional):**
    - transaction_confirmed_at
    - scheduled_arrival_at
    - checked_arrival_at_1
    - checked_arrival_at_2

    **Batch Management Fields (optional):**
    - batch_level_1: First level batch identifier
    - batch_level_2: Second level batch identifier
    - batch_level_3: Third level batch identifier

    **Behavior:**
    - If inventory_data is empty or not provided, only LegalPersonOffline is created
    - If JAN is empty/null, inventory is created without product association
    - If IMEI is empty/null, inventory is created with IMEI=null
    - If IMEI is duplicate, that inventory item is skipped (logged)
    - All inventory items are linked to the created LegalPersonOffline via source3

    **Status Codes:**
    - 201: Successfully created with all inventory items
    - 207: Partially successful (some inventory items were skipped)
    - 400: Validation error
    """,
    examples=[
        OpenApiExample(
            'Full Request Example',
            value={
                "username": "customer123",
                "appointment_time": "2026-01-15T10:00:00Z",
                "visit_time": "2026-01-15T10:30:00Z",
                "inventory_data": [
                    {
                        "jan": "4547597992388",
                        "imei": "123456789012345"
                    },
                    {
                        "jan": "4547597992395",
                        "imei": "987654321098765"
                    }
                ],
                "inventory_times": {
                    "transaction_confirmed_at": "2026-01-15T10:30:00Z",
                    "scheduled_arrival_at": "2026-01-22T00:00:00Z"
                },
                "batch_level_1": "WAREHOUSE-A",
                "batch_level_2": "AREA-1",
                "batch_level_3": "SHELF-01"
            },
            request_only=True,
        ),
        OpenApiExample(
            'Minimal Request Example',
            value={
                "username": "customer123"
            },
            request_only=True,
        ),
        OpenApiExample(
            'Success Response (201)',
            value={
                "status": "success",
                "message": "LegalPersonOffline created with 2 inventory items",
                "data": {
                    "legal_person_offline": {
                        "id": 123,
                        "uuid": "a1b2c3d4-e5f6-g7h8-i9j0-k1l2m3n4o5p6-q7r8s9t0-u1v2w3x4"
                    },
                    "inventories": [
                        {
                            "id": 456,
                            "uuid": "xyz123ab-cdef-4567-89ab-cdef01234567-89abcdef-01234567"
                        },
                        {
                            "id": 457,
                            "uuid": "abc456de-f012-3456-7890-abcdef123456-78901234-56789012"
                        }
                    ]
                }
            },
            response_only=True,
            status_codes=['201'],
        ),
        OpenApiExample(
            'Partial Success Response (207)',
            value={
                "status": "partial_success",
                "message": "LegalPersonOffline created with 1 inventory item. 1 item(s) skipped due to errors.",
                "data": {
                    "legal_person_offline": {
                        "id": 123,
                        "uuid": "a1b2c3d4-e5f6-g7h8-i9j0-k1l2m3n4o5p6-q7r8s9t0-u1v2w3x4"
                    },
                    "inventories": [
                        {
                            "id": 456,
                            "uuid": "xyz123ab-cdef-4567-89ab-cdef01234567-89abcdef-01234567"
                        }
                    ]
                }
            },
            response_only=True,
            status_codes=['207'],
        ),
    ],
)
@api_view(['POST'])
@authentication_classes([SimpleTokenAuthentication])
def create_legal_person_offline_with_inventory(request):
    """
    Create a LegalPersonOffline instance with associated inventory items.
    创建 LegalPersonOffline 实例并关联库存。

    Authentication: BATCH_STATS_API_TOKEN via Authorization header
    Format: Authorization: Bearer <BATCH_STATS_API_TOKEN>
    """
    # Validate request data
    serializer = CreateLegalPersonOfflineWithInventorySerializer(data=request.data)
    if not serializer.is_valid():
        return Response({
            'status': 'error',
            'message': 'Validation error',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    validated_data = serializer.validated_data

    # Extract fields
    username = validated_data['username']
    appointment_time = validated_data.get('appointment_time')
    visit_time = validated_data.get('visit_time')
    inventory_data_list = validated_data.get('inventory_data', [])
    inventory_times = validated_data.get('inventory_times')
    batch_level_1 = validated_data.get('batch_level_1')
    batch_level_2 = validated_data.get('batch_level_2')
    batch_level_3 = validated_data.get('batch_level_3')

    # Convert inventory_data from list of dicts to list of tuples
    inventory_tuples = []
    for item in inventory_data_list:
        jan = item.get('jan', '')
        imei = item.get('imei', '')
        inventory_tuples.append((jan, imei))

    # Prepare fields for LegalPersonOffline
    legal_person_fields = {
        'username': username,
    }

    if appointment_time is not None:
        legal_person_fields['appointment_time'] = appointment_time

    if visit_time is not None:
        legal_person_fields['visit_time'] = visit_time

    # Add inventory_times if provided
    if inventory_times:
        legal_person_fields['inventory_times'] = inventory_times

    # Add batch level fields if provided
    if batch_level_1 is not None:
        legal_person_fields['batch_level_1'] = batch_level_1
    if batch_level_2 is not None:
        legal_person_fields['batch_level_2'] = batch_level_2
    if batch_level_3 is not None:
        legal_person_fields['batch_level_3'] = batch_level_3

    try:
        # Call create_with_inventory with skip_on_error=True
        legal_person, inventories, skipped_count = LegalPersonOffline.create_with_inventory(
            inventory_data=inventory_tuples,
            skip_on_error=True,
            **legal_person_fields
        )

        # Prepare response data
        response_data = {
            'legal_person_offline': {
                'id': legal_person.id,
                'uuid': legal_person.uuid,
            },
            'inventories': [
                {
                    'id': inv.id,
                    'uuid': inv.uuid,
                }
                for inv in inventories
            ]
        }

        # Determine status and message
        total_items = len(inventory_tuples)
        created_items = len(inventories)

        if skipped_count == 0:
            # All items created successfully
            response_status = 'success'
            if created_items == 0:
                message = 'LegalPersonOffline created with 0 inventory items'
            else:
                message = f'LegalPersonOffline created with {created_items} inventory item{"s" if created_items != 1 else ""}'
            http_status = status.HTTP_201_CREATED
        else:
            # Some items were skipped
            response_status = 'partial_success'
            message = f'LegalPersonOffline created with {created_items} inventory item{"s" if created_items != 1 else ""}. {skipped_count} item(s) skipped due to errors.'
            http_status = status.HTTP_207_MULTI_STATUS

        return Response({
            'status': response_status,
            'message': message,
            'data': response_data
        }, status=http_status)

    except Exception as e:
        # Unexpected error
        return Response({
            'status': 'error',
            'message': f'Failed to create LegalPersonOffline: {str(e)}'
        }, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    summary="Export iPhone Inventory to Dashboard Excel",
    description="""
    Export iPhone inventory data to Excel file in Nextcloud Data_Dashboard folder.
    导出iPhone库存数据到Nextcloud的Data_Dashboard文件夹中的Excel文件。

    This endpoint:
    1. Checks if "iPhone inventory" file exists in Data_Dashboard folder (any extension)
    2. If exists, downloads it and writes data to existing file (preserving macros if .xlsm)
    3. If not exists, creates a new file "iPhone inventory.xlsx"
    4. Uploads the file back to Nextcloud

    Excel File Structure:
    - Row 1: Variable names (hidden)
    - Row 2: Japanese headers
    - Row 3+: Data
    - Cell protection: Only batch_level_1/2/3 columns are editable (password protected)

    Data Exported:
    - Only Inventory records where iphone field is not null
    - Includes related data from EcSite (source1), Purchasing (source2), 
      LegalPersonOffline (source3), TemporaryChannel (source4)
    - Includes OfficialAccount and Payment card information via Purchasing

    Authentication: BATCH_STATS_API_TOKEN via Authorization header
    Format: Authorization: Bearer <BATCH_STATS_API_TOKEN>
    """,
    request=None,
    responses={
        200: ExportIPhoneInventoryDashboardResponseSerializer,
        500: ExportIPhoneInventoryDashboardResponseSerializer
    }
)
@api_view(['POST'])
@authentication_classes([SimpleTokenAuthentication])
def export_iphone_inventory_dashboard(request):
    """
    Export iPhone inventory data to Dashboard Excel file in Nextcloud.
    导出iPhone库存数据到Nextcloud的Dashboard Excel文件。

    Authentication: BATCH_STATS_API_TOKEN via Authorization header
    Format: Authorization: Bearer <BATCH_STATS_API_TOKEN>
    """
    from .utils import export_iphone_inventory_dashboard as do_export

    try:
        result = do_export()

        if result['status'] == 'success':
            return Response(result, status=status.HTTP_200_OK)
        else:
            return Response(result, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    except Exception as e:
        return Response({
            'status': 'error',
            'message': f'Unexpected error: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema(
    summary='Get iPhone inventory dashboard data in JSON format',
    description="""
    Get iPhone inventory data in JSON format.
    获取iPhone库存数据的JSON格式。

    This endpoint uses the same data aggregation logic as the export endpoint,
    but returns data in JSON format instead of exporting to Excel.

    Authentication: BATCH_STATS_API_TOKEN via Authorization header
    Format: Authorization: Bearer <BATCH_STATS_API_TOKEN>
    """,
    request=None,
    responses={
        200: GetIPhoneInventoryDashboardDataResponseSerializer,
        500: GetIPhoneInventoryDashboardDataResponseSerializer
    }
)
@api_view(['GET'])
@authentication_classes([SimpleTokenAuthentication])
def get_iphone_inventory_dashboard_data(request):
    """
    Get iPhone inventory data in JSON format.
    获取iPhone库存数据的JSON格式。

    Authentication: BATCH_STATS_API_TOKEN via Authorization header
    Format: Authorization: Bearer <BATCH_STATS_API_TOKEN>
    """
    from .excel_exporters import get_dashboard_exporter

    try:
        # Get the exporter and prepare data using the same logic
        exporter = get_dashboard_exporter('iPhoneInventoryDashboard')
        data = exporter.prepare_data()
        field_headers = exporter.get_header_names()

        return Response({
            'status': 'success',
            'data': data,
            'count': len(data),
            'field_headers': field_headers
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({
            'status': 'error',
            'message': f'Unexpected error: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema(
    summary='Batch ingest emails from n8n',
    description="""
    Batch ingest emails from n8n Gmail extraction workflow.
    批量导入来自 n8n 的邮件数据。

    This endpoint accepts emails in the n8n Gmail output format and stores them in the database.
    - Automatically creates/updates MailAccount based on the 'to' field
    - Creates/updates MailMessage records (idempotent based on provider_message_id)
    - Creates MailMessageBody for email content
    - Creates/associates MailLabel records
    - Handles errors gracefully - continues processing if individual emails fail

    Authentication: BATCH_STATS_API_TOKEN via Authorization header
    Format: Authorization: Bearer <BATCH_STATS_API_TOKEN>
    """,
    request=EmailBatchIngestRequestSerializer,
    responses={
        200: EmailBatchIngestResponseSerializer,
        400: EmailBatchIngestResponseSerializer
    }
)
@api_view(['POST'])
@authentication_classes([SimpleTokenAuthentication])
def batch_ingest_emails(request):
    """
    Batch ingest emails from n8n.
    批量导入来自 n8n 的邮件数据。

    Authentication: BATCH_STATS_API_TOKEN via Authorization header
    Format: Authorization: Bearer <BATCH_STATS_API_TOKEN>
    """
    from django.db import transaction
    from django.utils import timezone
    import logging
    from email.utils import parseaddr

    logger = logging.getLogger(__name__)

    # Log incoming request info
    logger.info(f"Received email ingest request from {request.META.get('REMOTE_ADDR')}")
    logger.debug(f"Request content type: {request.content_type}")

    # Validate request
    serializer = EmailBatchIngestRequestSerializer(data=request.data)
    if not serializer.is_valid():
        # Log detailed validation errors
        logger.error(f"Email ingest request validation failed: {serializer.errors}")
        logger.error(f"Request data keys: {list(request.data.keys()) if hasattr(request.data, 'keys') else 'N/A'}")

        # Log more details about the emails field if present
        if 'emails' in request.data:
            emails_data = request.data.get('emails')
            logger.error(f"Emails field type: {type(emails_data)}")
            if isinstance(emails_data, list):
                logger.error(f"Number of emails in request: {len(emails_data)}")
                if emails_data:
                    logger.error(f"First email data keys: {list(emails_data[0].keys()) if isinstance(emails_data[0], dict) else 'Not a dict'}")
            else:
                logger.error(f"Emails field is not a list: {emails_data}")
        else:
            logger.error("Missing 'emails' field in request data")

        return Response({
            'status': 'error',
            'message': 'Invalid request data',
            'total': 0,
            'successful': 0,
            'failed': 0,
            'results': [],
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    emails = serializer.validated_data['emails']
    results = []
    successful_count = 0
    failed_count = 0

    for email_data in emails:
        email_id = email_data.get('id', 'unknown')

        try:
            with transaction.atomic():
                # Extract recipient email to determine account
                to_field = email_data.get('to')
                if not to_field or not to_field.get('value'):
                    raise ValueError('Missing or invalid "to" field')

                # Get the first recipient email address
                recipient_email = to_field['value'][0]['address']

                # Get or create MailAccount
                account, _ = MailAccount.objects.get_or_create(
                    email_address=recipient_email,
                    defaults={
                        'provider': 'gmail'
                    }
                )

                # Extract headers
                raw_headers = email_data.get('headers', {})

                # Extract sender information from raw_headers['from'] first
                # Format: "From: Apple Store <order_acknowledgment@orders.apple.com>"
                from_address = ''
                from_name = ''

                raw_from = raw_headers.get('from', '')
                if raw_from:
                    # Remove "From: " prefix if present
                    if raw_from.startswith('From: '):
                        raw_from = raw_from[6:]  # Remove "From: "

                    # Parse the email address and name using parseaddr
                    parsed_name, parsed_address = parseaddr(raw_from)
                    from_address = parsed_address
                    from_name = parsed_name

                # Fallback to structured from.value if raw_headers parsing failed
                if not from_address:
                    from_field = email_data.get('from', {})
                    from_value = from_field.get('value', [{}])[0] if from_field.get('value') else {}
                    from_address = from_value.get('address', '')
                    from_name = from_value.get('name', '')

                sender_domain = from_address.split('@')[-1] if '@' in from_address else ''

                # Parse date
                date_header_at = email_data.get('date')

                # Extract RFC message ID
                rfc_message_id = email_data.get('messageId', '')

                # Get or create thread if thread_id provided
                thread = None
                provider_thread_id = email_data.get('threadId', '')
                if provider_thread_id:
                    thread, _ = MailThread.objects.get_or_create(
                        account=account,
                        provider_thread_id=provider_thread_id,
                        defaults={
                            'subject_norm': email_data.get('subject', '')[:512],
                            'last_message_at': date_header_at or timezone.now()
                        }
                    )

                # Create or update MailMessage
                message, created = MailMessage.objects.update_or_create(
                    account=account,
                    provider_message_id=email_id,
                    defaults={
                        'provider_thread_id': provider_thread_id,
                        'rfc_message_id': rfc_message_id,
                        'thread': thread,
                        'date_header_at': date_header_at,
                        'internal_at': timezone.now(),
                        'subject': email_data.get('subject', ''),
                        'snippet': email_data.get('text', '')[:500],
                        'size_estimate': email_data.get('sizeEstimate', 0),
                        'from_address': from_address,
                        'from_name': from_name,
                        'sender_domain': sender_domain,
                        'to_recipients': to_field.get('value', []),
                        'to_text': to_field.get('text', ''),
                        'raw_headers': raw_headers,
                        'ingested_at': timezone.now()
                    }
                )

                # Create or update MailMessageBody
                MailMessageBody.objects.update_or_create(
                    message=message,
                    defaults={
                        'text_plain': email_data.get('text', ''),
                        'text_html': email_data.get('html', ''),
                        'text_as_html': email_data.get('textAsHtml', ''),
                        'text_normalized': email_data.get('text', '')
                    }
                )

                # Handle labels
                label_ids = email_data.get('labelIds', [])
                for label_id in label_ids:
                    # Create or get label
                    label, _ = MailLabel.objects.get_or_create(
                        account=account,
                        provider_label_id=label_id,
                        defaults={
                            'name': label_id,
                            'is_system': label_id in ['INBOX', 'SENT', 'DRAFT', 'TRASH', 'SPAM', 'UNREAD', 'STARRED', 'IMPORTANT']
                        }
                    )

                    # Create message-label association
                    MailMessageLabel.objects.get_or_create(
                        message=message,
                        label=label
                    )

                results.append({
                    'email_id': email_id,
                    'status': 'success',
                    'message_db_id': message.id
                })
                successful_count += 1
                logger.info(f"Successfully ingested email {email_id} (DB ID: {message.id})")

        except Exception as e:
            error_msg = str(e)
            error_type = type(e).__name__
            logger.error(f"Failed to ingest email {email_id}: [{error_type}] {error_msg}")
            logger.error(f"Email data - Subject: {email_data.get('subject', 'N/A')[:100]}, "
                        f"From: {email_data.get('from', {}).get('value', [{}])[0].get('address', 'N/A') if email_data.get('from', {}).get('value') else 'N/A'}, "
                        f"To: {email_data.get('to', {}).get('value', [{}])[0].get('address', 'N/A') if email_data.get('to', {}).get('value') else 'N/A'}")
            logger.error(f"Full exception details:", exc_info=True)
            results.append({
                'email_id': email_id,
                'status': 'error',
                'error': f"[{error_type}] {error_msg}"
            })
            failed_count += 1

    # Prepare response
    response_data = {
        'status': 'success' if failed_count == 0 else 'partial',
        'message': f'Processed {len(emails)} emails: {successful_count} successful, {failed_count} failed',
        'total': len(emails),
        'successful': successful_count,
        'failed': failed_count,
        'results': results
    }

    # Log summary
    logger.info(f"Email ingest batch completed - Total: {len(emails)}, Successful: {successful_count}, Failed: {failed_count}")
    if failed_count > 0:
        failed_email_ids = [r['email_id'] for r in results if r['status'] == 'error']
        logger.warning(f"Failed email IDs: {failed_email_ids}")

    return Response(response_data, status=status.HTTP_200_OK)
