"""
Record selector and locking utilities for Purchasing model.

Provides thread-safe record selection and locking for worker tasks.
Lock timeout: 5 minutes (configurable via LOCK_TIMEOUT_MINUTES)
Expired locks are cleaned up daily.
"""

import logging
from datetime import timedelta
from typing import Optional

from django.db import transaction
from django.db.models import Q
from django.utils import timezone

logger = logging.getLogger(__name__)

# Lock timeout in minutes - records locked longer than this are considered expired
# TODO: Move to settings or environment variable if needed
LOCK_TIMEOUT_MINUTES = 5


def is_field_empty(field_value) -> bool:
    """
    Check if a field value is considered empty.

    Handles both None and empty string cases for CharField fields.

    Args:
        field_value: The field value to check

    Returns:
        True if the field is None or empty string, False otherwise
    """
    return field_value is None or field_value == ''


def get_lock_expired_threshold() -> timezone.datetime:
    """
    Get the timestamp threshold for expired locks.

    Returns:
        Datetime before which locks are considered expired
    """
    return timezone.now() - timedelta(minutes=LOCK_TIMEOUT_MINUTES)


def acquire_record_for_worker(
    worker_name: str,
    filter_condition: Q,
) -> Optional['Purchasing']:
    """
    Acquire and lock a single Purchasing record for processing.

    This function:
    1. Finds an unlocked record matching the filter condition
    2. Locks it atomically using select_for_update
    3. Returns the locked record or None if no matching record found

    Args:
        worker_name: Name of the worker acquiring the lock
        filter_condition: Django Q object for filtering records

    Returns:
        Locked Purchasing instance or None
    """
    from apps.data_aggregation.models import Purchasing

    expired_threshold = get_lock_expired_threshold()

    with transaction.atomic():
        # Find an unlocked record or one with an expired lock
        # Order by created_at ascending (oldest first)
        record = (
            Purchasing.objects
            .filter(filter_condition)
            .filter(
                Q(is_locked=False) |
                Q(is_locked=True, locked_at__lt=expired_threshold)
            )
            .select_for_update(skip_locked=True)
            .order_by('created_at')
            .first()
        )

        if record is None:
            logger.debug(f"[{worker_name}] No matching unlocked record found")
            return None

        # Lock the record
        record.is_locked = True
        record.locked_at = timezone.now()
        record.locked_by_worker = worker_name
        record.save(update_fields=['is_locked', 'locked_at', 'locked_by_worker'])

        logger.info(
            f"[{worker_name}] Acquired lock on Purchasing record "
            f"id={record.id}, order_number={record.order_number}"
        )

        return record


def release_record_lock(record: 'Purchasing', worker_name: str) -> bool:
    """
    Release the lock on a Purchasing record.

    Args:
        record: The Purchasing record to unlock
        worker_name: Name of the worker releasing the lock

    Returns:
        True if lock was released, False if record wasn't locked by this worker
    """
    from apps.data_aggregation.models import Purchasing

    with transaction.atomic():
        # Refresh the record to get current state
        current = Purchasing.objects.select_for_update().get(pk=record.pk)

        if current.locked_by_worker != worker_name:
            logger.warning(
                f"[{worker_name}] Cannot release lock on record id={record.id}, "
                f"locked by different worker: {current.locked_by_worker}"
            )
            return False

        current.is_locked = False
        current.locked_at = None
        current.locked_by_worker = ''
        current.save(update_fields=['is_locked', 'locked_at', 'locked_by_worker'])

        logger.info(
            f"[{worker_name}] Released lock on Purchasing record "
            f"id={record.id}, order_number={record.order_number}"
        )

        return True


def cleanup_expired_locks() -> int:
    """
    Clean up expired locks on Purchasing records.

    This should be run periodically (e.g., daily via Celery Beat).

    Returns:
        Number of expired locks cleaned up
    """
    from apps.data_aggregation.models import Purchasing

    expired_threshold = get_lock_expired_threshold()

    updated_count = (
        Purchasing.objects
        .filter(is_locked=True, locked_at__lt=expired_threshold)
        .update(is_locked=False, locked_at=None, locked_by_worker='')
    )

    if updated_count > 0:
        logger.info(f"Cleaned up {updated_count} expired locks")

    return updated_count


# =============================================================================
# Filter conditions for each worker type
# =============================================================================

def get_confirmed_at_empty_filter() -> Q:
    """
    Filter for confirmed_at_empty worker.

    Condition: confirmed_at is empty AND shipped_at, estimated_website_arrival_date,
    tracking_number, estimated_delivery_date are all empty.
    """
    return Q(
        confirmed_at__isnull=True,
        shipped_at__isnull=True,
        estimated_website_arrival_date__isnull=True,
        estimated_delivery_date__isnull=True,
    ) & (Q(tracking_number__isnull=True) | Q(tracking_number='') | Q(tracking_number='nan'))


def get_shipped_at_empty_filter() -> Q:
    """
    Filter for shipped_at_empty worker.

    Condition: shipped_at is empty AND estimated_website_arrival_date, tracking_number,
    estimated_delivery_date are all empty, BUT confirmed_at is NOT empty.
    """
    return Q(
        confirmed_at__isnull=False,
        shipped_at__isnull=True,
        estimated_website_arrival_date__isnull=True,
        estimated_delivery_date__isnull=True,
    ) & (Q(tracking_number__isnull=True) | Q(tracking_number='') | Q(tracking_number='nan'))


def get_estimated_website_arrival_date_empty_filter() -> Q:
    """
    Filter for estimated_website_arrival_date_empty worker.

    Condition: estimated_website_arrival_date is empty AND tracking_number,
    estimated_delivery_date are all empty, BUT shipped_at, confirmed_at are NOT empty.
    """
    return Q(
        confirmed_at__isnull=False,
        shipped_at__isnull=False,
        estimated_website_arrival_date__isnull=True,
        estimated_delivery_date__isnull=True,
    ) & (Q(tracking_number__isnull=True) | Q(tracking_number='') | Q(tracking_number='nan'))


def get_tracking_number_empty_filter() -> Q:
    """
    Filter for tracking_number_empty worker.

    Condition: tracking_number is empty AND estimated_delivery_date is empty,
    BUT shipped_at, confirmed_at, estimated_website_arrival_date are NOT empty.
    """
    return Q(
        confirmed_at__isnull=False,
        shipped_at__isnull=False,
        estimated_website_arrival_date__isnull=False,
        estimated_delivery_date__isnull=True,
    ) & (Q(tracking_number__isnull=True) | Q(tracking_number='') | Q(tracking_number='nan'))


def get_temporary_flexible_capture_filter() -> Q:
    """
    Filter for temporary_flexible_capture worker.

    Condition: Any record that does NOT match conditions 1-4.
    This excludes records where all fields are empty (those belong to confirmed_at_empty).

    Logic: NOT (condition1 OR condition2 OR condition3 OR condition4)
    AND NOT (all fields empty - which is condition1)

    Note: Former Worker 5 (estimated_delivery_date_empty) has been replaced by
    JapanPostTracking10TrackingNumberWorker which uses different selection criteria
    (order_number starts with 'w', tracking_number starts with '1').
    Records that don't match the new criteria are now handled by this worker.
    """
    # Combine all other conditions
    all_other_conditions = (
        get_confirmed_at_empty_filter() |
        get_shipped_at_empty_filter() |
        get_estimated_website_arrival_date_empty_filter() |
        get_tracking_number_empty_filter()
    )

    # Return records that don't match any of the above
    return ~all_other_conditions
