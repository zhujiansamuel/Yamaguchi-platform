"""
Serializers for data_aggregation app.
"""
from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
from drf_spectacular.types import OpenApiTypes
from .models import (
    iPhone, iPad, Inventory, Purchasing, OfficialAccount,
    TemporaryChannel, LegalPersonOffline, EcSite, GiftCard, GiftCardPayment,
    DebitCard, DebitCardPayment, CreditCard, CreditCardPayment, OtherPayment,
    HistoricalData, MailAccount, MailThread, MailLabel, MailMessage,
    MailMessageBody, MailMessageLabel, MailAttachment
)


class iPhoneSerializer(serializers.ModelSerializer):
    """
    Serializer for iPhone model with full CRUD support.
    """
    class Meta:
        model = iPhone
        fields = [
            'id',
            'part_number',
            'model_name',
            'capacity_gb',
            'color',
            'release_date',
            'jan',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_jan(self, value):
        """
        Validate that JAN code is 13 digits.
        """
        if not value.isdigit() or len(value) != 13:
            raise serializers.ValidationError("JAN code must be exactly 13 digits")
        return value

    def validate_capacity_gb(self, value):
        """
        Validate that capacity is a positive number.
        """
        if value <= 0:
            raise serializers.ValidationError("Capacity must be a positive number")
        return value


class iPadSerializer(serializers.ModelSerializer):
    """
    Serializer for iPad model with full CRUD support.
    """
    class Meta:
        model = iPad
        fields = [
            'id',
            'part_number',
            'model_name',
            'capacity_gb',
            'color',
            'release_date',
            'jan',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_jan(self, value):
        """
        Validate that JAN code is 13 digits.
        """
        if not value.isdigit() or len(value) != 13:
            raise serializers.ValidationError("JAN code must be exactly 13 digits")
        return value

    def validate_capacity_gb(self, value):
        """
        Validate that capacity is a positive number.
        """
        if value <= 0:
            raise serializers.ValidationError("Capacity must be a positive number")
        return value


class OfficialAccountSerializer(serializers.ModelSerializer):
    """
    Serializer for OfficialAccount model with full CRUD support.
    官方账号序列化器，支持完整的CRUD操作。
    """
    purchasing_orders_count = serializers.SerializerMethodField()

    class Meta:
        model = OfficialAccount
        fields = [
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
            'purchasing_orders_count',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'uuid', 'created_at', 'updated_at']

    @extend_schema_field(OpenApiTypes.INT)
    def get_purchasing_orders_count(self, obj) -> int:
        """Return the count of related purchasing orders"""
        return obj.purchasing_orders.count()

    # TODO: Add email format validation
    def validate_email(self, value):
        """
        Validate email format.
        """
        if not value or not value.strip():
            raise serializers.ValidationError("Email cannot be empty")
        # TODO: Add proper email regex validation
        return value.strip()

    # TODO: Add account_id format validation
    def validate_account_id(self, value):
        """
        Validate account_id is not empty.
        """
        if not value or not value.strip():
            raise serializers.ValidationError("Account ID cannot be empty")
        return value.strip()

    def validate_name(self, value):
        """
        Validate name is not empty.
        """
        if not value or not value.strip():
            raise serializers.ValidationError("Name cannot be empty")
        return value.strip()

    # TODO: Add postal_code format validation (e.g., Japanese postal code format: 123-4567)
    def validate_postal_code(self, value):
        """
        Validate postal code format.
        """
        if value and not value.strip():
            return ''
        # TODO: Add proper postal code format validation
        return value.strip() if value else ''

    # TODO: Add passkey security validation and encryption
    def validate_passkey(self, value):
        """
        Validate passkey.
        """
        if not value or not value.strip():
            raise serializers.ValidationError("Passkey cannot be empty")
        # TODO: Add passkey strength validation and encryption
        return value.strip()


class TemporaryChannelSerializer(serializers.ModelSerializer):
    """
    Serializer for TemporaryChannel model with full CRUD support.
    """
    inventory_count = serializers.SerializerMethodField()

    class Meta:
        model = TemporaryChannel
        fields = [
            'id',
            'created_time',
            'expected_time',
            'record',
            'last_updated',
            'inventory_count',
        ]
        read_only_fields = ['id', 'created_time', 'last_updated']

    @extend_schema_field(OpenApiTypes.INT)
    def get_inventory_count(self, obj) -> int:
        """Return the count of related inventory items"""
        return obj.temporary_channel_inventories.count()


class InventorySerializer(serializers.ModelSerializer):
    """
    Serializer for Inventory model with full CRUD support.
    """
    product_type = serializers.SerializerMethodField()
    product_display = serializers.SerializerMethodField()
    source3_display = serializers.SerializerMethodField()

    class Meta:
        model = Inventory
        fields = [
            'id',
            'uuid',
            'flag',
            'iphone',
            'ipad',
            'imei',
            'batch_level_1',
            'batch_level_2',
            'batch_level_3',
            'product_type',
            'product_display',
            'source1',
            'source2',
            'source3',
            'source3_display',
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
        read_only_fields = [
            'id',
            'uuid',
            'created_at',
            'updated_at',
            'product_type',
            'product_display',
            'source3_display',
            'is_deleted',
        ]

    @extend_schema_field({
        'type': 'object',
        'properties': {
            'type': {'type': 'string'},
            'id': {'type': 'integer'},
            'name': {'type': 'string'}
        },
        'nullable': True
    })
    def get_product_display(self, obj) -> dict | None:
        """Return product information"""
        if obj.iphone:
            return {
                'type': 'iPhone',
                'id': obj.iphone.id,
                'name': str(obj.iphone)
            }
        elif obj.ipad:
            return {
                'type': 'iPad',
                'id': obj.ipad.id,
                'name': str(obj.ipad)
            }
        return None

    @extend_schema_field({
        'type': 'object',
        'properties': {
            'id': {'type': 'integer'},
            'uuid': {'type': 'string'},
            'username': {'type': 'string'},
            'visit_time': {'type': 'string', 'format': 'date-time'},
            'order_created_at': {'type': 'string', 'format': 'date-time'}
        },
        'nullable': True
    })
    def get_source3_display(self, obj) -> dict | None:
        """Return Legal Person Offline source information"""
        if obj.source3:
            return {
                'id': obj.source3.id,
                'uuid': obj.source3.uuid,
                'username': obj.source3.username,
                'visit_time': obj.source3.visit_time,
                'order_created_at': obj.source3.order_created_at
            }
        return None

    @extend_schema_field(OpenApiTypes.STR)
    def get_product_type(self, obj) -> str | None:
        """Return the product type (iPhone or iPad)"""
        return obj.product_type

    def validate(self, data):
        """Validate that at least one product is selected or both are None"""
        iphone = data.get('iphone')
        ipad = data.get('ipad')

        # Both can be None (未分配产品的库存)
        # But if both are provided, it's an error
        if iphone and ipad:
            raise serializers.ValidationError(
                "Cannot assign both iPhone and iPad to the same inventory item. Choose one."
            )

        # TODO: Add validation to ensure at least one source (source1, source2, source3, source4) is set
        # TODO: Add validation to prevent multiple sources being set simultaneously (if business rule requires)

        return data


class PurchasingSerializer(serializers.ModelSerializer):
    """
    Serializer for Purchasing model with full CRUD support.
    采购订单序列化器，支持完整的CRUD操作。
    """
    # Display fields for choice fields
    delivery_status_display = serializers.CharField(
        source='get_delivery_status_display',
        read_only=True
    )
    official_account_display = serializers.SerializerMethodField()
    inventory_count = serializers.SerializerMethodField()
    inventory_items = serializers.SerializerMethodField()

    class Meta:
        model = Purchasing
        fields = [
            'id',
            'uuid',
            'order_number',
            'official_account',
            'official_account_display',
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
            'shipping_method',
            'official_query_url',
            'delivery_status',
            'delivery_status_display',
            'latest_delivery_status',
            'delivery_status_query_time',
            'delivery_status_query_source',
            'last_info_updated_at',
            'account_used',
            'payment_method',
            'inventory_count',
            'inventory_items',
            'is_locked',
            'locked_at',
            'locked_by_worker',
            'is_deleted',
            'creation_source',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'uuid',
            'created_at',
            'updated_at',
            'delivery_status_display',
            'official_account_display',
            'inventory_count',
            'inventory_items',
            'is_locked',
            'locked_at',
            'locked_by_worker',
            'is_deleted',
        ]

    @extend_schema_field({
        'type': 'object',
        'properties': {
            'id': {'type': 'integer'},
            'account_id': {'type': 'string'},
            'email': {'type': 'string'},
            'name': {'type': 'string'}
        },
        'nullable': True
    })
    def get_official_account_display(self, obj) -> dict | None:
        """Return official account information"""
        if obj.official_account:
            return {
                'id': obj.official_account.id,
                'account_id': obj.official_account.account_id,
                'email': obj.official_account.email,
                'name': obj.official_account.name
            }
        return None

    @extend_schema_field(OpenApiTypes.INT)
    def get_inventory_count(self, obj) -> int:
        """Return the count of inventory items"""
        return obj.inventory_count

    @extend_schema_field({
        'type': 'array',
        'items': {
            'type': 'object',
            'properties': {
                'id': {'type': 'integer'},
                'uuid': {'type': 'string'},
                'flag': {'type': 'string'},
                'status': {'type': 'string'},
                'product_type': {'type': 'string', 'nullable': True},
                'created_at': {'type': 'string', 'format': 'date-time'}
            }
        }
    })
    def get_inventory_items(self, obj) -> list[dict]:
        """
        Return details of inventory items associated with this purchasing order.
        返回与此采购订单关联的库存项目详情。
        """
        return [
            {
                'id': inventory.id,
                'uuid': inventory.uuid,
                'flag': inventory.flag,
                'status': inventory.status,
                'product_type': inventory.product_type,
                'created_at': inventory.created_at
            }
            for inventory in obj.purchasing_inventories.all()
        ]

    def validate_order_number(self, value):
        """
        Validate order number format.
        订单号验证（允许为空）。
        """
        # order_number is now optional, can be None or empty
        if value and value.strip():
            return value.strip()
        return value


class LegalPersonOfflineSerializer(serializers.ModelSerializer):
    """
    Serializer for LegalPersonOffline model with full CRUD support.
    """
    class Meta:
        model = LegalPersonOffline
        fields = [
            'id',
            'uuid',
            'username',
            'appointment_time',
            'visit_time',
            'order_created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'uuid', 'order_created_at', 'updated_at']

    def validate_username(self, value):
        """
        Validate that username is not empty.
        """
        if not value or not value.strip():
            raise serializers.ValidationError("Username cannot be empty")
        return value.strip()


class EcSiteSerializer(serializers.ModelSerializer):
    """
    Serializer for EcSite model with full CRUD support.
    """
    inventory_count = serializers.SerializerMethodField()

    class Meta:
        model = EcSite
        fields = [
            'id',
            'reservation_number',
            'username',
            'method',
            'reservation_time',
            'visit_time',
            'order_created_at',
            'info_updated_at',
            'order_detail_url',
            'inventory_count',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'order_created_at', 'info_updated_at']

    @extend_schema_field(OpenApiTypes.INT)
    def get_inventory_count(self, obj) -> int:
        """Return the count of associated inventory items"""
        return obj.ecsite_inventories.count()

    # TODO: Add validation for reservation_number (non-empty, unique check)
    # TODO: Add validation for username (non-empty)
    # TODO: Add validation for method (non-empty)
    # TODO: Add validation for order_detail_url (valid URL format)


class GiftCardSerializer(serializers.ModelSerializer):
    """
    Serializer for GiftCard model with full CRUD support.
    礼品卡序列化器，支持完整的CRUD操作。
    """
    purchasings_count = serializers.SerializerMethodField()
    purchasings_details = serializers.SerializerMethodField()

    class Meta:
        model = GiftCard
        fields = [
            'id',
            'card_number',
            'alternative_name',
            'passkey1',
            'passkey2',
            'balance',
            'batch_encoding',
            'purchasings',
            'purchasings_count',
            'purchasings_details',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    @extend_schema_field(OpenApiTypes.INT)
    def get_purchasings_count(self, obj) -> int:
        """Return the count of associated purchasing orders"""
        return obj.purchasings.count()

    @extend_schema_field({
        'type': 'array',
        'items': {
            'type': 'object',
            'properties': {
                'id': {'type': 'integer'},
                'uuid': {'type': 'string'},
                'order_number': {'type': 'string'},
                'delivery_status': {'type': 'string'}
            }
        }
    })
    def get_purchasings_details(self, obj) -> list[dict]:
        """Return details of associated purchasing orders"""
        return [
            {
                'id': purchasing.id,
                'uuid': purchasing.uuid,
                'order_number': purchasing.order_number,
                'delivery_status': purchasing.delivery_status,
            }
            for purchasing in obj.purchasings.all()
        ]

    def validate_balance(self, value):
        """
        Validate that balance is not negative.
        """
        if value < 0:
            raise serializers.ValidationError("Balance cannot be negative")
        return value

    def validate_card_number(self, value):
        """
        Validate that card_number is not empty.
        """
        if not value or not value.strip():
            raise serializers.ValidationError("Card number cannot be empty")
        return value.strip()


class DebitCardPaymentSerializer(serializers.ModelSerializer):
    """
    Serializer for DebitCardPayment intermediate model.
    借记卡支付中间表序列化器。
    """
    debit_card_number = serializers.SerializerMethodField()
    purchasing_order_number = serializers.SerializerMethodField()

    class Meta:
        model = DebitCardPayment
        fields = [
            'id',
            'debit_card',
            'debit_card_number',
            'purchasing',
            'purchasing_order_number',
            'payment_amount',
            'payment_time',
            'payment_status',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'payment_time', 'created_at', 'updated_at']

    @extend_schema_field(OpenApiTypes.STR)
    def get_debit_card_number(self, obj) -> str | None:
        """Return the debit card number"""
        return obj.debit_card.card_number if obj.debit_card else None

    @extend_schema_field(OpenApiTypes.STR)
    def get_purchasing_order_number(self, obj) -> str | None:
        """Return the purchasing order number"""
        return obj.purchasing.order_number if obj.purchasing else None

    def validate_payment_amount(self, value):
        """
        Validate that payment amount is positive.
        """
        if value <= 0:
            raise serializers.ValidationError("Payment amount must be greater than zero")
        return value


class DebitCardSerializer(serializers.ModelSerializer):
    """
    Serializer for DebitCard model with full CRUD support.
    借记卡序列化器，支持完整的CRUD操作。
    """
    payments_count = serializers.SerializerMethodField()
    payments_details = serializers.SerializerMethodField()
    purchasings_count = serializers.SerializerMethodField()

    class Meta:
        model = DebitCard
        fields = [
            'id',
            'card_number',
            'alternative_name',
            'expiry_month',
            'expiry_year',
            'passkey',
            'last_balance_update',
            'balance',
            'batch_encoding',
            'purchasings',
            'purchasings_count',
            'payments_count',
            'payments_details',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    @extend_schema_field(OpenApiTypes.INT)
    def get_payments_count(self, obj) -> int:
        """Return the count of payments made with this debit card"""
        return obj.payments.count()

    @extend_schema_field({
        'type': 'array',
        'items': {
            'type': 'object',
            'properties': {
                'id': {'type': 'integer'},
                'purchasing_order': {'type': 'string', 'nullable': True},
                'payment_amount': {'type': 'string'},
                'payment_time': {'type': 'string', 'format': 'date-time'},
                'payment_status': {'type': 'string'}
            }
        }
    })
    def get_payments_details(self, obj) -> list[dict]:
        """Return details of payments made with this debit card"""
        return [
            {
                'id': payment.id,
                'purchasing_order': payment.purchasing.order_number if payment.purchasing else None,
                'payment_amount': str(payment.payment_amount),
                'payment_time': payment.payment_time,
                'payment_status': payment.payment_status,
            }
            for payment in obj.payments.all()
        ]

    @extend_schema_field(OpenApiTypes.INT)
    def get_purchasings_count(self, obj) -> int:
        """Return the count of associated purchasing orders"""
        return obj.purchasings.count()

    def validate_balance(self, value):
        """
        Validate that balance is not negative.
        """
        if value < 0:
            raise serializers.ValidationError("Balance cannot be negative")
        return value

    def validate_card_number(self, value):
        """
        Validate that card_number is not empty.
        """
        if not value or not value.strip():
            raise serializers.ValidationError("Card number cannot be empty")
        return value.strip()

    def validate_expiry_month(self, value):
        """
        Validate that expiry_month is between 1 and 12.
        """
        if value < 1 or value > 12:
            raise serializers.ValidationError("Expiry month must be between 1 and 12")
        return value

    def validate_expiry_year(self, value):
        """
        Validate that expiry_year is not in the past.
        """
        from datetime import datetime
        current_year = datetime.now().year
        if value < current_year:
            raise serializers.ValidationError(f"Expiry year cannot be before {current_year}")
        return value

    def validate(self, data):
        """
        Validate that the card has not expired.
        """
        from datetime import datetime
        expiry_month = data.get('expiry_month')
        expiry_year = data.get('expiry_year')

        if expiry_month and expiry_year:
            current_date = datetime.now()
            if expiry_year == current_date.year and expiry_month < current_date.month:
                raise serializers.ValidationError(
                    "Card has expired (expiry date is in the past)"
                )

        return data


class CreditCardPaymentSerializer(serializers.ModelSerializer):
    """
    Serializer for CreditCardPayment intermediate model.
    信用卡支付中间表序列化器。
    """
    credit_card_number = serializers.SerializerMethodField()
    purchasing_order_number = serializers.SerializerMethodField()

    class Meta:
        model = CreditCardPayment
        fields = [
            'id',
            'credit_card',
            'credit_card_number',
            'purchasing',
            'purchasing_order_number',
            'payment_amount',
            'payment_time',
            'payment_status',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'payment_time', 'created_at', 'updated_at']

    @extend_schema_field(OpenApiTypes.STR)
    def get_credit_card_number(self, obj) -> str | None:
        """Return the credit card number"""
        return obj.credit_card.card_number if obj.credit_card else None

    @extend_schema_field(OpenApiTypes.STR)
    def get_purchasing_order_number(self, obj) -> str | None:
        """Return the purchasing order number"""
        return obj.purchasing.order_number if obj.purchasing else None


class CreditCardSerializer(serializers.ModelSerializer):
    """
    Serializer for CreditCard model with full CRUD support.
    信用卡序列化器，支持完整的CRUD操作。
    """
    payments_count = serializers.SerializerMethodField()
    payments_details = serializers.SerializerMethodField()
    purchasings_count = serializers.SerializerMethodField()

    class Meta:
        model = CreditCard
        fields = [
            'id',
            'card_number',
            'alternative_name',
            'expiry_month',
            'expiry_year',
            'passkey',
            'last_balance_update',
            'credit_limit',
            'batch_encoding',
            'purchasings',
            'purchasings_count',
            'payments_count',
            'payments_details',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    @extend_schema_field(OpenApiTypes.INT)
    def get_payments_count(self, obj) -> int:
        """Return the count of payments made with this credit card"""
        return obj.payments.count()

    @extend_schema_field({
        'type': 'array',
        'items': {
            'type': 'object',
            'properties': {
                'id': {'type': 'integer'},
                'purchasing_order': {'type': 'string', 'nullable': True},
                'payment_amount': {'type': 'string'},
                'payment_time': {'type': 'string', 'format': 'date-time'},
                'payment_status': {'type': 'string'}
            }
        }
    })
    def get_payments_details(self, obj) -> list[dict]:
        """Return details of payments made with this credit card"""
        return [
            {
                'id': payment.id,
                'purchasing_order': payment.purchasing.order_number if payment.purchasing else None,
                'payment_amount': str(payment.payment_amount),
                'payment_time': payment.payment_time,
                'payment_status': payment.payment_status,
            }
            for payment in obj.payments.all()
        ]

    @extend_schema_field(OpenApiTypes.INT)
    def get_purchasings_count(self, obj) -> int:
        """Return the count of associated purchasing orders"""
        return obj.purchasings.count()

    def validate_credit_limit(self, value):
        """
        Validate that credit limit is not negative.
        """
        if value < 0:
            raise serializers.ValidationError("Credit limit cannot be negative")
        return value

    def validate_card_number(self, value):
        """
        Validate that card_number is not empty.
        """
        if not value or not value.strip():
            raise serializers.ValidationError("Card number cannot be empty")
        return value.strip()

    def validate_expiry_month(self, value):
        """
        Validate that expiry_month is between 1 and 12.
        """
        if value < 1 or value > 12:
            raise serializers.ValidationError("Expiry month must be between 1 and 12")
        return value

    def validate_expiry_year(self, value):
        """
        Validate that expiry_year is not in the past.
        """
        from datetime import datetime
        current_year = datetime.now().year
        if value < current_year:
            raise serializers.ValidationError(f"Expiry year cannot be before {current_year}")
        return value

    def validate(self, data):
        """
        Validate that the card has not expired.
        """
        from datetime import datetime
        expiry_month = data.get('expiry_month')
        expiry_year = data.get('expiry_year')

        if expiry_month and expiry_year:
            current_date = datetime.now()
            if expiry_year == current_date.year and expiry_month < current_date.month:
                raise serializers.ValidationError(
                    "Card has expired (expiry date is in the past)"
                )

        return data


class GiftCardPaymentSerializer(serializers.ModelSerializer):
    """
    Serializer for GiftCardPayment intermediate model.
    礼品卡支付中间表序列化器。
    """
    gift_card_number = serializers.SerializerMethodField()
    purchasing_order_number = serializers.SerializerMethodField()

    class Meta:
        model = GiftCardPayment
        fields = [
            'id',
            'gift_card',
            'gift_card_number',
            'purchasing',
            'purchasing_order_number',
            'payment_amount',
            'payment_time',
            'payment_status',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'payment_time', 'created_at', 'updated_at']

    @extend_schema_field(OpenApiTypes.STR)
    def get_gift_card_number(self, obj) -> str | None:
        """Return the gift card number"""
        return obj.gift_card.card_number if obj.gift_card else None

    @extend_schema_field(OpenApiTypes.STR)
    def get_purchasing_order_number(self, obj) -> str | None:
        """Return the purchasing order number"""
        return obj.purchasing.order_number if obj.purchasing else None


class OtherPaymentSerializer(serializers.ModelSerializer):
    """
    Serializer for OtherPayment model.
    其他支付方式序列化器。
    """
    purchasing_order_number = serializers.SerializerMethodField()

    class Meta:
        model = OtherPayment
        fields = [
            'id',
            'purchasing',
            'purchasing_order_number',
            'payment_info',
            'payment_amount',
            'payment_time',
            'payment_status',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'payment_time', 'created_at', 'updated_at']

    @extend_schema_field(OpenApiTypes.STR)
    def get_purchasing_order_number(self, obj) -> str | None:
        """Return the purchasing order number"""
        return obj.purchasing.order_number if obj.purchasing else None


class HistoricalDataSerializer(serializers.ModelSerializer):
    """
    Serializer for HistoricalData model.
    历史数据序列化器。
    """
    class Meta:
        model = HistoricalData
        fields = [
            'id',
            'model',
            'slug',
            'value',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']


# Serializers for LegalPersonOffline create_with_inventory API

class InventoryItemSerializer(serializers.Serializer):
    """
    Serializer for individual inventory item in the inventory_data array.
    库存项序列化器，用于 inventory_data 数组中的每个项。
    """
    jan = serializers.CharField(
        max_length=13,
        required=False,
        allow_blank=True,
        allow_null=True,
        help_text='JAN code (13 digits). Can be empty to create inventory without product association.'
    )
    imei = serializers.CharField(
        max_length=17,
        required=False,
        allow_blank=True,
        allow_null=True,
        help_text='IMEI number (up to 17 characters). Can be empty.'
    )


class InventoryTimesSerializer(serializers.Serializer):
    """
    Serializer for inventory time fields.
    库存时间字段序列化器。
    """
    transaction_confirmed_at = serializers.DateTimeField(
        required=False,
        allow_null=True,
        help_text='Transaction confirmation time'
    )
    scheduled_arrival_at = serializers.DateTimeField(
        required=False,
        allow_null=True,
        help_text='Scheduled arrival time'
    )
    checked_arrival_at_1 = serializers.DateTimeField(
        required=False,
        allow_null=True,
        help_text='First checked arrival time'
    )
    checked_arrival_at_2 = serializers.DateTimeField(
        required=False,
        allow_null=True,
        help_text='Second checked arrival time'
    )


class CreateLegalPersonOfflineWithInventorySerializer(serializers.Serializer):
    """
    Serializer for creating LegalPersonOffline with inventory items.
    创建 LegalPersonOffline 并关联库存的序列化器。
    """
    # Required field
    username = serializers.CharField(
        max_length=50,
        required=True,
        help_text='Customer username (required)'
    )

    # Optional LegalPersonOffline fields
    appointment_time = serializers.DateTimeField(
        required=False,
        allow_null=True,
        help_text='Scheduled appointment time at store'
    )
    visit_time = serializers.DateTimeField(
        required=False,
        allow_null=True,
        help_text='Actual visit time to store'
    )

    # Inventory data
    inventory_data = serializers.ListField(
        child=InventoryItemSerializer(),
        required=False,
        allow_empty=True,
        default=list,
        help_text='List of inventory items to create'
    )

    # Inventory times
    inventory_times = InventoryTimesSerializer(
        required=False,
        allow_null=True,
        help_text='Optional time fields to apply to all inventory items'
    )

    # Batch management fields
    batch_level_1 = serializers.CharField(
        max_length=255,
        required=False,
        allow_blank=True,
        allow_null=True,
        help_text='First level batch identifier (applied to all inventory items)'
    )
    batch_level_2 = serializers.CharField(
        max_length=255,
        required=False,
        allow_blank=True,
        allow_null=True,
        help_text='Second level batch identifier (applied to all inventory items)'
    )
    batch_level_3 = serializers.CharField(
        max_length=255,
        required=False,
        allow_blank=True,
        allow_null=True,
        help_text='Third level batch identifier (applied to all inventory items)'
    )


class SimpleLegalPersonOfflineSerializer(serializers.Serializer):
    """
    Simple serializer for LegalPersonOffline response (only id and uuid).
    简化的 LegalPersonOffline 响应序列化器（仅返回 id 和 uuid）。
    """
    id = serializers.IntegerField(read_only=True)
    uuid = serializers.CharField(read_only=True)


class SimpleInventorySerializer(serializers.Serializer):
    """
    Simple serializer for Inventory response (only id and uuid).
    简化的 Inventory 响应序列化器（仅返回 id 和 uuid）。
    """
    id = serializers.IntegerField(read_only=True)
    uuid = serializers.CharField(read_only=True)


class CreateLegalPersonOfflineWithInventoryResponseSerializer(serializers.Serializer):
    """
    Serializer for API response.
    API 响应序列化器。
    """
    status = serializers.CharField(read_only=True)
    message = serializers.CharField(read_only=True)
    data = serializers.DictField(read_only=True)

class ExportIPhoneInventoryDashboardResponseSerializer(serializers.Serializer):
    """
    Serializer for export_iphone_inventory_dashboard response.
    """
    status = serializers.CharField(read_only=True, help_text="Status of the export (success or error)")
    message = serializers.CharField(read_only=True, help_text="Detailed message about the export result")
    filename = serializers.CharField(read_only=True, required=False, help_text="Name of the exported file")
    url = serializers.CharField(read_only=True, required=False, help_text="URL to the exported file in Nextcloud")
    file_existed = serializers.BooleanField(read_only=True, required=False, help_text="Whether the file already existed before export")

class GetIPhoneInventoryDashboardDataResponseSerializer(serializers.Serializer):
    """
    Serializer for get_iphone_inventory_dashboard_data response.
    """
    status = serializers.CharField(read_only=True, help_text="Status of the request (success or error)")
    data = serializers.ListField(
        child=serializers.DictField(),
        read_only=True,
        help_text="List of iPhone inventory records with all related data"
    )
    count = serializers.IntegerField(read_only=True, help_text="Total number of records")
    field_headers = serializers.DictField(read_only=True, help_text="Mapping of field names to Japanese headers")
    message = serializers.CharField(read_only=True, required=False, help_text="Error message if status is error")


# ====== Email/Mail Serializers ======

class EmailAddressValueSerializer(serializers.Serializer):
    """
    Serializer for email address value from n8n format.
    """
    address = serializers.EmailField(required=True)
    name = serializers.CharField(required=False, allow_blank=True, default='')


class EmailAddressFieldSerializer(serializers.Serializer):
    """
    Serializer for email address field from n8n format (from/to).
    """
    value = serializers.ListField(
        child=EmailAddressValueSerializer(),
        required=True,
        min_length=1
    )
    text = serializers.CharField(required=False, allow_blank=True, default='')
    html = serializers.CharField(required=False, allow_blank=True, default='')


class NullableCharField(serializers.CharField):
    """
    CharField that accepts null/false values and converts them to empty string.
    Some email fields like 'html' may come as false or null from Gmail when empty.
    """
    def __init__(self, **kwargs):
        kwargs['allow_null'] = True
        super().__init__(**kwargs)

    def run_validation(self, data=serializers.empty):
        # Convert None or False to empty string before validation
        if data is None or data is False:
            data = ''
        return super().run_validation(data)


class EmailIngestItemSerializer(serializers.Serializer):
    """
    Serializer for individual email item in batch ingest request.
    单个邮件导入项的序列化器。
    """
    id = serializers.CharField(required=True, help_text='Gmail message ID')
    threadId = serializers.CharField(required=False, allow_blank=True, default='')
    labelIds = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        default=list,
        help_text='List of Gmail label IDs'
    )
    sizeEstimate = serializers.IntegerField(required=False, default=0)
    headers = serializers.DictField(required=False, default=dict)
    html = NullableCharField(required=False, allow_blank=True, default='')
    text = NullableCharField(required=False, allow_blank=True, default='')
    textAsHtml = NullableCharField(required=False, allow_blank=True, default='')
    subject = serializers.CharField(required=False, allow_blank=True, default='')
    date = serializers.DateTimeField(required=False, allow_null=True)
    messageId = serializers.CharField(required=False, allow_blank=True, default='')
    from_field = EmailAddressFieldSerializer(source='from', required=False)
    to = EmailAddressFieldSerializer(required=False)


class EmailBatchIngestRequestSerializer(serializers.Serializer):
    """
    Serializer for batch email ingest request.
    批量邮件导入请求序列化器。
    """
    emails = serializers.ListField(
        child=EmailIngestItemSerializer(),
        required=True,
        min_length=1,
        help_text='List of emails to ingest'
    )


class EmailIngestResultSerializer(serializers.Serializer):
    """
    Serializer for individual email ingest result.
    单个邮件导入结果序列化器。
    """
    email_id = serializers.CharField(read_only=True)
    status = serializers.ChoiceField(
        choices=['success', 'error'],
        read_only=True
    )
    message_db_id = serializers.IntegerField(required=False, allow_null=True, read_only=True)
    error = serializers.CharField(required=False, allow_blank=True, read_only=True)


class EmailBatchIngestResponseSerializer(serializers.Serializer):
    """
    Serializer for batch email ingest response.
    批量邮件导入响应序列化器。
    """
    status = serializers.CharField(read_only=True)
    message = serializers.CharField(read_only=True)
    total = serializers.IntegerField(read_only=True)
    successful = serializers.IntegerField(read_only=True)
    failed = serializers.IntegerField(read_only=True)
    results = serializers.ListField(
        child=EmailIngestResultSerializer(),
        read_only=True
    )
