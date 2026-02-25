"""
Workers package for data acquisition.

Contains Playwright-based workers for automated data extraction from Purchasing records.
Each worker targets records with specific empty field combinations.

Workers:
- ConfirmedAtEmptyWorker: Records with all fields empty
- ShippedAtEmptyWorker: Records with confirmed_at set, others empty
- EstimatedWebsiteArrivalDateEmptyWorker: Records with confirmed_at, shipped_at set
- TrackingNumberEmptyWorker: Records with estimated_website_arrival_date set
- JapanPostTracking10TrackingNumberWorker: Japan Post tracking queries (order_number starts with 'w')
- TemporaryFlexibleCaptureWorker: Flexible filter conditions (dynamic OR filters)

Each worker uses:
- Dedicated Redis DB for isolation (DB 2-7)
- Single-threaded operation (concurrency=1)
- Record locking to prevent concurrent modifications
"""

from .base import BasePlaywrightWorker
from .record_selector import (
    acquire_record_for_worker,
    release_record_lock,
    cleanup_expired_locks,
    LOCK_TIMEOUT_MINUTES,
)
from .confirmed_at_empty import ConfirmedAtEmptyWorker
from .shipped_at_empty import ShippedAtEmptyWorker
from .estimated_website_arrival_date_empty import EstimatedWebsiteArrivalDateEmptyWorker
from .tracking_number_empty import TrackingNumberEmptyWorker
from .japan_post_tracking_10_tracking_number import JapanPostTracking10TrackingNumberWorker
from .temporary_flexible_capture import (
    TemporaryFlexibleCaptureWorker,
    FIELD_MAPPING,
    DATE_ONLY_FIELDS,
    TEXT_FIELDS,
)

__all__ = [
    # Base class
    'BasePlaywrightWorker',

    # Record selection utilities
    'acquire_record_for_worker',
    'release_record_lock',
    'cleanup_expired_locks',
    'LOCK_TIMEOUT_MINUTES',

    # Workers
    'ConfirmedAtEmptyWorker',
    'ShippedAtEmptyWorker',
    'EstimatedWebsiteArrivalDateEmptyWorker',
    'TrackingNumberEmptyWorker',
    'JapanPostTracking10TrackingNumberWorker',
    'TemporaryFlexibleCaptureWorker',

    # TemporaryFlexibleCaptureWorker constants
    'FIELD_MAPPING',
    'DATE_ONLY_FIELDS',
    'TEXT_FIELDS',
]
