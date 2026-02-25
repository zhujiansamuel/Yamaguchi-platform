"""
Worker for processing Initial Order Confirmation Emails.

Queue: initial_order_confirmation_email_queue
Redis DB: 10

This worker:
1. Receives email data from email_content_analysis
2. Queries the corresponding Purchasing record by order_number
3. If found: Updates the record using update_fields()
4. If not found: Creates a new record using create_with_inventory(), then updates OfficialAccount fields
"""

import logging
import re
from datetime import datetime, date
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)


def _parse_date_string(date_str: Optional[str]) -> Optional[date]:
    """
    Convert date string to date object.
    支持的格式: YYYY/MM/DD, YYYY-MM-DD

    Args:
        date_str: Date string in YYYY/MM/DD or YYYY-MM-DD format

    Returns:
        date object or None if parsing fails
    """
    if not date_str:
        return None

    # Try YYYY/MM/DD format
    try:
        return datetime.strptime(date_str, '%Y/%m/%d').date()
    except (ValueError, TypeError):
        pass

    # Try YYYY-MM-DD format
    try:
        return datetime.strptime(date_str, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        pass

    logger.warning(f"Failed to parse date string: {date_str}")
    return None


def _parse_datetime_string(date_str: Optional[str]) -> Optional[datetime]:
    """
    Convert date string to datetime object (for confirmed_at field).
    支持的格式: YYYY/MM/DD, YYYY-MM-DD

    Args:
        date_str: Date string in YYYY/MM/DD or YYYY-MM-DD format

    Returns:
        datetime object (at midnight) or None if parsing fails
    """
    date_obj = _parse_date_string(date_str)
    if date_obj:
        return datetime.combine(date_obj, datetime.min.time())
    return None


def _normalize_iphone_type_name(product_name: Optional[str]) -> Optional[str]:
    """
    Normalize iPhone product name to match _find_iphone_by_type_name expected format.
    期望格式: "{model_name} {capacity}GB {color}" 或 "{model_name} {capacity}TB {color}"

    Args:
        product_name: Product name from email (e.g., "iPhone 15 Pro Max 256GB ナチュラルチタニウム")

    Returns:
        Normalized product name or None if invalid
    """
    if not product_name:
        return None

    # Remove extra whitespace
    product_name = ' '.join(product_name.split()).strip()

    # Check if the format is already correct (matches the expected pattern)
    # Pattern: {model} {capacity}{unit} {color}
    pattern = r'^(.+?)\s+(\d+)\s*(TB|GB)\s+(.+)$'
    match = re.match(pattern, product_name, re.IGNORECASE)

    if match:
        model = match.group(1).strip()
        capacity = match.group(2)
        unit = match.group(3).upper()
        color = match.group(4).strip()
        return f"{model} {capacity}{unit} {color}"

    # If no match, return original (let _find_iphone_by_type_name handle the error)
    logger.warning(f"Product name may not match expected format: {product_name}")
    return product_name


def _extract_iphone_type_names_from_line_items(line_items: Optional[List[Dict]]) -> List[str]:
    """
    Extract iPhone type names from line_items list.

    Args:
        line_items: List of line item dictionaries with product_name and quantity

    Returns:
        List of iPhone type names (expanded by quantity)
    """
    if not line_items:
        return []

    iphone_type_names = []
    for item in line_items:
        product_name = item.get('product_name')
        if not product_name:
            continue

        normalized_name = _normalize_iphone_type_name(product_name)
        if not normalized_name:
            continue

        # Expand by quantity
        quantity = item.get('quantity', 1) or 1
        for _ in range(quantity):
            iphone_type_names.append(normalized_name)

    return iphone_type_names


def _extract_line_items_with_dates(line_items: Optional[List[Dict]]) -> Dict[str, Any]:
    """
    Extract iPhone type names and their corresponding arrival dates from line_items.

    Args:
        line_items: List of line item dictionaries with product_name, quantity, and delivery info

    Returns:
        Dictionary with:
        - 'iphone_type_names': List of iPhone type names (expanded by quantity)
        - 'arrival_dates': List of arrival dates corresponding to each iPhone
        - 'all_dates_same': Boolean indicating if all dates are the same
        - 'single_date': The common date if all_dates_same is True, else None
    """
    if not line_items:
        return {
            'iphone_type_names': [],
            'arrival_dates': [],
            'all_dates_same': True,
            'single_date': None
        }

    iphone_type_names = []
    arrival_dates = []

    for item in line_items:
        product_name = item.get('product_name')
        if not product_name:
            continue

        normalized_name = _normalize_iphone_type_name(product_name)
        if not normalized_name:
            continue

        # Extract delivery date for this item
        delivery = item.get('delivery')
        item_date = None
        if delivery:
            if delivery.get('type') == 'range':
                # Use start_date for range type
                item_date = _parse_date_string(delivery.get('start_date'))
            else:
                # Use date for single type
                item_date = _parse_date_string(delivery.get('date'))

        # Expand by quantity
        quantity = item.get('quantity', 1) or 1
        for _ in range(quantity):
            iphone_type_names.append(normalized_name)
            arrival_dates.append(item_date)

    # Determine if all dates are the same
    unique_dates = set(arrival_dates)
    all_dates_same = len(unique_dates) <= 1
    single_date = arrival_dates[0] if all_dates_same and arrival_dates else None

    return {
        'iphone_type_names': iphone_type_names,
        'arrival_dates': arrival_dates,
        'all_dates_same': all_dates_same,
        'single_date': single_date
    }


class InitialOrderConfirmationEmailWorker:
    """
    Worker for processing initial order confirmation emails.

    This worker updates Purchasing records based on initial order
    confirmation email content.
    """

    QUEUE_NAME = 'initial_order_confirmation_email_queue'
    WORKER_NAME = 'initial_order_confirmation_email_worker'

    def __init__(self):
        """Initialize the initial order confirmation email worker."""
        pass

    def find_purchasing_record(self, order_number: str) -> Optional['Purchasing']:
        """
        Find the Purchasing record by order_number.

        Args:
            order_number: Order number to search for

        Returns:
            Purchasing instance or None if not found
        """
        from apps.data_aggregation.models import Purchasing

        if not order_number:
            return None

        try:
            return Purchasing.objects.get(order_number=order_number, is_deleted=False)
        except Purchasing.DoesNotExist:
            logger.info(f"[{self.WORKER_NAME}] Purchasing record not found for order_number={order_number}")
            return None
        except Purchasing.MultipleObjectsReturned:
            logger.error(
                f"[{self.WORKER_NAME}] Multiple Purchasing records found for order_number={order_number}"
            )
            # Return the first one (oldest by created_at)
            return Purchasing.objects.filter(
                order_number=order_number, is_deleted=False
            ).order_by('created_at').first()

    def acquire_record_lock(self, record: 'Purchasing') -> bool:
        """
        Acquire lock on the Purchasing record.

        Args:
            record: Purchasing record to lock

        Returns:
            True if lock acquired successfully
        """
        from apps.data_acquisition.workers.record_selector import acquire_record_for_worker
        from django.db.models import Q

        # Use the shared locking mechanism
        # Create a filter for this specific record
        filter_condition = Q(id=record.id)

        locked_record = acquire_record_for_worker(self.WORKER_NAME, filter_condition)

        return locked_record is not None

    def release_record_lock(self, record: 'Purchasing') -> bool:
        """
        Release the lock on a Purchasing record.

        Args:
            record: The record to release

        Returns:
            True if lock was released successfully
        """
        from apps.data_acquisition.workers.record_selector import release_record_lock

        return release_record_lock(record, self.WORKER_NAME)

    def _prepare_update_fields_kwargs(self, email_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prepare keyword arguments for update_fields() method.

        Args:
            email_data: Email data dictionary

        Returns:
            Dictionary of keyword arguments for update_fields()
        """
        kwargs = {}

        # Email and OfficialAccount related fields
        if email_data.get('email'):
            kwargs['email'] = email_data['email']
        if email_data.get('name'):
            kwargs['name'] = email_data['name']
        if email_data.get('postal_code'):
            kwargs['postal_code'] = email_data['postal_code']
        if email_data.get('address_line_1'):
            kwargs['address_line_1'] = email_data['address_line_1']
        if email_data.get('address_line_2'):
            kwargs['address_line_2'] = email_data['address_line_2']

        # Purchasing fields
        if email_data.get('official_query_url'):
            kwargs['official_query_url'] = email_data['official_query_url']

        # confirmed_at (convert to datetime)
        confirmed_at = _parse_datetime_string(email_data.get('confirmed_at'))
        if confirmed_at:
            kwargs['confirmed_at'] = confirmed_at

        # estimated_website_arrival_date_2 (convert to date) - for Purchasing field only
        estimated_date_2 = _parse_date_string(email_data.get('estimated_website_arrival_date_2'))
        if estimated_date_2:
            kwargs['estimated_website_arrival_date_2'] = estimated_date_2

        # iphone_type_names and arrival_dates from line_items
        line_items = email_data.get('line_items')
        if line_items:
            # Extract with dates for smarter handling
            extracted = _extract_line_items_with_dates(line_items)
            iphone_type_names = extracted['iphone_type_names']

            if iphone_type_names:
                # Limit to 2 items as per update_fields specification
                kwargs['iphone_type_names'] = iphone_type_names[:2]

                # Handle arrival dates based on whether they are all the same
                if extracted['all_dates_same']:
                    # All dates are the same - use single date
                    if extracted['single_date']:
                        kwargs['estimated_website_arrival_date'] = extracted['single_date']
                else:
                    # Dates are different - pass as list (limited to match iphone_type_names)
                    arrival_dates = extracted['arrival_dates'][:2]
                    # Filter out None values but keep position correspondence
                    if any(d is not None for d in arrival_dates):
                        kwargs['estimated_website_arrival_date'] = arrival_dates
        else:
            # Fallback to backward compatible fields
            iphone_product_name = email_data.get('iphone_product_names')
            if iphone_product_name:
                normalized_name = _normalize_iphone_type_name(iphone_product_name)
                if normalized_name:
                    kwargs['iphone_type_names'] = [normalized_name]

            # Use top-level estimated_website_arrival_date
            estimated_date_1 = _parse_date_string(email_data.get('estimated_website_arrival_date'))
            if estimated_date_1:
                kwargs['estimated_website_arrival_date'] = estimated_date_1

        return kwargs

    def _update_existing_purchasing(self, purchasing: 'Purchasing', email_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an existing Purchasing record.

        Args:
            purchasing: Existing Purchasing instance
            email_data: Email data dictionary

        Returns:
            Result dictionary
        """
        logger.info(
            f"[{self.WORKER_NAME}] Updating existing Purchasing record "
            f"id={purchasing.id}, order_number={purchasing.order_number}"
        )

        kwargs = self._prepare_update_fields_kwargs(email_data)

        if not kwargs:
            logger.warning(f"[{self.WORKER_NAME}] No fields to update for order_number={purchasing.order_number}")
            return {
                'status': 'no_update',
                'message': 'No fields to update',
                'order_number': purchasing.order_number,
                'purchasing_id': purchasing.id,
            }

        try:
            purchasing.update_fields(**kwargs)
            logger.info(
                f"[{self.WORKER_NAME}] Successfully updated Purchasing record "
                f"id={purchasing.id}, fields={list(kwargs.keys())}"
            )
            # Success indicator
            logger.info(f"[{self.WORKER_NAME}] ===== UPDATE SUCCESS =====")
            logger.info(f"[{self.WORKER_NAME}]   Order Number: {purchasing.order_number}")
            logger.info(f"[{self.WORKER_NAME}]   Purchasing ID: {purchasing.id}")
            logger.info(f"[{self.WORKER_NAME}]   Updated Fields: {list(kwargs.keys())}")
            logger.info(f"[{self.WORKER_NAME}] ==========================")
            return {
                'status': 'updated',
                'message': 'Purchasing record updated successfully',
                'order_number': purchasing.order_number,
                'purchasing_id': purchasing.id,
                'updated_fields': list(kwargs.keys()),
            }
        except Exception as e:
            logger.error(
                f"[{self.WORKER_NAME}] Failed to update Purchasing record id={purchasing.id}: {e}",
                exc_info=True
            )
            raise

    def _create_new_purchasing(self, email_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new Purchasing record with inventory.

        Args:
            email_data: Email data dictionary

        Returns:
            Result dictionary
        """
        from apps.data_aggregation.models import Purchasing

        order_number = email_data.get('order_number')
        logger.info(f"[{self.WORKER_NAME}] Creating new Purchasing record for order_number={order_number}")

        # Prepare create_with_inventory kwargs
        create_kwargs = {
            'order_number': order_number,
            'creation_source': 'Initial Order Confirmation Email',
        }

        # Email for OfficialAccount lookup
        if email_data.get('email'):
            create_kwargs['email'] = email_data['email']

        # official_query_url
        if email_data.get('official_query_url'):
            create_kwargs['official_query_url'] = email_data['official_query_url']

        # confirmed_at (convert to datetime)
        confirmed_at = _parse_datetime_string(email_data.get('confirmed_at'))
        if confirmed_at:
            create_kwargs['confirmed_at'] = confirmed_at

        # estimated_website_arrival_date_2 (convert to date) - for Purchasing field only
        estimated_date_2 = _parse_date_string(email_data.get('estimated_website_arrival_date_2'))
        if estimated_date_2:
            create_kwargs['estimated_website_arrival_date_2'] = estimated_date_2

        # Determine iphone_type_names and arrival_dates from line_items
        line_items = email_data.get('line_items')
        if line_items:
            # Extract with dates for smarter handling
            extracted = _extract_line_items_with_dates(line_items)
            iphone_type_names = extracted['iphone_type_names']

            if iphone_type_names:
                # Use iphone_type_names (list) for create_with_inventory
                create_kwargs['iphone_type_names'] = iphone_type_names

                # Handle arrival dates based on whether they are all the same
                if extracted['all_dates_same']:
                    # All dates are the same - use single date
                    if extracted['single_date']:
                        create_kwargs['estimated_website_arrival_date'] = extracted['single_date']
                else:
                    # Dates are different - pass as list
                    arrival_dates = extracted['arrival_dates']
                    if any(d is not None for d in arrival_dates):
                        create_kwargs['estimated_website_arrival_date'] = arrival_dates
        else:
            # Fallback to backward compatible fields
            iphone_product_name = email_data.get('iphone_product_names')
            if iphone_product_name:
                normalized_name = _normalize_iphone_type_name(iphone_product_name)
                if normalized_name:
                    create_kwargs['iphone_type_name'] = normalized_name

            quantities = email_data.get('quantities')
            if quantities:
                try:
                    create_kwargs['inventory_count'] = int(quantities)
                except (ValueError, TypeError):
                    create_kwargs['inventory_count'] = 1

            # Use top-level estimated_website_arrival_date for fallback
            estimated_date_1 = _parse_date_string(email_data.get('estimated_website_arrival_date'))
            if estimated_date_1:
                create_kwargs['estimated_website_arrival_date'] = estimated_date_1

        try:
            # Create purchasing with inventory
            purchasing, inventories = Purchasing.create_with_inventory(**create_kwargs)

            logger.info(
                f"[{self.WORKER_NAME}] Created Purchasing record id={purchasing.id}, "
                f"order_number={purchasing.order_number}, inventory_count={len(inventories)}"
            )

            # Now update OfficialAccount fields using update_fields
            # (create_with_inventory doesn't support name, postal_code, address_line_1, address_line_2)
            update_kwargs = {}
            if email_data.get('email'):
                update_kwargs['email'] = email_data['email']
            if email_data.get('name'):
                update_kwargs['name'] = email_data['name']
            if email_data.get('postal_code'):
                update_kwargs['postal_code'] = email_data['postal_code']
            if email_data.get('address_line_1'):
                update_kwargs['address_line_1'] = email_data['address_line_1']
            if email_data.get('address_line_2'):
                update_kwargs['address_line_2'] = email_data['address_line_2']

            if update_kwargs:
                purchasing.update_fields(**update_kwargs)
                logger.info(
                    f"[{self.WORKER_NAME}] Updated OfficialAccount fields for Purchasing id={purchasing.id}"
                )

            # Success indicator
            logger.info(f"[{self.WORKER_NAME}] ===== CREATE SUCCESS =====")
            logger.info(f"[{self.WORKER_NAME}]   Order Number: {purchasing.order_number}")
            logger.info(f"[{self.WORKER_NAME}]   Purchasing ID: {purchasing.id}")
            logger.info(f"[{self.WORKER_NAME}]   Inventory Count: {len(inventories)}")
            logger.info(f"[{self.WORKER_NAME}] ==========================")

            return {
                'status': 'created',
                'message': 'Purchasing record created successfully',
                'order_number': purchasing.order_number,
                'purchasing_id': purchasing.id,
                'inventory_count': len(inventories),
            }

        except Exception as e:
            logger.error(
                f"[{self.WORKER_NAME}] Failed to create Purchasing record for order_number={order_number}: {e}",
                exc_info=True
            )
            raise

    def execute(self, task_data: dict) -> dict:
        """
        Execute the initial order confirmation email processing.

        Processing logic:
        1. Extract email_data from task_data
        2. Validate order_number (skip if empty)
        3. Find Purchasing record by order_number
        4. If found: Update using update_fields()
        5. If not found: Create using create_with_inventory(), then update OfficialAccount fields

        Args:
            task_data: Dictionary containing task parameters (including email_data)

        Returns:
            Dictionary containing execution results
        """
        email_data = task_data.get('email_data', {})

        if not email_data:
            logger.warning(f"[{self.WORKER_NAME}] No email_data provided")
            return {
                'status': 'no_data',
                'message': 'No email data provided',
            }

        # Log received email data
        separator = "=" * 60
        logger.info(f"[{self.WORKER_NAME}] {separator}")
        logger.info(f"[{self.WORKER_NAME}] PROCESSING EMAIL DATA - Initial Order Confirmation")
        logger.info(f"[{self.WORKER_NAME}] {separator}")

        for key, value in email_data.items():
            if isinstance(value, (list, dict)):
                value_str = str(value)[:100] + '...' if len(str(value)) > 100 else str(value)
            else:
                value_str = str(value)
            logger.info(f"[{self.WORKER_NAME}]   {key}: {value_str}")

        logger.info(f"[{self.WORKER_NAME}] {separator}")

        # Step 1: Validate order_number
        order_number = email_data.get('order_number')
        if not order_number:
            logger.error(f"[{self.WORKER_NAME}] order_number is empty, skipping processing")
            return {
                'status': 'skip',
                'message': 'order_number is empty, cannot process email',
                'email_id': email_data.get('email_id'),
            }

        # Step 2: Find existing Purchasing record
        purchasing = self.find_purchasing_record(order_number)

        # Step 3: Update or Create
        if purchasing:
            # Update existing record
            result = self._update_existing_purchasing(purchasing, email_data)
        else:
            # Create new record
            result = self._create_new_purchasing(email_data)

        # Add email_id to result
        result['email_id'] = email_data.get('email_id')

        logger.info(f"[{self.WORKER_NAME}] Processing completed: {result}")
        return result

    def run(self, task_data: dict) -> dict:
        """
        Run the worker with proper error handling.

        Args:
            task_data: Dictionary containing task parameters

        Returns:
            Dictionary containing execution results
        """
        try:
            logger.info(f"[{self.WORKER_NAME}] Starting task")
            result = self.execute(task_data)
            logger.info(f"[{self.WORKER_NAME}] Task completed successfully")
            return {
                'status': 'success',
                'result': result,
            }
        except Exception as e:
            logger.error(f"[{self.WORKER_NAME}] Task failed: {e}", exc_info=True)
            return {
                'status': 'error',
                'error': str(e),
            }
