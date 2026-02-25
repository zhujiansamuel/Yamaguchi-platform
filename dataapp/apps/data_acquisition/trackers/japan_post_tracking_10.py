"""
Japan Post Tracking 10 tracker for processing webhook data and updating database.

This module handles:
1. Reading DataFrame from webhook results
2. Extracting tracking information
3. Updating Purchasing records with delivery status
"""

import logging
import re
import pandas as pd
import numpy as np
from typing import List, Dict, Optional
from datetime import datetime
from django.utils import timezone
import pytz

logger = logging.getLogger(__name__)


def parse_japanese_datetime(datetime_str: str) -> Optional[datetime]:
    """
    Parse Japanese datetime string to datetime object.

    Supported formats:
    - "2026/01/09 10:37"
    - "2026/01/09 10:37:25"
    - "2026-01-09 10:37"
    - "2026-01-09 10:37:25"

    Args:
        datetime_str: DateTime string to parse

    Returns:
        datetime object with Tokyo timezone, or None if parsing fails
    """
    if not datetime_str:
        return None

    datetime_str = str(datetime_str).strip()

    if not datetime_str:
        return None

    # Try different formats
    formats = [
        '%Y/%m/%d %H:%M:%S',
        '%Y/%m/%d %H:%M',
        '%Y-%m-%d %H:%M:%S',
        '%Y-%m-%d %H:%M',
    ]

    for fmt in formats:
        try:
            dt = datetime.strptime(datetime_str, fmt)
            # Localize to Tokyo timezone
            tokyo_tz = pytz.timezone('Asia/Tokyo')
            if dt.tzinfo is None:
                dt = tokyo_tz.localize(dt)
            return dt
        except ValueError:
            continue

    logger.warning(f"Failed to parse datetime string: {datetime_str}")
    return None


def extract_tracking_data(df: pd.DataFrame) -> List[Dict]:
    """
    Extract tracking data from Japan Post DataFrame.

    Args:
        df: DataFrame containing tracking data from WebScraper

    Returns:
        List of dictionaries containing tracking information
    """
    # Filter rows with tracking numbers matching pattern XXXX-XXXX-XXXX
    pattern = r'^\d{4}-\d{4}-\d{4}$'
    mask = df['お問い合わせ番号'].astype(str).str.match(pattern)
    df_filtered = df[mask].copy()

    # Map columns to English names
    column_mapping = {
        'お問い合わせ番号': 'tracking_number',
        '最新年月日': 'delivery_status_query_time',
        '最新状態': 'latest_delivery_status',
        'time-scraped': 'last_info_updated_at'
    }

    df_result = df_filtered[list(column_mapping.keys())].rename(columns=column_mapping)

    def clean_text(text):
        """Clean text by removing extra whitespace and newlines."""
        if pd.isna(text) or text is None:
            return None
        if isinstance(text, float) and np.isnan(text):
            return None
        return re.sub(r'\s+', ' ', str(text).replace('\n', ' ')).strip()

    # Clean delivery_status_query_time field
    if 'delivery_status_query_time' in df_result.columns:
        df_result['delivery_status_query_time'] = df_result['delivery_status_query_time'].apply(clean_text)

    result_list = df_result.to_dict(orient='records')

    logger.info(f"Extracted {len(result_list)} tracking records from DataFrame")

    return result_list


def update_purchasing_records(tracking_data: List[Dict]) -> Dict[str, int]:
    """
    Update Purchasing records with tracking data.

    Args:
        tracking_data: List of tracking information dictionaries

    Returns:
        Dictionary with update statistics
    """
    from apps.data_aggregation.models import Purchasing

    updated_count = 0
    not_found_count = 0
    error_count = 0

    for item in tracking_data:
        try:
            # Extract tracking number and convert to 12-digit format
            # Example: 1837-9316-7924 -> 183793167924
            tracking_number = item.get('tracking_number', '')
            digits_only = re.sub(r'\D', '', tracking_number)

            if not digits_only or len(digits_only) != 12:
                logger.warning(f"Invalid tracking number format: {tracking_number}")
                error_count += 1
                continue

            # Query Purchasing records with matching tracking number
            purchasing_records = Purchasing.objects.filter(
                tracking_number__icontains=digits_only
            )

            # Alternative: extract digits from database tracking_number and compare
            matched_records = []
            for record in purchasing_records:
                record_digits = re.sub(r'\D', '', record.tracking_number or '')
                if record_digits == digits_only:
                    matched_records.append(record)

            if not matched_records:
                logger.warning(f"No Purchasing record found for tracking number: {tracking_number}")
                not_found_count += 1
                continue

            # Update each matched record
            for record in matched_records:
                # Parse delivery_status_query_time from string to datetime
                delivery_status_query_time_str = item.get('delivery_status_query_time')
                delivery_status_query_time = parse_japanese_datetime(delivery_status_query_time_str)

                # Update fields
                record.delivery_status_query_time = delivery_status_query_time
                record.latest_delivery_status = item.get('latest_delivery_status')
                record.last_info_updated_at = timezone.now()
                record.delivery_status_query_source = 'japan_post_tracking_10'

                # Save with update_fields for efficiency
                record.save(update_fields=[
                    'delivery_status_query_time',
                    'latest_delivery_status',
                    'last_info_updated_at',
                    'delivery_status_query_source'
                ])

                updated_count += 1
                logger.info(
                    f"Updated Purchasing {record.id} (order: {record.order_number}) "
                    f"with tracking {tracking_number}: {item.get('latest_delivery_status')} "
                    f"(query_time: {delivery_status_query_time})"
                )

        except Exception as exc:
            logger.error(
                f"Error updating record for tracking {item.get('tracking_number')}: {exc}",
                exc_info=True
            )
            error_count += 1

    return {
        'updated': updated_count,
        'not_found': not_found_count,
        'errors': error_count,
        'total_processed': len(tracking_data)
    }


def japan_post_tracking_10(df: pd.DataFrame) -> str:
    """
    Japan Post Tracking 10 data parser and processor.

    This function:
    1. Extracts tracking data from the DataFrame
    2. Updates Purchasing records with delivery status
    3. Returns processing summary

    Args:
        df: DataFrame containing tracking data from WebScraper

    Returns:
        Processing result summary as string
    """
    logger.info(f"[japan_post_tracking_10] Processing DataFrame with {len(df)} rows")
    logger.info(f"[japan_post_tracking_10] DataFrame columns: {list(df.columns)}")
    logger.info(f"[japan_post_tracking_10] DataFrame shape: {df.shape}")

    try:
        # Validate DataFrame
        if df.empty:
            logger.warning("[japan_post_tracking_10] Received empty DataFrame")
            return "Empty DataFrame received"

        # Check required columns
        required_columns = ['お問い合わせ番号', '最新年月日', '最新状態']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            error_msg = f"Missing required columns: {missing_columns}. Available columns: {list(df.columns)}"
            logger.error(f"[japan_post_tracking_10] {error_msg}")
            return error_msg

        logger.info(f"[japan_post_tracking_10] All required columns found")

        # Step 1: Extract tracking data from DataFrame
        tracking_data = extract_tracking_data(df)

        if not tracking_data:
            logger.warning(f"[japan_post_tracking_10] No valid tracking data found in DataFrame")
            logger.warning(f"[japan_post_tracking_10] Sample data (first 3 rows): {df.head(3).to_dict('records')}")
            return "No valid tracking data found"

        logger.info(f"[japan_post_tracking_10] Extracted {len(tracking_data)} tracking records")
        logger.info(f"[japan_post_tracking_10] Sample tracking data: {tracking_data[0] if tracking_data else 'N/A'}")

        # Step 2: Update Purchasing records
        stats = update_purchasing_records(tracking_data)

        # Step 3: Log summary
        summary = (
            f"Japan Post Tracking 10 processing completed: "
            f"{stats['updated']} updated, "
            f"{stats['not_found']} not found, "
            f"{stats['errors']} errors, "
            f"{stats['total_processed']} total processed"
        )

        logger.info(f"[japan_post_tracking_10] {summary}")

        return summary

    except Exception as exc:
        error_msg = f"Failed to process Japan Post tracking data: {exc}"
        logger.error(f"[japan_post_tracking_10] {error_msg}", exc_info=True)
        return error_msg
