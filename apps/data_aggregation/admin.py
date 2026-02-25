"""
Admin configuration for data_aggregation app.
"""
from django.contrib import admin
from apps.core.admin import BaseHistoryAdmin
from .models import (
    AggregationSource, AggregatedData, AggregationTask,
    iPhone, iPad, Inventory, TemporaryChannel, DuplicateProduct,
    LegalPersonOffline, EcSite, Purchasing, OfficialAccount, OrderConflict, OrderConflictField,
    GiftCard, GiftCardPayment, DebitCard, DebitCardPayment, CreditCard, CreditCardPayment,
    OtherPayment, HistoricalData, MailAccount, MailThread, MailLabel, MailMessage,
    MailMessageBody, MailMessageLabel, MailAttachment
)


@admin.register(AggregationSource)
class AggregationSourceAdmin(BaseHistoryAdmin):
    list_display = ['name', 'status', 'created_at', 'updated_at']
    list_filter = ['status', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(AggregatedData)
class AggregatedDataAdmin(BaseHistoryAdmin):
    list_display = ['source', 'aggregated_at', 'created_at']
    list_filter = ['source', 'aggregated_at']
    search_fields = ['source__name']
    readonly_fields = ['created_at']
    date_hierarchy = 'aggregated_at'


@admin.register(AggregationTask)
class AggregationTaskAdmin(BaseHistoryAdmin):
    list_display = ['task_id', 'source', 'status', 'started_at', 'completed_at']
    list_filter = ['status', 'created_at']
    search_fields = ['task_id', 'source__name']
    readonly_fields = ['created_at', 'started_at', 'completed_at']


@admin.register(iPhone)
class iPhoneAdmin(BaseHistoryAdmin):
    list_display = ['part_number', 'model_name', 'capacity_gb', 'color', 'release_date', 'jan', 'is_deleted']
    list_filter = ['model_name', 'capacity_gb', 'color', 'release_date', 'is_deleted']
    search_fields = ['part_number', 'model_name', 'jan', 'color']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Product Information', {
            'fields': ('part_number', 'model_name', 'capacity_gb', 'color')
        }),
        ('Release Information', {
            'fields': ('release_date', 'jan')
        }),
        ('Status', {
            'fields': ('is_deleted',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    date_hierarchy = 'release_date'


@admin.register(iPad)
class iPadAdmin(BaseHistoryAdmin):
    list_display = ['part_number', 'model_name', 'capacity_gb', 'color', 'release_date', 'jan', 'is_deleted']
    list_filter = ['model_name', 'capacity_gb', 'color', 'release_date', 'is_deleted']
    search_fields = ['part_number', 'model_name', 'jan', 'color']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Product Information', {
            'fields': ('part_number', 'model_name', 'capacity_gb', 'color')
        }),
        ('Release Information', {
            'fields': ('release_date', 'jan')
        }),
        ('Status', {
            'fields': ('is_deleted',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    date_hierarchy = 'release_date'


@admin.register(Inventory)
class InventoryAdmin(BaseHistoryAdmin):
    list_display = [
        'uuid_short',
        'flag',
        'product_display',
        'imei',
        'batch_level_1',
        'batch_level_2',
        'batch_level_3',
        'status',
        'actual_arrival_at',
        'created_at',
        'is_deleted',
    ]
    list_filter = [
        'status',
        'created_at',
        'actual_arrival_at',
        'batch_level_1',
        'batch_level_2',
        'batch_level_3',
        'source1',
        'source2',
        'source3',
        'source4',
        'is_deleted',
    ]
    search_fields = ['uuid', 'flag', 'imei']
    readonly_fields = ['uuid', 'created_at', 'updated_at']

    fieldsets = (
        ('Identification', {
            'fields': ('uuid', 'flag')
        }),
        ('Product Information', {
            'fields': ('iphone', 'ipad', 'imei')
        }),
        ('Batch Information', {
            'fields': ('batch_level_1', 'batch_level_2', 'batch_level_3'),
            'classes': ('collapse',)
        }),
        ('Purchase Sources', {
            'fields': ('source1', 'source2', 'source3', 'source4'),
            'classes': ('collapse',)
        }),
        ('Time Tracking', {
            'fields': (
                'transaction_confirmed_at',
                'scheduled_arrival_at',
                'checked_arrival_at_1',
                'checked_arrival_at_2',
                'actual_arrival_at'
            )
        }),
        ('Status', {
            'fields': ('status', 'is_deleted')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    date_hierarchy = 'created_at'

    def uuid_short(self, obj):
        """Display shortened UUID"""
        return f"{obj.uuid[:12]}..."
    uuid_short.short_description = 'UUID'

    def product_display(self, obj):
        """Display associated product"""
        if obj.iphone:
            return f"iPhone: {obj.iphone.model_name}"
        elif obj.ipad:
            return f"iPad: {obj.ipad.model_name}"
        return "No Product"
    product_display.short_description = 'Product'


@admin.register(TemporaryChannel)
class TemporaryChannelAdmin(BaseHistoryAdmin):
    list_display = ['uuid_short', 'record_short', 'expected_time', 'inventory_count', 'created_time', 'last_updated', 'is_deleted']
    list_filter = ['expected_time', 'created_time', 'is_deleted']
    search_fields = ['record']
    readonly_fields = ['uuid', 'created_time', 'last_updated']

    fieldsets = (
        ('Identification', {
            'fields': ('uuid',)
        }),
        ('Channel Information', {
            'fields': ('record', 'expected_time', 'is_deleted')
        }),
        ('Metadata', {
            'fields': ('created_time', 'last_updated'),
            'classes': ('collapse',)
        }),
    )

    date_hierarchy = 'created_time'

    def uuid_short(self, obj):
        """Display shortened UUID"""
        return f"{obj.uuid[:12]}..."
    uuid_short.short_description = 'UUID'

    def record_short(self, obj):
        """Display shortened record"""
        return f"{obj.record[:50]}..." if len(obj.record) > 50 else obj.record
    record_short.short_description = 'Record'

    def inventory_count(self, obj):
        """Display count of associated inventory items"""
        return obj.temporary_channel_inventories.count()
    inventory_count.short_description = 'Inventory Items'


@admin.register(LegalPersonOffline)
class LegalPersonOfflineAdmin(BaseHistoryAdmin):
    list_display = ['uuid_short', 'username', 'visit_time', 'appointment_time', 'order_created_at', 'creation_source', 'is_deleted']
    list_filter = ['order_created_at', 'visit_time', 'appointment_time', 'creation_source', 'is_deleted']
    search_fields = ['uuid', 'username', 'creation_source']
    readonly_fields = ['uuid', 'order_created_at', 'updated_at']

    fieldsets = (
        ('Identification', {
            'fields': ('uuid',)
        }),
        ('Customer Information', {
            'fields': ('username',)
        }),
        ('Time Information', {
            'fields': (
                'appointment_time',
                'visit_time',
                'order_created_at',
                'updated_at'
            )
        }),
        ('Source Information', {
            'fields': ('creation_source',),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('is_deleted',)
        }),
    )

    date_hierarchy = 'order_created_at'

    def uuid_short(self, obj):
        """Display shortened UUID"""
        return f"{obj.uuid[:12]}..."
    uuid_short.short_description = 'UUID'


@admin.register(EcSite)
class EcSiteAdmin(BaseHistoryAdmin):
    list_display = ['uuid_short', 'reservation_number', 'username', 'method', 'visit_time', 'order_created_at', 'inventory_count', 'is_deleted']
    list_filter = ['method', 'order_created_at', 'visit_time', 'is_deleted']
    search_fields = ['reservation_number', 'username', 'order_detail_url']
    readonly_fields = ['uuid', 'created_at', 'updated_at']

    fieldsets = (
        ('Order Information', {
            'fields': ('uuid', 'reservation_number', 'username', 'method', 'order_detail_url')
        }),
        ('Time Information', {
            'fields': ('reservation_time', 'visit_time', 'order_created_at', 'info_updated_at')
        }),
        ('Status', {
            'fields': ('is_deleted',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    date_hierarchy = 'order_created_at'

    def uuid_short(self, obj):
        """Display shortened UUID"""
        return f"{obj.uuid[:12]}..."
    uuid_short.short_description = 'UUID'

    def inventory_count(self, obj):
        """Display count of associated inventory items"""
        return obj.ecsite_inventories.count()
    inventory_count.short_description = 'Inventory Items'


@admin.register(OfficialAccount)
class OfficialAccountAdmin(BaseHistoryAdmin):
    list_display = ['uuid_short', 'account_id', 'email', 'name', 'batch_encoding', 'purchasing_orders_count', 'created_at', 'is_deleted']
    list_filter = ['created_at', 'updated_at', 'is_deleted']
    search_fields = ['uuid', 'account_id', 'email', 'name', 'postal_code', 'batch_encoding']
    readonly_fields = ['uuid', 'created_at', 'updated_at', 'purchasing_orders_count']

    fieldsets = (
        ('Identification', {
            'fields': ('uuid', 'account_id')
        }),
        ('Contact Information', {
            'fields': ('email', 'name')
        }),
        ('Address Information', {
            'fields': ('postal_code', 'address_line_1', 'address_line_2', 'address_line_3')
        }),
        ('Security', {
            'fields': ('passkey',)
        }),
        ('Batch Information', {
            'fields': ('batch_encoding',)
        }),
        ('Status', {
            'fields': ('is_deleted',)
        }),
        ('Statistics', {
            'fields': ('purchasing_orders_count',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    date_hierarchy = 'created_at'

    def uuid_short(self, obj):
        """Display shortened UUID"""
        return f"{obj.uuid[:12]}..."
    uuid_short.short_description = 'UUID'

    def purchasing_orders_count(self, obj):
        """Display count of associated purchasing orders"""
        return obj.purchasing_orders.count()
    purchasing_orders_count.short_description = 'Purchasing Orders'


@admin.register(Purchasing)
class PurchasingAdmin(BaseHistoryAdmin):
    list_display = [
        'uuid_short',
        'order_number',
        'official_account',
        'batch_encoding',
        'creation_source',
        'tracking_number',
        'delivery_status',
        'latest_delivery_status',
        'created_at',
        'shipped_at',
        'last_info_updated_at',
        'delivery_status_query_time',
        'delivery_status_query_source',
        'inventory_count',
        'is_locked',
        'is_deleted',
    ]
    list_filter = [
        'delivery_status',
        'payment_method',
        'batch_encoding',
        'batch_level_1',
        'batch_level_2',
        'batch_level_3',
        'creation_source',
        'created_at',
        'shipped_at',
        'official_account',
        'is_locked',
        'is_deleted',
    ]
    search_fields = [
        'uuid',
        'order_number',
        'tracking_number',
        'account_used',
        'batch_encoding',
        'shipping_method',
        'official_query_url',
        'delivery_status_query_source',
    ]
    readonly_fields = ['uuid', 'created_at', 'updated_at', 'inventory_count']

    fieldsets = (
        ('Identification', {
            'fields': ('uuid', 'order_number')
        }),
        ('Official Account', {
            'fields': ('official_account',)
        }),
        ('Batch Information', {
            'fields': ('batch_encoding', 'batch_level_1', 'batch_level_2', 'batch_level_3'),
            'classes': ('collapse',)
        }),
        ('Time Tracking', {
            'fields': ('created_at', 'confirmed_at', 'shipped_at', 'updated_at', 'last_info_updated_at')
        }),
        ('Delivery Information', {
            'fields': (
                'estimated_website_arrival_date',
                'estimated_website_arrival_date_2',
                'tracking_number',
                'estimated_delivery_date',
                'shipping_method',
                'official_query_url',
                'delivery_status',
                'latest_delivery_status',
                'delivery_status_query_time',
                'delivery_status_query_source',
            )
        }),
        ('Payment Information', {
            'fields': ('payment_method', 'account_used')
        }),
        ('Statistics', {
            'fields': ('inventory_count',),
            'classes': ('collapse',)
        }),
        ('Worker Lock', {
            'fields': ('is_locked', 'locked_at', 'locked_by_worker'),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('is_deleted',)
        }),
        ('Metadata', {
            'fields': ('creation_source',),
            'classes': ('collapse',)
        }),
    )

    date_hierarchy = 'created_at'

    def uuid_short(self, obj):
        """Display shortened UUID"""
        return f"{obj.uuid[:12]}..."
    uuid_short.short_description = 'UUID'

    def inventory_count(self, obj):
        """Display count of associated inventory items"""
        return obj.purchasing_inventories.count()
    inventory_count.short_description = 'Inventory Items'


@admin.register(OrderConflict)
class OrderConflictAdmin(admin.ModelAdmin):
    list_display = ['uuid', 'purchasing', 'is_processed', 'created_at']
    list_filter = ['is_processed', 'created_at']
    search_fields = ['uuid', 'purchasing__order_number', 'purchasing__uuid']
    readonly_fields = ['uuid', 'created_at']


@admin.register(OrderConflictField)
class OrderConflictFieldAdmin(admin.ModelAdmin):
    list_display = [
        'uuid',
        'order_conflict',
        'field_name',
        'old_value',
        'incoming_value',
        'source',
        'is_processed',
        'detected_at',
    ]
    list_filter = ['field_name', 'is_processed', 'detected_at', 'source']
    search_fields = ['uuid', 'field_name', 'old_value', 'incoming_value', 'source', 'order_conflict__uuid']
    readonly_fields = ['uuid', 'detected_at']


class GiftCardPaymentInline(admin.TabularInline):
    """
    Inline admin for GiftCardPayment model.
    礼品卡支付中间表内联管理。
    """
    model = GiftCardPayment
    extra = 1
    autocomplete_fields = ['purchasing']


@admin.register(GiftCard)
class GiftCardAdmin(BaseHistoryAdmin):
    """
    Admin interface for GiftCard model.
    礼品卡模型管理界面。
    """
    list_display = ['card_number', 'alternative_name', 'balance', 'batch_encoding', 'purchasings_count', 'created_at', 'updated_at', 'is_deleted']
    list_filter = ['created_at', 'updated_at', 'balance', 'is_deleted']
    search_fields = ['card_number', 'alternative_name', 'passkey1', 'passkey2', 'batch_encoding']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [GiftCardPaymentInline]

    fieldsets = (
        ('Card Information', {
            'fields': ('card_number', 'alternative_name', 'passkey1', 'passkey2', 'balance')
        }),
        ('Batch Information', {
            'fields': ('batch_encoding',)
        }),
        ('Status', {
            'fields': ('is_deleted',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    date_hierarchy = 'created_at'

    def purchasings_count(self, obj):
        """Display count of associated purchasing orders"""
        return obj.purchasings.count()
    purchasings_count.short_description = 'Purchasing Orders'


@admin.register(DebitCardPayment)
class DebitCardPaymentAdmin(BaseHistoryAdmin):
    """
    Admin interface for DebitCardPayment model.
    借记卡支付中间表管理界面。
    """
    list_display = ['id', 'debit_card_display', 'purchasing_display', 'payment_amount', 'payment_status', 'payment_time', 'is_deleted']
    list_filter = ['payment_status', 'payment_time', 'created_at', 'is_deleted']
    search_fields = ['debit_card__card_number', 'purchasing__order_number']
    readonly_fields = ['payment_time', 'created_at', 'updated_at']

    fieldsets = (
        ('Payment Information', {
            'fields': ('debit_card', 'purchasing', 'payment_amount', 'payment_status')
        }),
        ('Time Information', {
            'fields': ('payment_time', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('is_deleted',)
        }),
    )

    date_hierarchy = 'payment_time'

    def debit_card_display(self, obj):
        """Display debit card number"""
        return obj.debit_card.card_number if obj.debit_card else 'N/A'
    debit_card_display.short_description = 'Debit Card'

    def purchasing_display(self, obj):
        """Display purchasing order number"""
        return obj.purchasing.order_number if obj.purchasing else 'N/A'
    purchasing_display.short_description = 'Purchasing Order'


@admin.register(DebitCard)
class DebitCardAdmin(BaseHistoryAdmin):
    """
    Admin interface for DebitCard model.
    借记卡模型管理界面。

    Note: The 'purchasings' ManyToManyField uses a through model (DebitCardPayment),
    so it cannot be directly edited in the admin. Use DebitCardPayment admin instead.
    """
    list_display = [
        'card_number',
        'alternative_name',
        'expiry_display',
        'balance',
        'last_balance_update',
        'batch_encoding',
        'payments_count',
        'created_at',
        'is_deleted',
    ]
    list_filter = ['expiry_year', 'expiry_month', 'created_at', 'updated_at', 'is_deleted']
    search_fields = ['card_number', 'alternative_name', 'passkey', 'batch_encoding']
    readonly_fields = ['created_at', 'updated_at', 'payments_count']

    fieldsets = (
        ('Card Information', {
            'fields': ('card_number', 'alternative_name', 'expiry_month', 'expiry_year', 'passkey')
        }),
        ('Balance Information', {
            'fields': ('balance', 'last_balance_update')
        }),
        ('Batch Information', {
            'fields': ('batch_encoding',)
        }),
        ('Status', {
            'fields': ('is_deleted',)
        }),
        ('Statistics', {
            'fields': ('payments_count',),
            'description': 'Payments are managed through the DebitCardPayment model'
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    date_hierarchy = 'created_at'

    def expiry_display(self, obj):
        """Display card expiry date"""
        return f"{obj.expiry_year}-{obj.expiry_month:02d}"
    expiry_display.short_description = 'Expiry Date'

    def payments_count(self, obj):
        """Display count of payments made with this debit card"""
        return obj.payments.count()
    payments_count.short_description = 'Payment Count'


@admin.register(CreditCardPayment)
class CreditCardPaymentAdmin(BaseHistoryAdmin):
    """
    Admin interface for CreditCardPayment model.
    信用卡支付中间表管理界面。
    """
    list_display = ['id', 'credit_card_display', 'purchasing_display', 'payment_amount', 'payment_status', 'payment_time', 'is_deleted']
    list_filter = ['payment_status', 'payment_time', 'created_at', 'is_deleted']
    search_fields = ['credit_card__card_number', 'purchasing__order_number']
    readonly_fields = ['payment_time', 'created_at', 'updated_at']

    fieldsets = (
        ('Payment Information', {
            'fields': ('credit_card', 'purchasing', 'payment_amount', 'payment_status')
        }),
        ('Time Information', {
            'fields': ('payment_time', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('is_deleted',)
        }),
    )

    date_hierarchy = 'payment_time'

    def credit_card_display(self, obj):
        """Display credit card number"""
        return obj.credit_card.card_number if obj.credit_card else 'N/A'
    credit_card_display.short_description = 'Credit Card'

    def purchasing_display(self, obj):
        """Display purchasing order number"""
        return obj.purchasing.order_number if obj.purchasing else 'N/A'
    purchasing_display.short_description = 'Purchasing Order'


@admin.register(CreditCard)
class CreditCardAdmin(BaseHistoryAdmin):
    """
    Admin interface for CreditCard model.
    信用卡模型管理界面。

    Note: The 'purchasings' ManyToManyField uses a through model (CreditCardPayment),
    so it cannot be directly edited in the admin. Use CreditCardPayment admin instead.
    """
    list_display = [
        'card_number',
        'alternative_name',
        'expiry_display',
        'credit_limit',
        'last_balance_update',
        'batch_encoding',
        'payments_count',
        'created_at',
        'is_deleted',
    ]
    list_filter = ['expiry_year', 'expiry_month', 'created_at', 'updated_at', 'is_deleted']
    search_fields = ['card_number', 'alternative_name', 'passkey', 'batch_encoding']
    readonly_fields = ['created_at', 'updated_at', 'payments_count']

    fieldsets = (
        ('Card Information', {
            'fields': ('card_number', 'alternative_name', 'expiry_month', 'expiry_year', 'passkey')
        }),
        ('Credit Limit Information', {
            'fields': ('credit_limit', 'last_balance_update')
        }),
        ('Batch Information', {
            'fields': ('batch_encoding',)
        }),
        ('Status', {
            'fields': ('is_deleted',)
        }),
        ('Statistics', {
            'fields': ('payments_count',),
            'description': 'Payments are managed through the CreditCardPayment model'
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    date_hierarchy = 'created_at'

    def expiry_display(self, obj):
        """Display card expiry date"""
        return f"{obj.expiry_year}-{obj.expiry_month:02d}"
    expiry_display.short_description = 'Expiry Date'

    def payments_count(self, obj):
        """Display count of payments made with this credit card"""
        return obj.payments.count()
    payments_count.short_description = 'Payment Count'


@admin.register(GiftCardPayment)
class GiftCardPaymentAdmin(BaseHistoryAdmin):
    """
    Admin interface for GiftCardPayment model.
    礼品卡支付中间表管理界面。
    """
    list_display = ['id', 'gift_card_display', 'purchasing_display', 'payment_amount', 'payment_status', 'payment_time', 'is_deleted']
    list_filter = ['payment_status', 'payment_time', 'created_at', 'is_deleted']
    search_fields = ['gift_card__card_number', 'purchasing__order_number']
    readonly_fields = ['payment_time', 'created_at', 'updated_at']

    fieldsets = (
        ('Payment Information', {
            'fields': ('gift_card', 'purchasing', 'payment_amount', 'payment_status')
        }),
        ('Time Information', {
            'fields': ('payment_time', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('is_deleted',)
        }),
    )

    date_hierarchy = 'payment_time'

    def gift_card_display(self, obj):
        """Display gift card number"""
        return obj.gift_card.card_number if obj.gift_card else 'N/A'
    gift_card_display.short_description = 'Gift Card'

    def purchasing_display(self, obj):
        """Display purchasing order number"""
        return obj.purchasing.order_number if obj.purchasing else 'N/A'
    purchasing_display.short_description = 'Purchasing Order'


@admin.register(OtherPayment)
class OtherPaymentAdmin(BaseHistoryAdmin):
    """
    Admin interface for OtherPayment model.
    其他支付方式管理界面。
    """
    list_display = ['id', 'purchasing_display', 'payment_info_short', 'payment_amount', 'payment_status', 'payment_time']
    list_filter = ['payment_status', 'payment_time', 'created_at']
    search_fields = ['payment_info', 'purchasing__order_number']
    readonly_fields = ['payment_time', 'created_at', 'updated_at']

    fieldsets = (
        ('Payment Information', {
            'fields': ('purchasing', 'payment_info', 'payment_amount', 'payment_status')
        }),
        ('Time Information', {
            'fields': ('payment_time', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    date_hierarchy = 'payment_time'

    def purchasing_display(self, obj):
        """Display purchasing order number"""
        return obj.purchasing.order_number if obj.purchasing else 'N/A'
    purchasing_display.short_description = 'Purchasing Order'

    def payment_info_short(self, obj):
        """Display shortened payment info"""
        if len(obj.payment_info) > 50:
            return obj.payment_info[:50] + '...'
        return obj.payment_info
    payment_info_short.short_description = 'Payment Info'


@admin.register(HistoricalData)
class HistoricalDataAdmin(BaseHistoryAdmin):
    """
    Admin interface for HistoricalData model.
    历史数据管理界面。
    """
    list_display = ['model', 'slug', 'value', 'created_at']
    list_filter = ['model', 'created_at']
    search_fields = ['model', 'slug']
    readonly_fields = ['created_at']

    fieldsets = (
        ('Data Information', {
            'fields': ('model', 'slug', 'value')
        }),
        ('Metadata', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )

    date_hierarchy = 'created_at'


@admin.register(MailAccount)
class MailAccountAdmin(admin.ModelAdmin):
    list_display = ['email_address', 'provider', 'official_account', 'last_history_id', 'created_at', 'updated_at']
    list_filter = ['provider', 'created_at', 'updated_at']
    search_fields = ['email_address', 'official_account__email']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(MailThread)
class MailThreadAdmin(admin.ModelAdmin):
    list_display = ['account', 'provider_thread_id', 'subject_norm', 'last_message_at', 'created_at']
    list_filter = ['account', 'last_message_at', 'created_at']
    search_fields = ['provider_thread_id', 'subject_norm', 'account__email_address']
    readonly_fields = ['created_at']


@admin.register(MailLabel)
class MailLabelAdmin(admin.ModelAdmin):
    list_display = ['account', 'provider_label_id', 'name', 'is_system', 'created_at']
    list_filter = ['account', 'is_system', 'created_at']
    search_fields = ['provider_label_id', 'name', 'account__email_address']
    readonly_fields = ['created_at']


class MailMessageLabelInline(admin.TabularInline):
    model = MailMessageLabel
    extra = 1
    raw_id_fields = ['label']


@admin.register(MailMessage)
class MailMessageAdmin(admin.ModelAdmin):
    list_display = [
        'account',
        'provider_message_id',
        'subject',
        'from_address',
        'to_text',
        'has_attachments',
        'is_extracted',
        'date_header_at',
        'internal_at',
        'ingested_at',
    ]
    list_filter = ['account', 'has_attachments', 'is_extracted', 'date_header_at', 'internal_at', 'ingested_at']
    search_fields = ['provider_message_id', 'subject', 'from_address', 'to_text', 'account__email_address']
    readonly_fields = ['sender_domain', 'ingested_at']
    fieldsets = (
        ('Account', {
            'fields': ('account', 'thread', 'provider_thread_id', 'provider_message_id', 'rfc_message_id')
        }),
        ('Headers', {
            'fields': ('date_header_at', 'internal_at', 'raw_headers')
        }),
        ('Content', {
            'fields': ('subject', 'snippet')
        }),
        ('Participants', {
            'fields': ('from_address', 'from_name', 'sender_domain', 'to_recipients', 'to_text')
        }),
        ('Status', {
            'fields': ('has_attachments', 'size_estimate', 'is_extracted')
        }),
        ('Metadata', {
            'fields': ('ingested_at',),
            'classes': ('collapse',)
        }),
    )
    inlines = [MailMessageLabelInline]
    date_hierarchy = 'date_header_at'


@admin.register(MailMessageBody)
class MailMessageBodyAdmin(admin.ModelAdmin):
    list_display = ['message', 'created_at']
    search_fields = ['message__provider_message_id', 'message__subject']
    readonly_fields = ['created_at']
    raw_id_fields = ['message']


@admin.register(MailMessageLabel)
class MailMessageLabelAdmin(admin.ModelAdmin):
    list_display = ['message', 'label', 'created_at']
    list_filter = ['label', 'created_at']
    search_fields = ['message__provider_message_id', 'label__name']
    readonly_fields = ['created_at']
    raw_id_fields = ['message', 'label']


@admin.register(MailAttachment)
class MailAttachmentAdmin(admin.ModelAdmin):
    list_display = ['message', 'filename', 'mime_type', 'size_bytes', 'is_inline', 'created_at']
    list_filter = ['mime_type', 'is_inline', 'created_at']
    search_fields = ['filename', 'provider_attachment_id', 'message__provider_message_id']
    readonly_fields = ['created_at']
    raw_id_fields = ['message']


@admin.register(DuplicateProduct)
class DuplicateProductAdmin(admin.ModelAdmin):
    list_display = ['uuid_short', 'inventory', 'first_record_uuid', 'second_record_uuid', 'created_at']
    list_filter = ['created_at']
    search_fields = ['uuid', 'first_record_uuid', 'second_record_uuid', 'inventory__imei']
    readonly_fields = ['uuid', 'created_at']

    def uuid_short(self, obj):
        """Display shortened UUID"""
        return f"{obj.uuid[:12]}..."
    uuid_short.short_description = 'UUID'
