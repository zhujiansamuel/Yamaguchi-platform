"""
Models for data_aggregation app.
"""
from __future__ import annotations
import secrets
from datetime import datetime, date
import pytz
from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from apps.core.history import HistoricalRecordsWithSource


def generate_uuid():
    """
    Generate a 48-character unique identifier.
    Format: 12 groups of 4 hexadecimal characters
    Example: 1a2b-3c4d-5e6f-7a8b-9c0d-1e2f-3a4b-5c6d-7e8f-9a0b-1c2d-3e4f
    """
    return '-'.join([''.join(secrets.token_hex(2)) for _ in range(12)])


def ensure_tokyo_timezone(dt_value):
    """
    Ensure a datetime or date value is interpreted as Tokyo time (JST/UTC+9).
    
    Args:
        dt_value: Can be:
            - datetime with timezone: returned as-is
            - datetime without timezone (naive): interpreted as Tokyo time
            - date object: converted to datetime at midnight Tokyo time
            - string: parsed and interpreted as Tokyo time
            - None or other types: returned as-is
    
    Returns:
        datetime with timezone or original value if not applicable
    
    Examples:
        >>> ensure_tokyo_timezone(datetime(2025, 1, 20, 10, 30))  # naive datetime
        datetime(2025, 1, 20, 10, 30, tzinfo=<DstTzInfo 'Asia/Tokyo' JST+9:00:00 STD>)
        
        >>> ensure_tokyo_timezone(date(2025, 1, 20))  # date object
        datetime(2025, 1, 20, 0, 0, tzinfo=<DstTzInfo 'Asia/Tokyo' JST+9:00:00 STD>)
        
        >>> ensure_tokyo_timezone('2025-01-20')  # string
        datetime(2025, 1, 20, 0, 0, tzinfo=<DstTzInfo 'Asia/Tokyo' JST+9:00:00 STD>)
    """
    if dt_value is None:
        return None
    
    tokyo_tz = pytz.timezone('Asia/Tokyo')
    
    # Handle datetime objects
    if isinstance(dt_value, datetime):
        if dt_value.tzinfo is None:
            # Naive datetime - interpret as Tokyo time
            return tokyo_tz.localize(dt_value)
        else:
            # Already has timezone - return as-is
            return dt_value
    
    # Handle date objects
    if isinstance(dt_value, date):
        # Convert date to datetime at midnight Tokyo time
        dt = datetime.combine(dt_value, datetime.min.time())
        return tokyo_tz.localize(dt)
    
    # Handle string values
    if isinstance(dt_value, str):
        try:
            # Try to parse as datetime
            if 'T' in dt_value or ' ' in dt_value:
                # Contains time component
                parsed_dt = datetime.fromisoformat(dt_value.replace('Z', '+00:00'))
                if parsed_dt.tzinfo is None:
                    return tokyo_tz.localize(parsed_dt)
                else:
                    return parsed_dt
            else:
                # Date only string
                parsed_date = datetime.strptime(dt_value, '%Y-%m-%d').date()
                dt = datetime.combine(parsed_date, datetime.min.time())
                return tokyo_tz.localize(dt)
        except (ValueError, AttributeError):
            # If parsing fails, return original value
            return dt_value
    
    # For other types, return as-is
    return dt_value


class AggregationSource(models.Model):
    """
    Represents a data source for aggregation.
    """
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('error', 'Error'),
    ]

    name = models.CharField(max_length=255, unique=True, verbose_name='Source Name')
    description = models.TextField(blank=True, verbose_name='Description')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    config = models.JSONField(default=dict, blank=True, verbose_name='Configuration')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    history = HistoricalRecordsWithSource()

    class Meta:
        db_table = 'aggregation_sources'
        verbose_name = 'Aggregation Source'
        verbose_name_plural = 'Aggregation Sources'
        ordering = ['-created_at']

    def __str__(self):
        return self.name


class AggregatedData(models.Model):
    """
    Stores aggregated data results.
    """
    source = models.ForeignKey(
        AggregationSource,
        on_delete=models.CASCADE,
        related_name='aggregated_data'
    )
    data = models.JSONField(verbose_name='Aggregated Data')
    metadata = models.JSONField(default=dict, blank=True, verbose_name='Metadata')

    aggregated_at = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)

    history = HistoricalRecordsWithSource()

    class Meta:
        db_table = 'aggregated_data'
        verbose_name = 'Aggregated Data'
        verbose_name_plural = 'Aggregated Data'
        ordering = ['-aggregated_at']
        indexes = [
            models.Index(fields=['-aggregated_at']),
            models.Index(fields=['source', '-aggregated_at']),
        ]

    def __str__(self):
        return f"{self.source.name} - {self.aggregated_at}"


class AggregationTask(models.Model):
    """
    Tracks aggregation task execution.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    task_id = models.CharField(max_length=255, unique=True, verbose_name='Celery Task ID')
    source = models.ForeignKey(
        AggregationSource,
        on_delete=models.CASCADE,
        related_name='tasks',
        null=True,
        blank=True
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    result = models.JSONField(null=True, blank=True, verbose_name='Task Result')
    error_message = models.TextField(blank=True, verbose_name='Error Message')

    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    history = HistoricalRecordsWithSource()

    class Meta:
        db_table = 'aggregation_tasks'
        verbose_name = 'Aggregation Task'
        verbose_name_plural = 'Aggregation Tasks'
        ordering = ['-created_at']

    def __str__(self):
        return f"Task {self.task_id} - {self.status}"


class ElectronicProduct(models.Model):
    """
    Abstract base class for electronic products.
    Contains common fields for all electronic products (iPhone, iPad, Apple Watch, AirPods, etc.)
    """
    part_number = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='Part Number',
        help_text='Unique part number (e.g., MG674J/A)'
    )
    model_name = models.CharField(
        max_length=100,
        verbose_name='Model Name',
        help_text='Product model name'
    )
    capacity_gb = models.IntegerField(
        verbose_name='Capacity (GB)',
        help_text='Storage capacity in GB',
        null=True,
        blank=True
    )
    color = models.CharField(
        max_length=50,
        verbose_name='Color',
        help_text='Device color'
    )
    release_date = models.DateField(
        verbose_name='Release Date',
        help_text='Official release date'
    )
    jan = models.CharField(
        max_length=13,
        unique=True,
        verbose_name='JAN Code',
        help_text='Japanese Article Number (13 digits)'
    )

    # Metadata fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True  # This makes it an abstract base class
        ordering = ['-release_date', 'model_name']

    def __str__(self):
        if self.capacity_gb:
            return f"{self.model_name} {self.capacity_gb}GB {self.color}"
        return f"{self.model_name} {self.color}"


class DuplicateProduct(models.Model):
    """
    Model for tracking duplicate IMEI inventory items.
    重复商品模型，用于记录IMEI重复的库存项。
    """
    uuid = models.CharField(
        max_length=59,
        unique=True,
        default=generate_uuid,
        verbose_name='UUID',
        help_text='48-character globally unique identifier'
    )

    inventory = models.ForeignKey(
        'Inventory',
        on_delete=models.CASCADE,
        related_name='duplicate_records',
        verbose_name='Inventory',
        help_text='The newly created inventory item with duplicate IMEI'
    )

    first_record_uuid = models.CharField(
        max_length=59,
        verbose_name='First Record UUID',
        help_text='UUID of the existing record (LegalPersonOffline/TemporaryChannel/Purchasing/EcSite)'
    )

    second_record_uuid = models.CharField(
        max_length=59,
        verbose_name='Second Record UUID',
        help_text='UUID of the new record (LegalPersonOffline/TemporaryChannel/Purchasing/EcSite)'
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Created At'
    )

    class Meta:
        db_table = 'duplicate_products'
        verbose_name = 'Duplicate Product'
        verbose_name_plural = 'Duplicate Products'
        ordering = ['-created_at']

    def __str__(self):
        return f"Duplicate IMEI for Inventory {self.inventory.id}"


class iPhone(ElectronicProduct):
    """
    iPhone product model.
    Inherits common electronic product fields from ElectronicProduct.
    """
    # Override capacity_gb to make it required for iPhone
    capacity_gb = models.IntegerField(
        verbose_name='Capacity (GB)',
        help_text='Storage capacity in GB'
    )

    is_deleted = models.BooleanField(
        default=False,
        verbose_name='Is Deleted',
        help_text='Soft delete flag'
    )

    history = HistoricalRecordsWithSource()

    class Meta:
        db_table = 'iphones'
        verbose_name = 'iPhone'
        verbose_name_plural = 'iPhones'
        ordering = ['-release_date', 'model_name']
        indexes = [
            models.Index(fields=['model_name']),
            models.Index(fields=['release_date']),
            models.Index(fields=['jan']),
            models.Index(fields=['part_number']),
        ]


class iPad(ElectronicProduct):
    """
    iPad product model.
    Inherits common electronic product fields from ElectronicProduct.
    """
    # Override capacity_gb to make it required for iPad
    capacity_gb = models.IntegerField(
        verbose_name='Capacity (GB)',
        help_text='Storage capacity in GB'
    )

    is_deleted = models.BooleanField(
        default=False,
        verbose_name='Is Deleted',
        help_text='Soft delete flag'
    )

    history = HistoricalRecordsWithSource()

    class Meta:
        db_table = 'ipads'
        verbose_name = 'iPad'
        verbose_name_plural = 'iPads'
        ordering = ['-release_date', 'model_name']
        indexes = [
            models.Index(fields=['model_name']),
            models.Index(fields=['release_date']),
            models.Index(fields=['jan']),
            models.Index(fields=['part_number']),
        ]


class TemporaryChannel(models.Model):
    """
    Temporary channel model for tracking inventory sources.
    临时渠道模型，用于跟踪库存来源。
    """
    created_time = models.DateTimeField(
        auto_now_add=True,
        verbose_name='创建时间',
        help_text='Record creation time'
    )

    expected_time = models.DateTimeField(
        verbose_name='入库预计时间',
        help_text='Expected arrival time'
    )

    record = models.CharField(
        max_length=255,
        verbose_name='记录',
        help_text='Record information'
    )

    last_updated = models.DateTimeField(
        auto_now=True,
        verbose_name='最后更新时间',
        help_text='Last update time'
    )

    uuid = models.CharField(
        max_length=59,  # 48 chars + 11 hyphens
        unique=True,
        default=generate_uuid,
        verbose_name='UUID',
        help_text='48-character globally unique identifier'
    )

    is_deleted = models.BooleanField(
        default=False,
        verbose_name='Is Deleted',
        help_text='Soft delete flag'
    )

    history = HistoricalRecordsWithSource()

    class Meta:
        db_table = 'temporary_channels'
        verbose_name = 'Temporary Channel'
        verbose_name_plural = 'Temporary Channels'
        ordering = ['-created_time']
        indexes = [
            models.Index(fields=['-created_time']),
            models.Index(fields=['expected_time']),
        ]

    def __str__(self):
        return f"{self.record[:50]} - {self.expected_time.strftime('%Y-%m-%d %H:%M')}"


class LegalPersonOffline(models.Model):
    """
    Legal person offline store visit model.
    Represents customer visits to offline stores for product purchases.
    This model corresponds to Inventory source3 field.
    """
    # Unique identifier
    uuid = models.CharField(
        max_length=59,  # 48 chars + 11 hyphens
        unique=True,
        default=generate_uuid,
        verbose_name='UUID',
        help_text='48-character globally unique identifier'
    )

    # Customer information
    username = models.CharField(
        max_length=50,
        verbose_name='Username',
        help_text='Customer username'
    )

    # Time tracking fields
    appointment_time = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Appointment Time',
        help_text='Scheduled appointment time at store'
    )

    visit_time = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Visit Time',
        help_text='Actual visit time to store'
    )

    order_created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Order Created At',
        help_text='Order creation time'
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Updated At',
        help_text='Last update time'
    )

    is_deleted = models.BooleanField(
        default=False,
        verbose_name='Is Deleted',
        help_text='Soft delete flag'
    )

    creation_source = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name='创建来源',
        help_text='Source of order creation (e.g., API, manual import, auto sync)'
    )

    history = HistoricalRecordsWithSource()

    class Meta:
        db_table = 'legal_person_offline'
        verbose_name = 'Legal Person Offline'
        verbose_name_plural = 'Legal Person Offline'
        ordering = ['-order_created_at']
        indexes = [
            models.Index(fields=['uuid']),
            models.Index(fields=['username']),
            models.Index(fields=['-order_created_at']),
            models.Index(fields=['visit_time']),
        ]

    def __str__(self):
        date_str = self.order_created_at.strftime('%Y-%m-%d') if self.order_created_at else 'N/A'
        return f"{self.username} - {self.uuid[:8]}... ({date_str})"

    @classmethod
    def create_with_inventory(cls, inventory_data, skip_on_error=False, **fields):
        """
        Create a LegalPersonOffline instance with associated inventory items.
        创建LegalPersonOffline实例并自动创建关联的库存项目。

        Args:
            inventory_data (List[Tuple[str, str]]): List of (jan, imei) tuples.
                Each tuple represents an inventory item with:
                - jan (str): JAN code to find product in iPhone or iPad models
                - imei (str): IMEI number for the device
            skip_on_error (bool): If True, skip inventory items that fail to create
                and continue with others. If False, raise exception on any error.
                Default: False
            **fields: Keyword arguments for LegalPersonOffline fields.
                Special keys:
                - inventory_times (dict): Optional time fields for inventory items.
                    Example: {'transaction_confirmed_at': datetime, 'scheduled_arrival_at': datetime}
                    These fields will be applied to all created inventory items.
                - batch_level_1 (str): First level batch identifier (applied to all inventory items)
                - batch_level_2 (str): Second level batch identifier (applied to all inventory items)
                - batch_level_3 (str): Third level batch identifier (applied to all inventory items)

        Returns:
            tuple: (legal_person_instance, inventory_list, skipped_count)
                - legal_person_instance: Created LegalPersonOffline instance
                - inventory_list: List of created Inventory instances
                - skipped_count: Number of inventory items skipped due to errors

        Raises:
            Exception: If any database operation fails and skip_on_error=False
                (transaction will be rolled back)

        Example:
            >>> from django.utils import timezone
            >>> legal_person, inventories, skipped = LegalPersonOffline.create_with_inventory(
            ...     inventory_data=[
            ...         ('4547597992388', '123456789012345'),
            ...         ('4547597992395', '987654321098765'),
            ...     ],
            ...     username='customer123',
            ...     appointment_time=timezone.now(),
            ...     visit_time=timezone.now(),
            ...     inventory_times={
            ...         'transaction_confirmed_at': timezone.now(),
            ...         'scheduled_arrival_at': timezone.now() + timezone.timedelta(days=7)
            ...     },
            ...     skip_on_error=True
            ... )
            >>> print(f"Created {legal_person} with {len(inventories)} inventory items, {skipped} skipped")
        """
        from django.db import transaction, IntegrityError
        from django.utils import timezone
        import logging

        logger = logging.getLogger(__name__)

        with transaction.atomic():
            # Automatically record caller information if creation_source is not provided
            if 'creation_source' not in fields:
                import sys
                f = sys._getframe(1)
                caller_name = f.f_code.co_name
                caller_info = caller_name
                if 'self' in f.f_locals:
                    class_name = f.f_locals['self'].__class__.__name__
                    caller_info = f"{class_name}.{caller_name}"
                elif 'cls' in f.f_locals:
                    try:
                        class_name = f.f_locals['cls'].__name__
                        caller_info = f"{class_name}.{caller_name}"
                    except:
                        pass
                fields['creation_source'] = caller_info

            # Extract special fields
            inventory_times = fields.pop('inventory_times', {})
            batch_level_1 = fields.pop('batch_level_1', None)
            batch_level_2 = fields.pop('batch_level_2', None)
            batch_level_3 = fields.pop('batch_level_3', None)

            # Apply Tokyo timezone to datetime fields in fields
            datetime_fields = ['appointment_time', 'visit_time']
            for field in datetime_fields:
                if field in fields and fields[field] is not None:
                    fields[field] = ensure_tokyo_timezone(fields[field])

            # Apply Tokyo timezone to inventory_times
            inventory_time_fields = ['transaction_confirmed_at', 'scheduled_arrival_at', 
                                   'checked_arrival_at_1', 'checked_arrival_at_2', 'actual_arrival_at']
            for field in inventory_time_fields:
                if field in inventory_times and inventory_times[field] is not None:
                    inventory_times[field] = ensure_tokyo_timezone(inventory_times[field])

            # Create LegalPersonOffline instance
            legal_person_instance = cls.objects.create(**fields)

            # Get UUID prefix for flag generation
            uuid_prefix = legal_person_instance.uuid.split('-')[0]

            # Create inventory items
            inventory_list = []
            skipped_count = 0
            for index, (jan, imei) in enumerate(inventory_data, start=1):
                try:
                    # Search for product by JAN
                    product = None
                    product_type = None

                    # First try to find in iPhone (is_deleted=False)
                    if jan:
                        try:
                            product = iPhone.objects.get(jan=jan, is_deleted=False)
                            product_type = 'iphone'
                        except iPhone.DoesNotExist:
                            # Then try to find in iPad (is_deleted=False)
                            try:
                                product = iPad.objects.get(jan=jan, is_deleted=False)
                                product_type = 'ipad'
                            except iPad.DoesNotExist:
                                # Product not found, will create inventory without product association
                                pass

                    # Prepare inventory data
                    # Handle empty/null IMEI
                    imei_value = imei if imei and imei.strip() else None

                    inventory_fields = {
                        'source3': legal_person_instance,
                        'status': 'arrived',
                        'flag': f'LPO-{uuid_prefix}-{index:03d}',
                        'imei': imei_value,
                        'actual_arrival_at': timezone.now(),
                    }

                    # Associate product if found
                    if product and product_type == 'iphone':
                        inventory_fields['iphone'] = product
                    elif product and product_type == 'ipad':
                        inventory_fields['ipad'] = product

                    # Add batch level fields if provided
                    if batch_level_1 is not None:
                        inventory_fields['batch_level_1'] = batch_level_1
                    if batch_level_2 is not None:
                        inventory_fields['batch_level_2'] = batch_level_2
                    if batch_level_3 is not None:
                        inventory_fields['batch_level_3'] = batch_level_3

                    # Add optional time fields from inventory_times
                    for time_field, time_value in inventory_times.items():
                        if hasattr(Inventory, time_field):
                            inventory_fields[time_field] = time_value

                    # Check for duplicate IMEI before creation to log and persist
                    existing_inventory = None
                    if imei_value:
                        existing_inventory = Inventory.objects.filter(imei=imei_value).first()

                    # Create inventory (now imei is not unique, so this won't raise IntegrityError for IMEI)
                    inventory = Inventory.objects.create(**inventory_fields)
                    inventory_list.append(inventory)

                    # If duplicate was detected, log it and create DuplicateProduct record
                    if existing_inventory:
                        logger.error(
                            f"Duplicate IMEI detected for inventory item {index} for LegalPersonOffline {legal_person_instance.uuid}: "
                            f"JAN={jan}, IMEI={imei}. Existing inventory ID: {existing_inventory.id}"
                        )
                        
                        # Determine the first record's UUID
                        first_record_uuid = "Unknown"
                        if existing_inventory.source3:
                            first_record_uuid = existing_inventory.source3.uuid
                        elif existing_inventory.source4:
                            first_record_uuid = existing_inventory.source4.uuid
                        elif existing_inventory.source2:
                            first_record_uuid = existing_inventory.source2.uuid
                        elif existing_inventory.source1:
                            first_record_uuid = existing_inventory.source1.uuid
                        
                        # Create DuplicateProduct record
                        DuplicateProduct.objects.create(
                            inventory=inventory,
                            first_record_uuid=first_record_uuid,
                            second_record_uuid=legal_person_instance.uuid
                        )

                except Exception as e:
                    # Other errors (e.g. database connection, field validation)
                    if skip_on_error:
                        skipped_count += 1
                        logger.error(
                            f"Skipped inventory item {index} for LegalPersonOffline {legal_person_instance.uuid}: "
                            f"JAN={jan}, IMEI={imei}, Error: {str(e)}"
                        )
                    else:
                        raise

            return legal_person_instance, inventory_list, skipped_count


class EcSite(models.Model):
    """
    EC site order information model.
    Represents order/reservation data from e-commerce sites.
    """
    reservation_number = models.CharField(max_length=50, unique=True)
    username = models.CharField(max_length=50)
    method = models.CharField(max_length=50)
    reservation_time = models.DateTimeField(null=True, blank=True)
    visit_time = models.DateTimeField(null=True, blank=True)
    order_created_at = models.DateTimeField(auto_now_add=True)
    info_updated_at = models.DateTimeField(auto_now=True)
    order_detail_url = models.CharField(max_length=255)

    # Unique identifier
    uuid = models.CharField(
        max_length=59,  # 48 chars + 11 hyphens
        unique=True,
        default=generate_uuid,
        verbose_name='UUID',
        help_text='48-character globally unique identifier'
    )

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    is_deleted = models.BooleanField(
        default=False,
        verbose_name='Is Deleted',
        help_text='Soft delete flag'
    )

    history = HistoricalRecordsWithSource()

    class Meta:
        db_table = 'ec_site'
        verbose_name = 'EC Site'
        verbose_name_plural = 'EC Sites'
        ordering = ['-order_created_at']
        indexes = [
            models.Index(fields=['reservation_number']),
            models.Index(fields=['order_created_at']),
            models.Index(fields=['visit_time']),
        ]

    def __str__(self):
        date_str = self.order_created_at.strftime('%Y-%m-%d') if self.order_created_at else 'N/A'
        return f"{self.reservation_number} - {self.username} ({date_str})"


class Inventory(models.Model):
    """
    Inventory management model for tracking product stock.
    """
    STATUS_CHOICES = [
        ('planned', '计划中'),
        ('in_transit', '到达中'),
        ('arrived', '到达'),
        ('out_of_stock', '出库'),
        ('abnormal', '异常'),
    ]

    # Unique identifier
    uuid = models.CharField(
        max_length=59,  # 48 chars + 11 hyphens
        unique=True,
        default=generate_uuid,
        verbose_name='UUID',
        help_text='48-character globally unique identifier'
    )

    # Human-readable identifier
    flag = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Flag',
        help_text='Human-readable identifier (rules to be implemented)'
    )

    # Product category - Foreign keys to product models (nullable)
    iphone = models.ForeignKey(
        'iPhone',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='iphone_inventories',
        verbose_name='iPhone Product'
    )

    ipad = models.ForeignKey(
        'iPad',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ipad_inventories',
        verbose_name='iPad Product'
    )

    # Device IMEI number
    imei = models.CharField(
        max_length=17,
        unique=False,
        blank=True,
        null=True,
        verbose_name='IMEI',
        help_text='International Mobile Equipment Identity (up to 17 characters)'
    )

    # Batch management fields for inventory classification
    batch_level_1 = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name='Batch Level 1',
        help_text='First level batch identifier for inventory management'
    )

    batch_level_2 = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name='Batch Level 2',
        help_text='Second level batch identifier for inventory management'
    )

    batch_level_3 = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name='Batch Level 3',
        help_text='Third level batch identifier for inventory management'
    )

    # Purchase source - EC Site
    source1 = models.ForeignKey(
        'EcSite',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='ecsite_inventories',
        verbose_name='Source 1 (EC Site)',
        help_text='Purchase source 1 - EC Site'
    )

    # Purchase source 2 - Foreign key to Purchasing model
    source2 = models.ForeignKey(
        'Purchasing',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='purchasing_inventories',
        verbose_name='Source 2 (Purchasing)',
        help_text='Purchasing order associated with this inventory item'
    )

    source3 = models.ForeignKey(
        'LegalPersonOffline',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='legal_person_inventories',
        verbose_name='Source 3 - Legal Person Offline',
        help_text='Legal person offline purchase source'
    )

    source4 = models.ForeignKey(
        'TemporaryChannel',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='temporary_channel_inventories',
        verbose_name='Source 4 - Temporary Channel',
        help_text='Temporary channel purchase source'
    )

    # Time tracking fields
    transaction_confirmed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Transaction Confirmed At',
        help_text='Time when transaction was confirmed'
    )

    scheduled_arrival_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Scheduled Arrival At',
        help_text='Scheduled arrival time'
    )

    checked_arrival_at_1 = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Checked Arrival Time 1',
        help_text='First checked arrival time'
    )

    checked_arrival_at_2 = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Checked Arrival Time 2',
        help_text='Second checked arrival time'
    )

    actual_arrival_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Actual Arrival At',
        help_text='Actual arrival time'
    )

    # Status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='planned',
        verbose_name='Status'
    )

    # Metadata
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Created At',
        help_text='Record creation time'
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Updated At'
    )

    is_deleted = models.BooleanField(
        default=False,
        verbose_name='Is Deleted',
        help_text='Soft delete flag'
    )

    history = HistoricalRecordsWithSource()

    class Meta:
        db_table = 'inventory'
        verbose_name = 'Inventory'
        verbose_name_plural = 'Inventory'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['uuid']),
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
            models.Index(fields=['-actual_arrival_at']),
            models.Index(fields=['batch_level_1']),
            models.Index(fields=['batch_level_2']),
            models.Index(fields=['batch_level_3']),
        ]

    def __str__(self):
        product_info = ""
        if self.iphone:
            product_info = f"iPhone: {self.iphone}"
        elif self.ipad:
            product_info = f"iPad: {self.ipad}"
        else:
            product_info = "No Product"

        return f"{self.uuid[:8]}... - {product_info} - {self.get_status_display()}"

    @property
    def product(self):
        """Get the associated product (iPhone or iPad)."""
        return self.iphone or self.ipad

    @property
    def product_type(self):
        """Get the product type."""
        if self.iphone:
            return 'iPhone'
        elif self.ipad:
            return 'iPad'
        return None


class OfficialAccount(models.Model):
    """
    Official account model for managing account information.
    官方账号模型，用于管理账号信息。
    """
    # Unique identifier
    uuid = models.CharField(
        max_length=59,  # 48 chars + 11 hyphens
        unique=True,
        default=generate_uuid,
        verbose_name='UUID',
        help_text='48-character globally unique identifier'
    )

    # TODO: Add validation for account_id format
    account_id = models.CharField(
        max_length=50,
        verbose_name='账号ID',
        help_text='Account ID (may not be unique)'
    )

    # TODO: Add email format validation
    email = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='邮箱',
        help_text='Email address (must be unique)'
    )

    name = models.CharField(
        max_length=50,
        blank=True,
        default='',
        verbose_name='姓名',
        help_text='Account holder name'
    )

    # TODO: Add postal code format validation (e.g., Japanese postal code format)
    postal_code = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='邮编',
        help_text='Postal code'
    )

    address_line_1 = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='地址1',
        help_text='Address line 1'
    )

    address_line_2 = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='地址2',
        help_text='Address line 2'
    )

    address_line_3 = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='地址3',
        help_text='Address line 3'
    )

    # TODO: Add passkey encryption/security validation
    passkey = models.CharField(
        max_length=50,
        verbose_name='Passkey',
        help_text='Account passkey'
    )

    batch_encoding = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='批次编号',
        help_text='Batch encoding for grouping related records'
    )

    # Metadata
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Created At',
        help_text='Record creation time'
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Updated At'
    )

    is_deleted = models.BooleanField(
        default=False,
        verbose_name='Is Deleted',
        help_text='Soft delete flag'
    )

    history = HistoricalRecordsWithSource()

    class Meta:
        db_table = 'official_accounts'
        verbose_name = 'Official Account'
        verbose_name_plural = 'Official Accounts'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['uuid']),
            models.Index(fields=['email']),
            models.Index(fields=['account_id']),
            models.Index(fields=['-created_at']),
        ]

    def __str__(self):
        return f"{self.name} ({self.email})"


class Purchasing(models.Model):
    """
    Purchasing order model for tracking purchase orders and delivery.
    采购订单模型，用于跟踪采购订单和配送信息。
    """
    DELIVERY_STATUS_CHOICES = [
        ('pending_confirmation', '等待确认'),
        ('shipped', '已发送'),
        ('in_delivery', '配送中'),
        ('delivered', '已送达'),
    ]

    # Unique identifier
    uuid = models.CharField(
        max_length=59,  # 48 chars + 11 hyphens
        unique=True,
        default=generate_uuid,
        verbose_name='UUID',
        help_text='48-character globally unique identifier'
    )

    # Order information
    order_number = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name='订单号',
        help_text='Purchase order number'
    )

    # Official account relationship (one-to-many: one account has many purchasing orders)
    official_account = models.ForeignKey(
        'OfficialAccount',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='purchasing_orders',
        verbose_name='Official Account',
        help_text='Official account associated with this purchasing order'
    )

    # Batch information fields
    batch_encoding = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='批次编码',
        help_text='Batch encoding for grouping purchases'
    )

    batch_level_1 = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='批次层级1',
        help_text='Batch level 1 identifier'
    )

    batch_level_2 = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='批次层级2',
        help_text='Batch level 2 identifier'
    )

    batch_level_3 = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='批次层级3',
        help_text='Batch level 3 identifier'
    )

    # Time tracking fields
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='创建时间',
        help_text='Order creation time'
    )

    confirmed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='认可时间',
        help_text='Order confirmation time'
    )

    shipped_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='发送时间',
        help_text='Shipment time'
    )

    # Delivery information
    estimated_website_arrival_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='官网到达预计时间',
        help_text='Estimated arrival date from website'
    )

    estimated_website_arrival_date_2 = models.DateField(
        null=True,
        blank=True,
        verbose_name='官网到达预计时间2',
        help_text='Second estimated arrival date from website'
    )

    tracking_number = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='邮寄单号',
        help_text='Shipping tracking number'
    )

    estimated_delivery_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='邮寄送达预计时间',
        help_text='Estimated delivery date'
    )

    # Status
    delivery_status = models.CharField(
        max_length=30,
        choices=DELIVERY_STATUS_CHOICES,
        default='pending_confirmation',
        verbose_name='送达状态',
        help_text='Delivery status'
    )
    latest_delivery_status = models.CharField(
        max_length=10,
        blank=True,
        null=True,
        verbose_name='最新送达状态',
        help_text='Latest delivery status in Japanese (max 10 characters)'
    )
    delivery_status_query_time = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='配送状态查询时间',
        help_text='Delivery status query time'
    )
    delivery_status_query_source = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name='配送状态查询来源',
        help_text='Delivery status query source'
    )

    # Additional delivery information
    official_query_url = models.URLField(
        max_length=500,
        blank=True,
        null=True,
        verbose_name='官方查询URL',
        help_text='Official query URL for order tracking'
    )

    shipping_method = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name='快递方式',
        help_text='Shipping method (e.g., Standard, Express, DHL, EMS, SF Express)'
    )

    # Update tracking
    last_info_updated_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='最后信息更新时间',
        help_text='Last information update time'
    )

    # Account and payment information
    account_used = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='使用账号',
        help_text='Account used for purchase'
    )

    payment_method = models.TextField(
        blank=True,
        verbose_name='使用付款方式',
        help_text='Payment method used or unmatched payment cards info'
    )

    # Metadata
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Updated At'
    )

    # Worker lock fields for data acquisition
    # Used to prevent concurrent modifications during Playwright-based data extraction
    # Lock timeout: 5 minutes (configurable in worker settings)
    # Expired locks are cleaned up daily (see scheduled task)
    is_locked = models.BooleanField(
        default=False,
        verbose_name='Is Locked',
        help_text='Whether this record is locked by a worker'
    )
    locked_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Locked At',
        help_text='Timestamp when the record was locked'
    )
    locked_by_worker = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='Locked By Worker',
        help_text='Name of the worker that locked this record'
    )

    is_deleted = models.BooleanField(
        default=False,
        verbose_name='Is Deleted',
        help_text='Soft delete flag'
    )

    creation_source = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name='创建来源',
        help_text='Source of order creation (e.g., API, manual import, auto sync)'
    )

    history = HistoricalRecordsWithSource()

    class Meta:
        db_table = 'purchasing'
        verbose_name = 'Purchasing Order'
        verbose_name_plural = 'Purchasing Orders'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['uuid']),
            models.Index(fields=['order_number']),
            models.Index(fields=['delivery_status']),
            models.Index(fields=['created_at']),
            models.Index(fields=['-shipped_at']),
            models.Index(fields=['tracking_number']),
            models.Index(fields=['is_locked']),
            models.Index(fields=['batch_encoding']),
        ]

    def __str__(self):
        return f"Order {self.order_number} - {self.get_delivery_status_display()}"

    @property
    def inventory_count(self):
        """
        Get the count of inventory items associated with this purchasing order.
        获取与此采购订单关联的库存数量。
        """
        return self.purchasing_inventories.count()

    def get_inventory_items(self):
        """
        Get all inventory items associated with this purchasing order.
        获取与此采购订单关联的所有库存项目。
        """
        return self.purchasing_inventories.all()

    def update_fields(self, **kwargs):
        """
        Update Purchasing instance fields with inventory updates.
        更新采购订单实例字段，并同步更新相关库存信息。

        Args:
            **kwargs: Keyword arguments for fields to update.
                     Special keys:
                     - email (str): Email to find and update OfficialAccount
                     - payment_cards (list): List of payment card dictionaries
                     - iphone_type_names (list): List of 1-2 iPhone type name strings
                     - estimated_website_arrival_date: Updates inventory checked_arrival_at_1
                     - estimated_delivery_date: Updates inventory checked_arrival_at_2

        Returns:
            bool: True if update succeeds

        Example:
            >>> purchasing.update_fields(
            ...     email='new@example.com',
            ...     delivery_status='shipped',
            ...     iphone_type_names=['iPhone 17 Pro Max 256GB コズミックオレンジ'],
            ...     estimated_website_arrival_date='2025-01-20'
            ... )
            True
        """
        from django.db import transaction
        import logging

        logger = logging.getLogger(__name__)

        with transaction.atomic():
            # Get caller information for conflict tracking
            caller_source = self._get_caller_info()

            # Extract special fields
            email = kwargs.pop('email', None)
            payment_cards = kwargs.pop('payment_cards', None)
            iphone_type_names = kwargs.pop('iphone_type_names', None)
            estimated_website_arrival_date = kwargs.pop('estimated_website_arrival_date', None)
            estimated_website_arrival_date_2 = kwargs.pop('estimated_website_arrival_date_2', None)
            estimated_delivery_date = kwargs.pop('estimated_delivery_date', None)

            # Extract OfficialAccount related fields (only processed if email is provided)
            name = kwargs.pop('name', None)
            postal_code = kwargs.pop('postal_code', None)
            address_line_1 = kwargs.pop('address_line_1', None)
            address_line_2 = kwargs.pop('address_line_2', None)

            # Conflict detection for official_account (via email)
            if email and self._is_valid_value(email):
                if self.official_account and self.official_account.email != email:
                    # Email conflict detected: record it and skip official_account update
                    self._record_field_conflict(
                        'official_account',
                        self.official_account.email,
                        email,
                        caller_source
                    )
                    logger.warning(
                        f"Purchasing {self.uuid}: Email conflict detected. "
                        f"Existing: {self.official_account.email}, Incoming: {email}. "
                        f"official_account and account_used will not be updated."
                    )
                    # Set email to None to skip the update logic below
                    email = None

            # Conflict detection for tracking_number
            if 'tracking_number' in kwargs:
                incoming_tracking = kwargs['tracking_number']
                if self._is_valid_value(incoming_tracking):
                    if self._is_valid_value(self.tracking_number) and self.tracking_number != incoming_tracking:
                        # Tracking number conflict detected
                        self._record_field_conflict(
                            'tracking_number',
                            self.tracking_number,
                            incoming_tracking,
                            caller_source
                        )
                        logger.warning(
                            f"Purchasing {self.uuid}: tracking_number conflict detected. "
                            f"Existing: {self.tracking_number}, Incoming: {incoming_tracking}. "
                            f"Field will not be updated."
                        )
                        # Remove from kwargs to prevent update
                        kwargs.pop('tracking_number')

            # Conflict detection for shipping_method
            if 'shipping_method' in kwargs:
                incoming_shipping = kwargs['shipping_method']
                if self._is_valid_value(incoming_shipping):
                    if self._is_valid_value(self.shipping_method) and self.shipping_method != incoming_shipping:
                        # Shipping method conflict detected
                        self._record_field_conflict(
                            'shipping_method',
                            self.shipping_method,
                            incoming_shipping,
                            caller_source
                        )
                        logger.warning(
                            f"Purchasing {self.uuid}: shipping_method conflict detected. "
                            f"Existing: {self.shipping_method}, Incoming: {incoming_shipping}. "
                            f"Field will not be updated."
                        )
                        # Remove from kwargs to prevent update
                        kwargs.pop('shipping_method')

            # Handle official_account update via email
            if email:
                official_account = Purchasing._find_or_create_official_account(
                    email=email,
                    name=name,
                    postal_code=postal_code,
                    address_line_1=address_line_1,
                    address_line_2=address_line_2
                )
                if official_account:
                    self.official_account = official_account
                # Always update account_used with email
                self.account_used = email

            # Handle payment cards
            if payment_cards:
                Purchasing._process_payment_cards(self, payment_cards)

            # Apply Tokyo timezone to date fields
            if estimated_website_arrival_date is not None:
                estimated_website_arrival_date = ensure_tokyo_timezone(estimated_website_arrival_date)
            if estimated_website_arrival_date_2 is not None:
                estimated_website_arrival_date_2 = ensure_tokyo_timezone(estimated_website_arrival_date_2)
            if estimated_delivery_date is not None:
                estimated_delivery_date = ensure_tokyo_timezone(estimated_delivery_date)

            # Handle iphone_type_names and inventory matching
            if iphone_type_names is not None:
                self._handle_iphone_type_names(
                    iphone_type_names,
                    estimated_website_arrival_date,
                    estimated_delivery_date,
                    logger
                )
            else:
                # Handle estimated_website_arrival_date and update inventory
                if estimated_website_arrival_date is not None:
                    self.estimated_website_arrival_date = estimated_website_arrival_date
                    self._update_inventory_checked_time(
                        'checked_arrival_at_1',
                        estimated_website_arrival_date
                    )

                # Handle estimated_delivery_date and update inventory
                if estimated_delivery_date is not None:
                    self.estimated_delivery_date = estimated_delivery_date
                    self._update_inventory_checked_time(
                        'checked_arrival_at_2',
                        estimated_delivery_date
                    )

            # Handle estimated_website_arrival_date_2 (no inventory update)
            if estimated_website_arrival_date_2 is not None:
                self.estimated_website_arrival_date_2 = estimated_website_arrival_date_2

            # Update remaining fields directly
            # Apply Tokyo timezone to datetime/date fields
            datetime_fields = ['confirmed_at', 'shipped_at', 'delivery_status_query_time', 'last_info_updated_at']
            for field, value in kwargs.items():
                if hasattr(self, field):
                    # Apply timezone conversion for datetime/date fields
                    if field in datetime_fields and value is not None:
                        value = ensure_tokyo_timezone(value)
                    setattr(self, field, value)

            # Save the instance
            self.save()

            return True

    def _update_inventory_checked_time(self, field_name, time_value):
        """
        Update specific time field for all associated inventory items.
        更新所有关联库存项目的指定时间字段。

        Args:
            field_name (str): Field name to update (checked_arrival_at_1 or checked_arrival_at_2)
            time_value: Time value to set
        """
        inventories = self.purchasing_inventories.all()
        for inventory in inventories:
            setattr(inventory, field_name, time_value)
            inventory.save(update_fields=[field_name])

    def _handle_iphone_type_names(self, iphone_type_names, estimated_website_arrival_date, estimated_delivery_date, logger):
        """
        Handle iphone_type_names parameter and match with existing inventories.
        处理iphone_type_names参数并与现有库存匹配。

        Args:
            iphone_type_names (list): List of 1-2 iPhone type name strings
            estimated_website_arrival_date: Website arrival date to update.
                Can be a single date value (applied to all inventories) or
                a list of date values (one per inventory, matching iphone_type_names order)
            estimated_delivery_date: Delivery date to update
            logger: Logger instance for error logging

        Logic:
            - Parse each iphone_type_name to get iPhone object
            - Match with existing inventories by order
            - If match: update time fields if provided
            - If mismatch: log error, skip time field updates
            - If inventory missing: create new inventory
            - If extra inventories exist: log error for them
        """
        # Validate input
        if not isinstance(iphone_type_names, list) or len(iphone_type_names) == 0 or len(iphone_type_names) > 2:
            logger.error(
                f"Purchasing {self.uuid}: Invalid iphone_type_names parameter - "
                f"must be a list with 1-2 elements, got {iphone_type_names}"
            )
            return

        # Normalize estimated_website_arrival_date to a list
        # If it's a single value, it will be used for all inventories
        # If it's a list, each value corresponds to an inventory
        arrival_dates = None
        if estimated_website_arrival_date is not None:
            if isinstance(estimated_website_arrival_date, list):
                arrival_dates = estimated_website_arrival_date
            else:
                # Single value - will be expanded when needed
                arrival_dates = [estimated_website_arrival_date] * len(iphone_type_names)

        # Parse iphone_type_names to get iPhone objects
        expected_iphones = []
        for iphone_type_name in iphone_type_names:
            try:
                iphone = Purchasing._find_iphone_by_type_name(iphone_type_name)
                if iphone is None:
                    logger.error(
                        f"Purchasing {self.uuid}: Failed to parse iphone_type_name '{iphone_type_name}' - "
                        f"returned None"
                    )
                    return
                expected_iphones.append(iphone)
            except ValueError as e:
                logger.error(
                    f"Purchasing {self.uuid}: Failed to parse iphone_type_name '{iphone_type_name}' - {str(e)}"
                )
                return

        # Get existing inventories ordered by creation time
        existing_inventories = list(self.purchasing_inventories.order_by('created_at'))
        existing_count = len(existing_inventories)
        expected_count = len(expected_iphones)

        # Update Purchasing time fields
        # For Purchasing model, use the first date if it's a list
        if arrival_dates is not None and len(arrival_dates) > 0:
            self.estimated_website_arrival_date = arrival_dates[0]
        if estimated_delivery_date is not None:
            self.estimated_delivery_date = estimated_delivery_date

        # Match and update inventories
        for i, expected_iphone in enumerate(expected_iphones):
            # Get the arrival date for this specific inventory
            inventory_arrival_date = arrival_dates[i] if arrival_dates and i < len(arrival_dates) else None

            if i < existing_count:
                # Inventory exists, check if it matches
                inventory = existing_inventories[i]
                actual_iphone = inventory.iphone

                if actual_iphone == expected_iphone:
                    # Match: update time fields
                    if inventory_arrival_date is not None:
                        inventory.checked_arrival_at_1 = inventory_arrival_date
                    if estimated_delivery_date is not None:
                        inventory.checked_arrival_at_2 = estimated_delivery_date

                    # Save only if there are changes
                    update_fields = []
                    if inventory_arrival_date is not None:
                        update_fields.append('checked_arrival_at_1')
                    if estimated_delivery_date is not None:
                        update_fields.append('checked_arrival_at_2')
                    if update_fields:
                        inventory.save(update_fields=update_fields)
                else:
                    # Mismatch: log error, skip time field updates
                    actual_name = self._format_iphone_name(actual_iphone) if actual_iphone else "None"
                    expected_name = self._format_iphone_name(expected_iphone)
                    logger.error(
                        f"Purchasing {self.uuid}: Inventory #{i+1} mismatch - "
                        f"expected iPhone '{expected_name}', but got '{actual_name}'. "
                        f"Time fields will not be updated for this inventory."
                    )
            else:
                # Inventory missing: create new inventory
                inventory_data = {
                    'source2': self,
                    'iphone': expected_iphone,
                    'status': 'planned'
                }
                if inventory_arrival_date is not None:
                    inventory_data['checked_arrival_at_1'] = inventory_arrival_date
                if estimated_delivery_date is not None:
                    inventory_data['checked_arrival_at_2'] = estimated_delivery_date

                Inventory.objects.create(**inventory_data)

                # Log error if this is due to type mismatch scenario
                if i == 1 and existing_count == 1:
                    # Scenario: 1 existing inventory (type different) + 1 new inventory
                    logger.error(
                        f"Purchasing {self.uuid}: Created new inventory for iPhone '{self._format_iphone_name(expected_iphone)}' "
                        f"while existing inventory has type mismatch."
                    )

        # Handle extra inventories
        if existing_count > expected_count:
            for i in range(expected_count, existing_count):
                inventory = existing_inventories[i]
                actual_iphone = inventory.iphone
                actual_name = self._format_iphone_name(actual_iphone) if actual_iphone else "None"
                logger.error(
                    f"Purchasing {self.uuid}: Extra inventory #{i+1} found (iPhone '{actual_name}'). "
                    f"Expected {expected_count} inventories but found {existing_count}. "
                    f"Time fields will not be updated for this inventory."
                )

    @staticmethod
    def _format_iphone_name(iphone):
        """
        Format iPhone object to a readable name string.
        将iPhone对象格式化为可读的名称字符串。

        Args:
            iphone (iPhone): iPhone object

        Returns:
            str: Formatted name (e.g., "iPhone 17 Pro Max 256GB コズミックオレンジ")
        """
        if iphone is None:
            return "None"
        return f"{iphone.model_name} {iphone.capacity_gb}GB {iphone.color}"

    @classmethod
    def create_with_inventory(cls, **kwargs):
        """
        Create a Purchasing order with associated inventory items.
        创建采购订单并自动创建关联的库存项目。

        Args:
            **kwargs: Keyword arguments for Purchasing fields.
                     Special keys:
                     - email (str): Email to find OfficialAccount
                     - inventory_count (int): Number of inventory items to create (optional)
                     - jan (str): JAN code to find and associate product (optional)
                     - iphone_type_name (str): iPhone type name to find and associate product (optional)
                     - iphone_type_names (list): List of iPhone type names for multiple different products (optional)
                     - estimated_website_arrival_date: Single date or list of dates for each inventory (optional)
                     - card_number_1 (str): First card number (optional)
                     - card_number_2 (str): Second card number (optional)
                     - card_number_3 (str): Third card number (optional)
                     - payment_amount_1 (Decimal): Payment amount for card 1 (optional, default: 0)
                     - payment_amount_2 (Decimal): Payment amount for card 2 (optional, default: 0)
                     - payment_amount_3 (Decimal): Payment amount for card 3 (optional, default: 0)
                     - payment_cards (list): Legacy payment cards format (optional)
                     - creation_source (str): Source of order creation (optional, max 200 chars)

        Returns:
            tuple: (purchasing_instance, [inventory_list])

        Example:
            >>> purchasing, inventories = Purchasing.create_with_inventory(
            ...     email='user@example.com',
            ...     inventory_count=3,
            ...     jan='4547597992388',
            ...     card_number_1='1234567890123456',
            ...     payment_amount_1=10000,
            ...     delivery_status='pending_confirmation'
            ... )

            # With multiple different products and dates:
            >>> purchasing, inventories = Purchasing.create_with_inventory(
            ...     email='user@example.com',
            ...     iphone_type_names=['iPhone 15 Pro 256GB ブラック', 'iPhone 15 Pro Max 512GB ホワイト'],
            ...     estimated_website_arrival_date=['2025-01-20', '2025-01-25']
            ... )
        """
        from django.db import transaction
        import logging

        logger = logging.getLogger(__name__)

        with transaction.atomic():
            # Automatically record caller information if creation_source is not provided
            if 'creation_source' not in kwargs:
                import sys
                f = sys._getframe(1)
                caller_name = f.f_code.co_name
                caller_info = caller_name
                if 'self' in f.f_locals:
                    class_name = f.f_locals['self'].__class__.__name__
                    caller_info = f"{class_name}.{caller_name}"
                elif 'cls' in f.f_locals:
                    try:
                        class_name = f.f_locals['cls'].__name__
                        caller_info = f"{class_name}.{caller_name}"
                    except:
                        pass
                kwargs['creation_source'] = caller_info

            # Parse kwargs for special keys
            (email, inventory_count, jan, iphone_type_name, iphone_type_names,
             estimated_website_arrival_date, card_data, payment_cards, purchasing_data) = cls._parse_kwargs(kwargs)

            # Apply Tokyo timezone to estimated_website_arrival_date
            if estimated_website_arrival_date is not None:
                if isinstance(estimated_website_arrival_date, list):
                    # Process each date in the list
                    estimated_website_arrival_date = [ensure_tokyo_timezone(d) for d in estimated_website_arrival_date]
                else:
                    # Process single date
                    estimated_website_arrival_date = ensure_tokyo_timezone(estimated_website_arrival_date)

            # Find official account by email
            official_account = cls._find_official_account(email)

            # Set official account and account_used fields
            if official_account:
                purchasing_data['official_account'] = official_account
            if email:
                purchasing_data['account_used'] = email

            # Handle multiple products (iphone_type_names) vs single product
            products_with_dates = None
            product = None
            product_type = None

            if iphone_type_names:
                # Multiple different products
                products_with_dates = []
                arrival_dates = None

                # Normalize estimated_website_arrival_date to a list
                # (already converted to Tokyo timezone above)
                if estimated_website_arrival_date is not None:
                    if isinstance(estimated_website_arrival_date, list):
                        arrival_dates = estimated_website_arrival_date
                    else:
                        arrival_dates = [estimated_website_arrival_date] * len(iphone_type_names)

                for i, type_name in enumerate(iphone_type_names):
                    try:
                        iphone = cls._find_iphone_by_type_name(type_name)
                        if iphone is None:
                            logger.error(f"create_with_inventory: Failed to find iPhone for '{type_name}'")
                            continue
                        arrival_date = arrival_dates[i] if arrival_dates and i < len(arrival_dates) else None
                        products_with_dates.append({
                            'product': iphone,
                            'product_type': 'iphone',
                            'arrival_date': arrival_date
                        })
                    except ValueError as e:
                        logger.error(f"create_with_inventory: Failed to parse iphone_type_name '{type_name}': {e}")
                        continue

                # Update inventory_count to match products
                inventory_count = len(products_with_dates)

                # Set Purchasing estimated_website_arrival_date to the first date
                if arrival_dates and len(arrival_dates) > 0:
                    purchasing_data['estimated_website_arrival_date'] = arrival_dates[0]

            else:
                # Single product type (original logic)
                if jan:
                    product, product_type = cls._find_product_by_jan(jan)
                elif iphone_type_name:
                    product = cls._find_iphone_by_type_name(iphone_type_name)
                    product_type = 'iphone'

            # Generate order_number if not provided
            if not purchasing_data.get('order_number'):
                purchasing_data['order_number'] = cls._generate_order_number()

            # Apply Tokyo timezone to datetime/date fields in purchasing_data
            datetime_fields = ['confirmed_at', 'shipped_at', 'estimated_website_arrival_date', 
                             'estimated_website_arrival_date_2', 'estimated_delivery_date',
                             'delivery_status_query_time', 'last_info_updated_at']
            for field in datetime_fields:
                if field in purchasing_data and purchasing_data[field] is not None:
                    purchasing_data[field] = ensure_tokyo_timezone(purchasing_data[field])

            # Create Purchasing instance
            purchasing_instance = cls.objects.create(**purchasing_data)

            # Create inventory items
            if products_with_dates:
                # Multiple different products with individual dates
                inventory_list = cls._create_inventory_items_with_products(
                    purchasing_instance,
                    products_with_dates
                )
            else:
                # Single product type (original logic)
                inventory_list = cls._create_inventory_items(
                    purchasing_instance,
                    inventory_count,
                    product=product,
                    product_type=product_type
                )

            # Process card payments (new format)
            if card_data:
                cls._process_card_payments(purchasing_instance, card_data)

            # Process payment cards (legacy format)
            if payment_cards:
                cls._process_payment_cards(purchasing_instance, payment_cards)

            return purchasing_instance, inventory_list

    @staticmethod
    def _parse_kwargs(kwargs):
        """
        Parse kwargs to extract special keys.
        解析kwargs，提取特殊参数。

        Args:
            kwargs (dict): Keyword arguments

        Returns:
            tuple: (email, inventory_count, jan, iphone_type_name, iphone_type_names,
                   estimated_website_arrival_date, card_data, payment_cards, remaining_kwargs)
        """
        email = kwargs.pop('email', None)
        inventory_count = kwargs.pop('inventory_count', None)
        jan = kwargs.pop('jan', None)
        iphone_type_name = kwargs.pop('iphone_type_name', None)
        iphone_type_names = kwargs.pop('iphone_type_names', None)
        estimated_website_arrival_date = kwargs.pop('estimated_website_arrival_date', None)
        payment_cards = kwargs.pop('payment_cards', None)

        # Extract card numbers and payment amounts
        card_data = []
        for i in range(1, 4):  # card_number_1, card_number_2, card_number_3
            card_number = kwargs.pop(f'card_number_{i}', None)
            payment_amount = kwargs.pop(f'payment_amount_{i}', None)

            if card_number:
                # TODO: Handle case where card_number is provided but payment_amount is not
                if payment_amount is None:
                    payment_amount = 0  # Default to 0
                card_data.append({
                    'card_number': card_number,
                    'payment_amount': payment_amount
                })
            elif payment_amount is not None:
                # TODO: Handle case where payment_amount is provided but card_number is not
                raise ValueError(f'payment_amount_{i} provided but card_number_{i} is missing')

        # Handle inventory_count logic
        # If iphone_type_names is provided, inventory_count will be determined by its length
        # If jan or iphone_type_name is provided but inventory_count is not, default to 1
        # If neither jan/iphone_type_name nor inventory_count is provided, set to 0 (no inventory)
        if inventory_count is None:
            if iphone_type_names:
                inventory_count = len(iphone_type_names)
            elif jan or iphone_type_name:
                inventory_count = 1
            else:
                inventory_count = 0

        return (email, inventory_count, jan, iphone_type_name, iphone_type_names,
                estimated_website_arrival_date, card_data, payment_cards, kwargs)

    @staticmethod
    def _find_iphone_by_type_name(iphone_type_name):
        """
        Find iPhone by a standard type name string.
        根据标准型号字符串查找iPhone。

        Args:
            iphone_type_name (str): Standard iPhone type name string
                Example: "iPhone 17 Pro Max 256GB コズミックオレンジ"

        Returns:
            iPhone: Matched iPhone instance

        Raises:
            ValueError: If parsing fails or no matching iPhone is found
        """
        import re
        import math

        # 处理 None、空值和 NaN
        if iphone_type_name is None:
            return None
        if isinstance(iphone_type_name, float) and math.isnan(iphone_type_name):
            return None
        if not isinstance(iphone_type_name, str):
            iphone_type_name = str(iphone_type_name)
        if not iphone_type_name.strip():
            return None

        pattern = r'^(?P<model>.+?)\s+(?P<capacity>\d+)\s*(?P<unit>TB|GB)\s+(?P<color>.+)$'
        match = re.match(pattern, iphone_type_name.strip())
        if not match:
            raise ValueError(f'Invalid iphone_type_name format: {iphone_type_name}')

        model_name = match.group('model').strip()
        capacity = int(match.group('capacity'))
        unit = match.group('unit').upper()
        color = match.group('color').strip()

        if unit == 'TB':
            capacity *= 1024

        try:
            return iPhone.objects.get(
                model_name=model_name,
                capacity_gb=capacity,
                color=color,
                is_deleted=False
            )
        except iPhone.DoesNotExist as exc:
            raise ValueError(
                f'iPhone not found for model_name={model_name}, capacity_gb={capacity}, color={color}'
            ) from exc
        except iPhone.MultipleObjectsReturned as exc:
            raise ValueError(
                f'Multiple iPhones found for model_name={model_name}, capacity_gb={capacity}, color={color}'
            ) from exc

    @staticmethod
    def _find_official_account(email):
        """
        Find OfficialAccount by email.
        根据email查找OfficialAccount。

        Args:
            email (str): Email address

        Returns:
            OfficialAccount or None: Matched account or None if not found
        """
        if not email:
            return None

        try:
            return OfficialAccount.objects.get(email=email)
        except OfficialAccount.DoesNotExist:
            return None

    @staticmethod
    def _find_or_create_official_account(email, name=None, postal_code=None, address_line_1=None, address_line_2=None):
        """
        Find or create OfficialAccount by email, and update related fields if provided.
        根据email查找或创建OfficialAccount，并更新相关字段（如果提供）。

        Args:
            email (str): Email address (required)
            name (str): Account holder name (optional)
            postal_code (str): Postal code (optional)
            address_line_1 (str): Address line 1 (optional)
            address_line_2 (str): Address line 2 (optional)

        Returns:
            OfficialAccount or None: OfficialAccount instance or None if email is not provided

        Behavior:
            - If OfficialAccount exists: update provided fields
            - If OfficialAccount does not exist: create new account with provided fields
            - account_id and passkey are set to email as default values for new accounts
        """
        if not email:
            return None

        try:
            # Try to find existing account
            official_account = OfficialAccount.objects.get(email=email)
            
            # Update fields if provided
            updated = False
            if name is not None:
                official_account.name = name
                updated = True
            if postal_code is not None:
                official_account.postal_code = postal_code
                updated = True
            if address_line_1 is not None:
                official_account.address_line_1 = address_line_1
                updated = True
            if address_line_2 is not None:
                official_account.address_line_2 = address_line_2
                updated = True
            
            if updated:
                official_account.save()
            
            return official_account
            
        except OfficialAccount.DoesNotExist:
            # Create new account with provided fields
            account_data = {
                'email': email,
                'account_id': email,  # Default to email
                'passkey': email,  # Default to email
            }
            
            if name is not None:
                account_data['name'] = name
            if postal_code is not None:
                account_data['postal_code'] = postal_code
            if address_line_1 is not None:
                account_data['address_line_1'] = address_line_1
            if address_line_2 is not None:
                account_data['address_line_2'] = address_line_2
            
            return OfficialAccount.objects.create(**account_data)

    @staticmethod
    def _find_product_by_jan(jan):
        """
        Find product (iPhone or iPad) by JAN code.
        根据JAN码查找产品（iPhone或iPad）。

        Args:
            jan (str): JAN code

        Returns:
            tuple: (product_instance, product_type) where product_type is 'iphone' or 'ipad'

        Raises:
            ValueError: If product not found
        """
        if not jan:
            return None, None

        # First try to find in iPhone
        try:
            product = iPhone.objects.get(jan=jan)
            return product, 'iphone'
        except iPhone.DoesNotExist:
            pass

        # Then try to find in iPad
        try:
            product = iPad.objects.get(jan=jan)
            return product, 'ipad'
        except iPad.DoesNotExist:
            pass

        # TODO: Add fallback logic for product not found
        raise ValueError(f'Product with JAN code {jan} not found in iPhone or iPad models')

    @staticmethod
    def _find_card_by_number(card_number):
        """
        Find payment card (GiftCard, DebitCard, or CreditCard) by card number.
        根据卡号查找支付卡（礼品卡、借记卡或信用卡）。

        Search order: GiftCard → DebitCard → CreditCard

        Args:
            card_number (str): Card number

        Returns:
            tuple: (card_instance, card_type) where card_type is 'gift', 'debit', or 'credit'

        Raises:
            ValueError: If card not found
        """
        if not card_number:
            return None, None

        # First try GiftCard
        try:
            card = GiftCard.objects.get(card_number=card_number)
            return card, 'gift'
        except GiftCard.DoesNotExist:
            pass

        # Then try DebitCard
        try:
            card = DebitCard.objects.get(card_number=card_number)
            return card, 'debit'
        except DebitCard.DoesNotExist:
            pass

        # Finally try CreditCard
        try:
            card = CreditCard.objects.get(card_number=card_number)
            return card, 'credit'
        except CreditCard.DoesNotExist:
            pass

        # TODO: Add fallback logic for card not found
        raise ValueError(f'Card with card_number {card_number} not found in GiftCard, DebitCard, or CreditCard models')

    @staticmethod
    def _generate_order_number():
        """
        Generate a unique order number.
        生成唯一订单号。

        Returns:
            str: Generated order number
        """
        from django.utils import timezone
        timestamp = timezone.now().strftime('%Y%m%d%H%M%S')
        random_suffix = generate_uuid().split('-')[0]  # Use first segment of UUID
        return f"ORD-{timestamp}-{random_suffix}"

    @staticmethod
    def _create_inventory_items(purchasing_instance, inventory_count, product=None, product_type=None):
        """
        Create inventory items associated with the purchasing order.
        创建与采购订单关联的库存项目。

        Args:
            purchasing_instance (Purchasing): Purchasing instance
            inventory_count (int): Number of inventory items to create
            product: Product instance (iPhone or iPad) to associate with inventory
            product_type (str): Type of product ('iphone' or 'ipad')

        Returns:
            list: List of created Inventory instances
        """
        inventory_list = []

        for _ in range(inventory_count):
            # Prepare inventory data
            inventory_data = {
                'source2': purchasing_instance,
                'status': 'planned'  # Default status for new inventory
            }

            # Associate product if provided
            if product and product_type:
                if product_type == 'iphone':
                    inventory_data['iphone'] = product
                elif product_type == 'ipad':
                    inventory_data['ipad'] = product

            # Create inventory
            inventory = Inventory.objects.create(**inventory_data)
            inventory_list.append(inventory)

        return inventory_list

    @staticmethod
    def _create_inventory_items_with_products(purchasing_instance, products_with_dates):
        """
        Create inventory items with different products and individual arrival dates.
        创建具有不同产品和各自到达日期的库存项目。

        Args:
            purchasing_instance (Purchasing): Purchasing instance
            products_with_dates (list): List of dicts with 'product', 'product_type', 'arrival_date'
                Example: [
                    {'product': iphone_obj_1, 'product_type': 'iphone', 'arrival_date': date(2025, 1, 20)},
                    {'product': iphone_obj_2, 'product_type': 'iphone', 'arrival_date': date(2025, 1, 25)},
                ]

        Returns:
            list: List of created Inventory instances
        """
        inventory_list = []

        for item in products_with_dates:
            product = item.get('product')
            product_type = item.get('product_type')
            arrival_date = item.get('arrival_date')

            # Prepare inventory data
            inventory_data = {
                'source2': purchasing_instance,
                'status': 'planned'
            }

            # Associate product if provided
            if product and product_type:
                if product_type == 'iphone':
                    inventory_data['iphone'] = product
                elif product_type == 'ipad':
                    inventory_data['ipad'] = product

            # Set arrival date if provided
            if arrival_date is not None:
                inventory_data['checked_arrival_at_1'] = arrival_date

            # Create inventory
            inventory = Inventory.objects.create(**inventory_data)
            inventory_list.append(inventory)

        return inventory_list

    @staticmethod
    def _process_payment_cards(purchasing_instance, payment_cards):
        """
        Process payment cards and create payment records.
        处理支付卡并创建支付记录。

        Args:
            purchasing_instance (Purchasing): Purchasing instance
            payment_cards (list): List of payment card dictionaries
                Format: [
                    {'method': 'gift_card', 'card_number': 'CARD123', 'amount': '100'},
                    {'method': 'gift_card', 'alternative_name': 'CARD-1-1', 'amount': '100'},
                    ...
                ]

        Returns:
            None (modifies purchasing_instance.payment_method for unmatched cards)
        """
        unmatched_cards = []

        for card_info in payment_cards:
            method = card_info.get('method', '').lower()
            card_number = card_info.get('card_number', '')
            alternative_name = card_info.get('alternative_name', '')
            amount = card_info.get('amount')

            # Convert amount to Decimal if provided
            if amount:
                from decimal import Decimal
                try:
                    amount = Decimal(str(amount))
                except (ValueError, TypeError):
                    amount = None

            matched = False

            # Try to find and link the card
            if method == 'gift_card':
                matched = Purchasing._link_gift_card(purchasing_instance, card_number, alternative_name, amount)
            elif method == 'credit_card':
                matched = Purchasing._link_credit_card(purchasing_instance, card_number, alternative_name, amount)
            elif method == 'debit_card':
                matched = Purchasing._link_debit_card(purchasing_instance, card_number, alternative_name, amount)
            else:
                # Unknown method, treat as unmatched
                matched = False

            # If not matched, add to unmatched list
            if not matched:
                identifier = card_number or alternative_name or 'unknown'
                unmatched_cards.append(f"({method}, {identifier})")

        # Update payment_method field with unmatched cards
        if unmatched_cards:
            purchasing_instance.payment_method = '|'.join(unmatched_cards)
            purchasing_instance.save(update_fields=['payment_method'])

    @staticmethod
    def _link_gift_card(purchasing_instance, card_number, alternative_name, amount):
        """
        Link a gift card to the purchasing order.
        关联礼品卡到采购订单。

        Args:
            purchasing_instance: Purchasing instance
            card_number (str): Card number for lookup
            alternative_name (str): Alternative name for lookup
            amount: Payment amount

        Returns:
            bool: True if card found and linked, False otherwise
        """
        try:
            # Try to find card by card_number first (if provided)
            if card_number:
                gift_card = GiftCard.objects.get(card_number=card_number)
            # Otherwise try to find by alternative_name
            elif alternative_name:
                gift_card = GiftCard.objects.get(alternative_name=alternative_name)
            else:
                return False

            GiftCardPayment.objects.create(
                gift_card=gift_card,
                purchasing=purchasing_instance,
                payment_amount=amount
            )
            return True
        except GiftCard.DoesNotExist:
            return False

    @staticmethod
    def _link_credit_card(purchasing_instance, card_number, alternative_name, amount):
        """
        Link a credit card to the purchasing order.
        关联信用卡到采购订单。

        Args:
            purchasing_instance: Purchasing instance
            card_number (str): Card number for lookup
            alternative_name (str): Alternative name for lookup
            amount: Payment amount

        Returns:
            bool: True if card found and linked, False otherwise
        """
        try:
            # Try to find card by card_number first (if provided)
            if card_number:
                credit_card = CreditCard.objects.get(card_number=card_number)
            # Otherwise try to find by alternative_name
            elif alternative_name:
                credit_card = CreditCard.objects.get(alternative_name=alternative_name)
            else:
                return False

            CreditCardPayment.objects.create(
                credit_card=credit_card,
                purchasing=purchasing_instance,
                payment_amount=amount
            )
            return True
        except CreditCard.DoesNotExist:
            return False

    @staticmethod
    def _link_debit_card(purchasing_instance, card_number, alternative_name, amount):
        """
        Link a debit card to the purchasing order.
        关联借记卡到采购订单。

        Args:
            purchasing_instance: Purchasing instance
            card_number (str): Card number for lookup
            alternative_name (str): Alternative name for lookup
            amount: Payment amount

        Returns:
            bool: True if card found and linked, False otherwise
        """
        try:
            # Try to find card by card_number first (if provided)
            if card_number:
                debit_card = DebitCard.objects.get(card_number=card_number)
            # Otherwise try to find by alternative_name
            elif alternative_name:
                debit_card = DebitCard.objects.get(alternative_name=alternative_name)
            else:
                return False

            DebitCardPayment.objects.create(
                debit_card=debit_card,
                purchasing=purchasing_instance,
                payment_amount=amount
            )
            return True
        except DebitCard.DoesNotExist:
            return False

    @staticmethod
    def _process_card_payments(purchasing_instance, card_data):
        """
        Process card payments using card numbers and amounts.
        使用卡号和金额处理卡支付。

        Args:
            purchasing_instance (Purchasing): Purchasing instance
            card_data (list): List of card payment dictionaries
                Format: [
                    {'card_number': '1234...', 'payment_amount': 100},
                    {'card_number': '5678...', 'payment_amount': 200},
                    ...
                ]

        Returns:
            None

        Raises:
            ValueError: If card not found
        """
        from decimal import Decimal

        for card_info in card_data:
            card_number = card_info.get('card_number')
            payment_amount = card_info.get('payment_amount', 0)

            # Convert payment_amount to Decimal
            if payment_amount is not None:
                try:
                    payment_amount = Decimal(str(payment_amount))
                except (ValueError, TypeError):
                    payment_amount = Decimal('0')
            else:
                payment_amount = Decimal('0')

            # Find the card
            card, card_type = Purchasing._find_card_by_number(card_number)

            # Create payment record based on card type
            if card_type == 'gift':
                GiftCardPayment.objects.create(
                    gift_card=card,
                    purchasing=purchasing_instance,
                    payment_amount=payment_amount,
                    payment_status='pending',
                    payment_time=None
                )
            elif card_type == 'debit':
                DebitCardPayment.objects.create(
                    debit_card=card,
                    purchasing=purchasing_instance,
                    payment_amount=payment_amount,
                    payment_status='pending',
                    payment_time=None
                )
            elif card_type == 'credit':
                CreditCardPayment.objects.create(
                    credit_card=card,
                    purchasing=purchasing_instance,
                    payment_amount=payment_amount,
                    payment_status='pending',
                    payment_time=None
                )

    def _is_valid_value(self, value):
        """
        Check if a value is valid (not None, not empty string, not whitespace-only).
        检查值是否有效（非None、非空字符串、非纯空格）。

        Args:
            value: Value to check

        Returns:
            bool: True if value is valid, False otherwise
        """
        if value is None:
            return False
        if isinstance(value, str):
            return value.strip() != ''
        return True

    def _get_caller_info(self):
        """
        Get caller information for conflict tracking.
        获取调用者信息用于冲突追踪。

        Returns:
            str: Caller information in format "ClassName.method_name" or "function_name"
        """
        import inspect
        
        frame = inspect.currentframe()
        try:
            # Skip _get_caller_info and update_fields frames
            caller_frame = frame.f_back.f_back
            if caller_frame is None:
                return 'unknown'
            
            function_name = caller_frame.f_code.co_name
            
            # Try to get class name if it's a method
            caller_locals = caller_frame.f_locals
            if 'self' in caller_locals:
                caller_instance = caller_locals['self']
                class_name = caller_instance.__class__.__name__
                return f"{class_name}.{function_name}"
            elif 'cls' in caller_locals:
                caller_class = caller_locals['cls']
                class_name = caller_class.__name__
                return f"{class_name}.{function_name}"
            else:
                # It's a regular function
                return function_name
        except Exception:
            return 'unknown'
        finally:
            del frame

    def _record_field_conflict(self, field_name, old_value, incoming_value, source):
        """
        Record field conflict to OrderConflict and OrderConflictField.
        记录字段冲突到OrderConflict和OrderConflictField。

        Args:
            field_name (str): Name of the conflicting field
            old_value: Existing value
            incoming_value: Incoming value that conflicts
            source (str): Source of the incoming data
        """
        from django.utils import timezone
        
        # Get or create OrderConflict for this purchasing order
        order_conflict, created = OrderConflict.objects.get_or_create(
            purchasing=self
        )
        
        # Create OrderConflictField record
        OrderConflictField.objects.create(
            order_conflict=order_conflict,
            field_name=field_name,
            old_value=str(old_value) if old_value is not None else '',
            incoming_value=str(incoming_value) if incoming_value is not None else '',
            source=source,
            detected_at=timezone.now()
        )


class OrderConflict(models.Model):
    """
    Order conflict model for tracking data conflicts in purchasing orders.
    订单信息冲突模型，用于跟踪采购订单数据冲突。
    """
    # Unique identifier
    uuid = models.CharField(
        max_length=59,
        unique=True,
        default=generate_uuid,
        verbose_name='UUID',
        help_text='48-character globally unique identifier'
    )

    # One-to-one relationship with Purchasing
    purchasing = models.OneToOneField(
        'Purchasing',
        on_delete=models.PROTECT,
        related_name='conflict',
        verbose_name='订单',
        help_text='The purchasing order associated with this conflict'
    )

    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='创建时间',
        help_text='When this conflict record was created'
    )

    # Status
    is_processed = models.BooleanField(
        default=False,
        verbose_name='已处理',
        help_text='Whether this conflict has been processed/resolved'
    )

    class Meta:
        db_table = 'order_conflict'
        verbose_name = 'Order Conflict'
        verbose_name_plural = 'Order Conflicts'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['uuid']),
            models.Index(fields=['is_processed']),
            models.Index(fields=['-created_at']),
        ]

    def __str__(self):
        return f"Conflict for Order {self.purchasing.order_number} - {'Processed' if self.is_processed else 'Pending'}"


class OrderConflictField(models.Model):
    """
    Order conflict field model for tracking individual field conflicts.
    订单冲突字段模型，用于跟踪具体字段的冲突信息。
    """
    # Unique identifier
    uuid = models.CharField(
        max_length=59,
        unique=True,
        default=generate_uuid,
        verbose_name='UUID',
        help_text='48-character globally unique identifier'
    )

    # Many-to-one relationship with OrderConflict
    order_conflict = models.ForeignKey(
        'OrderConflict',
        on_delete=models.CASCADE,
        related_name='conflict_fields',
        verbose_name='订单冲突',
        help_text='The order conflict this field belongs to'
    )

    # Field information
    field_name = models.CharField(
        max_length=100,
        verbose_name='冲突字段名',
        help_text='Name of the conflicting field (e.g., order_number, delivery_status)'
    )

    old_value = models.CharField(
        max_length=255,
        blank=True,
        verbose_name='旧字段值',
        help_text='The original/existing value of the field'
    )

    incoming_value = models.CharField(
        max_length=255,
        blank=True,
        verbose_name='传入字段值',
        help_text='The incoming/new value that conflicts with the existing value'
    )

    source = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='传入途径',
        help_text='Source of the incoming data (e.g., API, manual import, auto sync)'
    )

    # Timestamps
    detected_at = models.DateTimeField(
        verbose_name='冲突检测时间',
        help_text='When this field conflict was detected'
    )

    # Status
    is_processed = models.BooleanField(
        default=False,
        verbose_name='已处理',
        help_text='Whether this field conflict has been processed/resolved'
    )

    class Meta:
        db_table = 'order_conflict_field'
        verbose_name = 'Order Conflict Field'
        verbose_name_plural = 'Order Conflict Fields'
        ordering = ['-detected_at']
        indexes = [
            models.Index(fields=['uuid']),
            models.Index(fields=['field_name']),
            models.Index(fields=['is_processed']),
            models.Index(fields=['-detected_at']),
        ]

    def __str__(self):
        return f"{self.field_name}: '{self.old_value}' vs '{self.incoming_value}'"


class GiftCard(models.Model):
    """
    Gift card model for managing gift card information.
    礼品卡模型，用于管理礼品卡信息。
    """
    # Card information
    card_number = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='卡号',
        help_text='Gift card number (unique identifier)'
    )

    alternative_name = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name='别名',
        help_text='Human-friendly alternative name for easy management'
    )

    passkey1 = models.CharField(
        max_length=50,
        verbose_name='Passkey 1',
        help_text='First passkey for gift card authentication'
    )

    passkey2 = models.CharField(
        max_length=50,
        verbose_name='Passkey 2',
        help_text='Second passkey for gift card authentication'
    )

    balance = models.IntegerField(
        verbose_name='余额',
        help_text='Gift card balance amount'
    )

    batch_encoding = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='批次编号',
        help_text='Batch encoding for grouping related records'
    )

    # Many-to-many relationship with Purchasing through GiftCardPayment
    purchasings = models.ManyToManyField(
        'Purchasing',
        through='GiftCardPayment',
        related_name='gift_cards',
        blank=True,
        verbose_name='Purchasing Orders',
        help_text='Purchasing orders associated with this gift card'
    )

    # Metadata
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Created At',
        help_text='Record creation time'
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Updated At'
    )

    is_deleted = models.BooleanField(
        default=False,
        verbose_name='Is Deleted',
        help_text='Soft delete flag'
    )

    history = HistoricalRecordsWithSource()

    class Meta:
        db_table = 'gift_cards'
        verbose_name = 'Gift Card'
        verbose_name_plural = 'Gift Cards'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['card_number']),
            models.Index(fields=['-created_at']),
        ]

    def __str__(self):
        return f"{self.card_number} - Balance: {self.balance}"


class GiftCardPayment(models.Model):
    """
    Intermediate model for gift card payments on purchasing orders.
    礼品卡支付中间表模型，用于记录礼品卡在采购订单中的支付信息。
    """
    PAYMENT_STATUS_CHOICES = [
        ('pending', '待处理'),
        ('completed', '已完成'),
        ('failed', '失败'),
        ('refunded', '已退款'),
    ]

    gift_card = models.ForeignKey(
        'GiftCard',
        on_delete=models.SET_NULL,
        null=True,
        related_name='payments',
        verbose_name='Gift Card',
        help_text='Gift card used for this payment'
    )

    purchasing = models.ForeignKey(
        'Purchasing',
        on_delete=models.SET_NULL,
        null=True,
        related_name='gift_card_payments',
        verbose_name='Purchasing Order',
        help_text='Purchasing order for this payment'
    )

    payment_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='支付金额',
        help_text='Amount paid with this gift card'
    )

    payment_time = models.DateTimeField(
        auto_now_add=True,
        verbose_name='支付时间',
        help_text='Time when the payment was made'
    )

    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default='pending',
        verbose_name='支付状态',
        help_text='Status of the payment'
    )

    # Metadata
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Created At',
        help_text='Record creation time'
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Updated At'
    )

    is_deleted = models.BooleanField(
        default=False,
        verbose_name='Is Deleted',
        help_text='Soft delete flag'
    )

    history = HistoricalRecordsWithSource()

    class Meta:
        db_table = 'gift_card_payments'
        verbose_name = 'Gift Card Payment'
        verbose_name_plural = 'Gift Card Payments'
        ordering = ['-payment_time']
        indexes = [
            models.Index(fields=['payment_status']),
            models.Index(fields=['-payment_time']),
        ]

    def __str__(self):
        card_info = self.gift_card.card_number if self.gift_card else 'N/A'
        order_info = self.purchasing.order_number if self.purchasing else 'N/A'
        return f"{card_info} -> Order {order_info}: {self.payment_amount}"


class DebitCard(models.Model):
    """
    Debit card model for managing debit card information.
    借记卡模型，用于管理借记卡信息。
    """
    # Card information
    card_number = models.CharField(
        max_length=19,
        unique=True,
        verbose_name='卡号',
        help_text='Debit card number (unique identifier)'
    )

    alternative_name = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name='别名',
        help_text='Human-friendly alternative name for easy management'
    )

    expiry_month = models.IntegerField(
        verbose_name='有效期月份',
        help_text='Card expiry month (1-12)',
        validators=[
            MinValueValidator(1),
            MaxValueValidator(12)
        ]
    )

    expiry_year = models.IntegerField(
        verbose_name='有效期年份',
        help_text='Card expiry year (e.g., 2025)',
        validators=[
            MinValueValidator(2000)
        ]
    )

    passkey = models.CharField(
        max_length=128,
        verbose_name='Passkey',
        help_text='Passkey for debit card authentication'
    )

    last_balance_update = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='最近更新余额时间',
        help_text='Last time the balance was updated'
    )

    balance = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name='余额',
        help_text='Debit card balance amount'
    )

    batch_encoding = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='批次编号',
        help_text='Batch encoding for grouping related records'
    )

    # Many-to-many relationship with Purchasing through DebitCardPayment
    purchasings = models.ManyToManyField(
        'Purchasing',
        through='DebitCardPayment',
        related_name='debit_cards',
        blank=True,
        verbose_name='Purchasing Orders',
        help_text='Purchasing orders associated with this debit card'
    )

    # Metadata
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Created At',
        help_text='Record creation time'
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Updated At'
    )

    is_deleted = models.BooleanField(
        default=False,
        verbose_name='Is Deleted',
        help_text='Soft delete flag'
    )

    history = HistoricalRecordsWithSource()

    class Meta:
        db_table = 'debit_cards'
        verbose_name = 'Debit Card'
        verbose_name_plural = 'Debit Cards'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['card_number']),
            models.Index(fields=['-created_at']),
            models.Index(fields=['last_balance_update']),
        ]

    def __str__(self):
        return f"{self.card_number} - Balance: {self.balance}"


class DebitCardPayment(models.Model):
    """
    Intermediate model for debit card payments on purchasing orders.
    借记卡支付中间表模型，用于记录借记卡在采购订单中的支付信息。
    """
    PAYMENT_STATUS_CHOICES = [
        ('pending', '待处理'),
        ('completed', '已完成'),
        ('failed', '失败'),
        ('refunded', '已退款'),
    ]

    debit_card = models.ForeignKey(
        'DebitCard',
        on_delete=models.SET_NULL,
        null=True,
        related_name='payments',
        verbose_name='Debit Card',
        help_text='Debit card used for this payment'
    )

    purchasing = models.ForeignKey(
        'Purchasing',
        on_delete=models.SET_NULL,
        null=True,
        related_name='debit_card_payments',
        verbose_name='Purchasing Order',
        help_text='Purchasing order for this payment'
    )

    payment_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name='支付金额',
        help_text='Amount paid with this debit card'
    )

    payment_time = models.DateTimeField(
        auto_now_add=True,
        verbose_name='支付时间',
        help_text='Time when the payment was made'
    )

    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default='pending',
        verbose_name='支付状态',
        help_text='Status of the payment'
    )

    # Metadata
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Created At',
        help_text='Record creation time'
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Updated At'
    )

    is_deleted = models.BooleanField(
        default=False,
        verbose_name='Is Deleted',
        help_text='Soft delete flag'
    )

    history = HistoricalRecordsWithSource()

    class Meta:
        db_table = 'debit_card_payments'
        verbose_name = 'Debit Card Payment'
        verbose_name_plural = 'Debit Card Payments'
        ordering = ['-payment_time']
        indexes = [
            models.Index(fields=['payment_status']),
            models.Index(fields=['-payment_time']),
        ]

    def __str__(self):
        card_info = self.debit_card.card_number if self.debit_card else 'N/A'
        order_info = self.purchasing.order_number if self.purchasing else 'N/A'
        return f"{card_info} -> Order {order_info}: {self.payment_amount}"


class CreditCard(models.Model):
    """
    Credit card model for managing credit card information.
    信用卡模型，用于管理信用卡信息。
    """
    # Card information
    card_number = models.CharField(
        max_length=19,
        unique=True,
        verbose_name='卡号',
        help_text='Credit card number (unique identifier)'
    )

    alternative_name = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name='别名',
        help_text='Human-friendly alternative name for easy management'
    )

    expiry_month = models.IntegerField(
        verbose_name='有效期月份',
        help_text='Card expiry month (1-12)',
        validators=[
            MinValueValidator(1),
            MaxValueValidator(12)
        ]
    )

    expiry_year = models.IntegerField(
        verbose_name='有效期年份',
        help_text='Card expiry year (e.g., 2025)',
        validators=[
            MinValueValidator(2000)
        ]
    )

    passkey = models.CharField(
        max_length=128,
        verbose_name='Passkey',
        help_text='Passkey for credit card authentication'
    )

    last_balance_update = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='最近更新余额时间',
        help_text='Last time the balance was updated'
    )

    credit_limit = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name='额度',
        help_text='Credit card limit amount'
    )

    batch_encoding = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='批次编号',
        help_text='Batch encoding for grouping related records'
    )

    # Many-to-many relationship with Purchasing through CreditCardPayment
    purchasings = models.ManyToManyField(
        'Purchasing',
        through='CreditCardPayment',
        related_name='credit_cards',
        blank=True,
        verbose_name='Purchasing Orders',
        help_text='Purchasing orders associated with this credit card'
    )

    # Metadata
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Created At',
        help_text='Record creation time'
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Updated At'
    )

    is_deleted = models.BooleanField(
        default=False,
        verbose_name='Is Deleted',
        help_text='Soft delete flag'
    )

    history = HistoricalRecordsWithSource()

    class Meta:
        db_table = 'credit_cards'
        verbose_name = 'Credit Card'
        verbose_name_plural = 'Credit Cards'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['card_number']),
            models.Index(fields=['-created_at']),
            models.Index(fields=['last_balance_update']),
        ]

    def __str__(self):
        return f"{self.card_number} - Limit: {self.credit_limit}"


class CreditCardPayment(models.Model):
    """
    Intermediate model for credit card payments on purchasing orders.
    信用卡支付中间表模型，用于记录信用卡在采购订单中的支付信息。
    """
    PAYMENT_STATUS_CHOICES = [
        ('pending', '待处理'),
        ('completed', '已完成'),
        ('failed', '失败'),
        ('refunded', '已退款'),
    ]

    credit_card = models.ForeignKey(
        'CreditCard',
        on_delete=models.SET_NULL,
        null=True,
        related_name='payments',
        verbose_name='Credit Card',
        help_text='Credit card used for this payment'
    )

    purchasing = models.ForeignKey(
        'Purchasing',
        on_delete=models.SET_NULL,
        null=True,
        related_name='credit_card_payments',
        verbose_name='Purchasing Order',
        help_text='Purchasing order for this payment'
    )

    payment_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name='支付金额',
        help_text='Amount paid with this credit card'
    )

    payment_time = models.DateTimeField(
        auto_now_add=True,
        verbose_name='支付时间',
        help_text='Time when the payment was made'
    )

    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default='pending',
        verbose_name='支付状态',
        help_text='Status of the payment'
    )

    # Metadata
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Created At',
        help_text='Record creation time'
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Updated At'
    )

    is_deleted = models.BooleanField(
        default=False,
        verbose_name='Is Deleted',
        help_text='Soft delete flag'
    )

    history = HistoricalRecordsWithSource()

    class Meta:
        db_table = 'credit_card_payments'
        verbose_name = 'Credit Card Payment'
        verbose_name_plural = 'Credit Card Payments'
        ordering = ['-payment_time']
        indexes = [
            models.Index(fields=['payment_status']),
            models.Index(fields=['-payment_time']),
        ]

    def __str__(self):
        card_info = self.credit_card.card_number if self.credit_card else 'N/A'
        order_info = self.purchasing.order_number if self.purchasing else 'N/A'
        return f"{card_info} -> Order {order_info}: {self.payment_amount}"


class OtherPayment(models.Model):
    """
    Model for other payment methods not covered by specific card models.
    其他支付方式模型，用于记录非特定卡类型的支付信息。
    """
    PAYMENT_STATUS_CHOICES = [
        ('pending', '待处理'),
        ('completed', '已完成'),
        ('failed', '失败'),
        ('refunded', '已退款'),
    ]

    purchasing = models.ForeignKey(
        'Purchasing',
        on_delete=models.SET_NULL,
        null=True,
        related_name='other_payments',
        verbose_name='Purchasing Order',
        help_text='Purchasing order for this payment'
    )

    payment_info = models.TextField(
        verbose_name='支付信息',
        help_text='Payment information including method and card details'
    )

    payment_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='支付金额',
        help_text='Payment amount'
    )

    payment_time = models.DateTimeField(
        auto_now_add=True,
        verbose_name='支付时间',
        help_text='Time when the payment was made'
    )

    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default='pending',
        verbose_name='支付状态',
        help_text='Status of the payment'
    )

    # Metadata
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Created At',
        help_text='Record creation time'
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Updated At'
    )

    history = HistoricalRecordsWithSource()

    class Meta:
        db_table = 'other_payments'
        verbose_name = 'Other Payment'
        verbose_name_plural = 'Other Payments'
        ordering = ['-payment_time']
        indexes = [
            models.Index(fields=['payment_status']),
            models.Index(fields=['-payment_time']),
        ]

    def __str__(self):
        order_info = self.purchasing.order_number if self.purchasing else 'N/A'
        return f"Other Payment -> Order {order_info}: {self.payment_amount}"


class HistoricalData(models.Model):
    """
    Historical data model for tracking instance counts of models under specific conditions.
    历史数据模型，用于记录各模型符合特定条件的实例数的历史记录。

    This is a generic table designed for high compatibility and extensibility.
    The slug field uses conventions defined by the creating task.
    """
    model = models.CharField(
        max_length=100,
        verbose_name='Model Name',
        help_text='Name of the model being tracked'
    )

    slug = models.CharField(
        max_length=255,
        verbose_name='Condition Slug',
        help_text='Condition identifier, written by the creating task using agreed conventions'
    )

    value = models.IntegerField(
        verbose_name='Value',
        help_text='Count of instances matching the condition'
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Created At',
        help_text='Record creation time (auto-generated)'
    )

    history = HistoricalRecordsWithSource()

    class Meta:
        db_table = 'historical_data'
        verbose_name = 'Historical Data'
        verbose_name_plural = 'Historical Data'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['model']),
            models.Index(fields=['slug']),
            models.Index(fields=['model', 'slug']),
            models.Index(fields=['-created_at']),
        ]

    def __str__(self):
        return f"{self.model}:{self.slug} = {self.value} ({self.created_at.strftime('%Y-%m-%d %H:%M')})"


from django.db import models
from django.utils import timezone


class MailAccount(models.Model):
    """
    邮箱账号/数据来源（MVP）。
    """
    PROVIDER_GMAIL = "gmail"
    PROVIDER_IMAP = "imap"
    PROVIDER_CHOICES = [
        (PROVIDER_GMAIL, "Gmail"),
        (PROVIDER_IMAP, "IMAP"),
    ]

    provider = models.CharField(max_length=32, choices=PROVIDER_CHOICES, default=PROVIDER_GMAIL)
    email_address = models.EmailField(unique=True)

    # 与 OfficialAccount 的一对一关联
    official_account = models.OneToOneField(
        'OfficialAccount',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='mail_account',
        verbose_name='关联官方账号',
        help_text='Associated official account'
    )

    # Gmail 增量同步游标（可选，未来你做 historyId 同步会用到）
    last_history_id = models.CharField(max_length=64, blank=True, default="")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"{self.provider}:{self.email_address}"

    def link_or_create_official_account(self):
        """
        根据邮箱地址查找或创建 OfficialAccount 并建立关联。

        如果已经有关联的 OfficialAccount，则不做任何操作。
        如果存在相同邮箱的 OfficialAccount，则建立关联。
        如果不存在，则创建新的 OfficialAccount 并建立关联。

        Returns:
            OfficialAccount: 关联的 OfficialAccount 实例
        """
        # 如果已经有关联，直接返回
        if self.official_account:
            return self.official_account

        # 尝试查找相同邮箱的 OfficialAccount
        try:
            official_account = OfficialAccount.objects.get(email=self.email_address)
            self.official_account = official_account
            self.save(update_fields=['official_account'])
            return official_account
        except OfficialAccount.DoesNotExist:
            # 创建新的 OfficialAccount
            # account_id 使用邮箱前缀，name 留空（现在允许为空）
            email_prefix = self.email_address.split('@')[0]
            official_account = OfficialAccount.objects.create(
                email=self.email_address,
                account_id=email_prefix,
                name=''  # 名称留空，之后可以手动补充
            )
            self.official_account = official_account
            self.save(update_fields=['official_account'])
            return official_account





class MailThread(models.Model):
    """
    会话线程（Thread）。如果你暂时不需要线程维度，可以先不建这张表，
    仅在 MailMessage 存 provider_thread_id 即可；但建了更利于聚合检索。
    """
    account = models.ForeignKey(MailAccount, on_delete=models.CASCADE, related_name="threads")
    provider_thread_id = models.CharField(max_length=128)  # Gmail threadId

    subject_norm = models.CharField(max_length=512, blank=True, default="")
    last_message_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["account", "provider_thread_id"],
                name="uniq_thread_per_account",
            )
        ]
        indexes = [
            models.Index(fields=["account", "last_message_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.account.email_address}::{self.provider_thread_id}"


class MailLabel(models.Model):
    """
    Gmail label / 系统标签 / 自定义标签。
    """
    account = models.ForeignKey(MailAccount, on_delete=models.CASCADE, related_name="labels")
    provider_label_id = models.CharField(max_length=128)  # e.g. INBOX, UNREAD, Label_1
    name = models.CharField(max_length=255, blank=True, default="")
    is_system = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["account", "provider_label_id"],
                name="uniq_label_per_account",
            )
        ]
        indexes = [
            models.Index(fields=["account", "provider_label_id"]),
            models.Index(fields=["account", "name"]),
        ]

    def __str__(self) -> str:
        return f"{self.account.email_address}:{self.provider_label_id}"


class MailMessage(models.Model):
    """
    邮件主表：你最关心的 subject/date/from/to 的结构化检索字段放这里。
    正文 html/text 放到 MailMessageBody（一对一）。
    """
    account = models.ForeignKey(MailAccount, on_delete=models.CASCADE, related_name="messages")

    # Gmail: id / threadId / RFC Message-ID
    provider_message_id = models.CharField(max_length=128)  # Gmail message id: "19bc..."
    provider_thread_id = models.CharField(max_length=128, blank=True, default="")  # Gmail threadId
    thread = models.ForeignKey(
        MailThread,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="messages",
    )
    rfc_message_id = models.CharField(max_length=255, blank=True, default="")  # headers["message-id"] 或解析字段 messageId

    # 你关心的 date（建议同时存发件方 Date 与 Gmail internalDate，便于排序/对账）
    date_header_at = models.DateTimeField(null=True, blank=True)   # headers["date"] 解析后的时间（UTC）
    internal_at = models.DateTimeField(null=True, blank=True)      # Gmail internalDate（UTC），如果你拿得到

    # 你关心的 subject
    subject = models.TextField(blank=True, default="")

    # 可选：snippet / 大小 / 是否有附件
    snippet = models.TextField(blank=True, default="")
    size_estimate = models.PositiveIntegerField(default=0)
    has_attachments = models.BooleanField(default=False)

    # 你关心的 from / to：MVP 先存“规范化字段 + 原始结构”
    from_address = models.EmailField(blank=True, default="")
    from_name = models.CharField(max_length=255, blank=True, default="")
    sender_domain = models.CharField(max_length=255, blank=True, default="")

    # to 通常是多值：用 JSON 存 [{address,name}, ...] 最贴合你 n8n 输出
    to_recipients = models.JSONField(default=list, blank=True)  # [{"address": "...", "name": "..."}, ...]
    to_text = models.TextField(blank=True, default="")          # n8n 的 to.text（便于展示/简单搜索）

    # 原始 headers：建议保留，未来你要解析 ARC/SPF/DKIM/Received 链路时非常有用
    raw_headers = models.JSONField(default=dict, blank=True)

    # 状态字段
    ingested_at = models.DateTimeField(default=timezone.now)
    is_extracted = models.BooleanField(default=False)  # 是否已提取信息（用于业务管理）

    labels = models.ManyToManyField(
        MailLabel,
        through="MailMessageLabel",
        related_name="messages",
        blank=True,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["account", "provider_message_id"],
                name="uniq_message_per_account",
            )
        ]
        indexes = [
            models.Index(fields=["account", "-date_header_at"]),
            models.Index(fields=["account", "-internal_at"]),
            models.Index(fields=["account", "from_address"]),
            models.Index(fields=["account", "sender_domain"]),
            models.Index(fields=["account", "provider_thread_id"]),
        ]

    def save(self, *args, **kwargs):
        # 维护 sender_domain，便于按域过滤
        if self.from_address and "@" in self.from_address:
            self.sender_domain = self.from_address.split("@", 1)[1].lower()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"[{self.account.email_address}] {self.subject[:80]}"

    @property
    def primary_to_address(self) -> str:
        """
        便于快速取第一个收件人（常用于 UI/默认归类）。
        """
        if isinstance(self.to_recipients, list) and self.to_recipients:
            addr = (self.to_recipients[0] or {}).get("address") or ""
            return addr
        return ""


class MailMessageBody(models.Model):
    """
    正文表：承接你最关心的 html / text。
    """
    message = models.OneToOneField(MailMessage, on_delete=models.CASCADE, related_name="body")

    text_plain = models.TextField(blank=True, default="")  # n8n 的 text
    text_html = models.TextField(blank=True, default="")   # n8n 的 html
    text_as_html = models.TextField(blank=True, default="")  # n8n 的 textAsHtml（可选）

    # 可选：你可把 html -> 纯文本清洗后的版本放这里，用于全文检索/向量化
    text_normalized = models.TextField(blank=True, default="")

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"Body<{self.message_id}>"


class MailMessageLabel(models.Model):
    """
    邮件-标签 关联表（through）。
    """
    message = models.ForeignKey(MailMessage, on_delete=models.CASCADE)
    label = models.ForeignKey(MailLabel, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["message", "label"],
                name="uniq_message_label",
            )
        ]
        indexes = [
            models.Index(fields=["label", "message"]),
            models.Index(fields=["message", "label"]),
        ]


class MailAttachment(models.Model):
    """
    附件元数据（MVP 可选）。建议二进制文件本体不要直接入库，
    只存 storage_key（本地路径/MinIO/S3 key）。
    """
    message = models.ForeignKey(MailMessage, on_delete=models.CASCADE, related_name="attachments")

    provider_attachment_id = models.CharField(max_length=255, blank=True, default="")  # Gmail attachmentId
    filename = models.CharField(max_length=512, blank=True, default="")
    mime_type = models.CharField(max_length=255, blank=True, default="")
    size_bytes = models.PositiveIntegerField(default=0)

    storage_key = models.CharField(max_length=1024, blank=True, default="")  # 路径或对象存储 key
    sha256 = models.CharField(max_length=64, blank=True, default="")

    is_inline = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["message"]),
            models.Index(fields=["mime_type"]),
            models.Index(fields=["sha256"]),
        ]
