#!/usr/bin/env python3
"""
Script to clear date fields from all Purchasing instances.
清除所有 Purchasing 实例的日期字段信息。

Fields to be cleared:
- estimated_delivery_date (邮寄送达预计时间)
- estimated_website_arrival_date (官网到达预计时间)
- estimated_website_arrival_date_2 (官网到达预计时间2)
- last_info_updated_at (最后信息更新时间)

Usage:
    python scripts/clear_estimated_delivery_date.py

This script will:
1. Connect to the database using Django ORM
2. Set the above fields to NULL for all Purchasing instances
3. Display the number of records updated for each field
"""

import os
import sys
from pathlib import Path

import django


# Setup Django environment
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")
django.setup()

from apps.data_aggregation.models import Purchasing


# Fields to be cleared
FIELDS_TO_CLEAR = [
    'estimated_delivery_date',
    'estimated_website_arrival_date',
    'estimated_website_arrival_date_2',
    'last_info_updated_at',
]

# Field display names (Chinese)
FIELD_NAMES = {
    'estimated_delivery_date': '邮寄送达预计时间',
    'estimated_website_arrival_date': '官网到达预计时间',
    'estimated_website_arrival_date_2': '官网到达预计时间2',
    'last_info_updated_at': '最后信息更新时间',
}


def clear_date_fields():
    """
    Clear specified date fields from all Purchasing instances.
    清除所有 Purchasing 实例的指定日期字段。
    """
    print("Starting to clear date fields from Purchasing instances...")
    print("=" * 70)
    
    # Count total Purchasing instances
    total_count = Purchasing.objects.count()
    print(f"Total Purchasing instances: {total_count}")
    print()
    
    # Count instances with non-null values for each field
    field_stats = {}
    total_non_null = 0
    
    print("Current status of fields to be cleared:")
    print("-" * 70)
    
    for field in FIELDS_TO_CLEAR:
        count = Purchasing.objects.filter(**{f"{field}__isnull": False}).count()
        field_stats[field] = count
        total_non_null += count
        field_display = FIELD_NAMES.get(field, field)
        print(f"  {field_display:30s} ({field}): {count} instances")
    
    print("-" * 70)
    
    if total_non_null == 0:
        print("\nNo records to update. All specified fields are already NULL.")
        return
    
    # Confirm before proceeding
    print("\n" + "=" * 70)
    print("WARNING: This will set the following fields to NULL:")
    for field in FIELDS_TO_CLEAR:
        field_display = FIELD_NAMES.get(field, field)
        count = field_stats[field]
        if count > 0:
            print(f"  - {field_display} ({field}): {count} instance(s)")
    print("=" * 70)
    
    confirmation = input("\nDo you want to proceed? (yes/no): ").strip().lower()
    
    if confirmation not in ['yes', 'y']:
        print("\nOperation cancelled by user.")
        return
    
    print("\nClearing fields...")
    print("-" * 70)
    
    # Update all instances - set all fields to None at once
    update_dict = {field: None for field in FIELDS_TO_CLEAR}
    
    # Only update instances that have at least one non-null field
    from django.db.models import Q
    query = Q()
    for field in FIELDS_TO_CLEAR:
        query |= Q(**{f"{field}__isnull": False})
    
    updated_count = Purchasing.objects.filter(query).update(**update_dict)
    
    print(f"✓ Updated {updated_count} Purchasing instance(s)")
    print()
    
    # Verify the update for each field
    print("Verification results:")
    print("-" * 70)
    
    all_cleared = True
    for field in FIELDS_TO_CLEAR:
        remaining_count = Purchasing.objects.filter(**{f"{field}__isnull": False}).count()
        field_display = FIELD_NAMES.get(field, field)
        
        if remaining_count == 0:
            print(f"  ✓ {field_display:30s}: All cleared")
        else:
            print(f"  ⚠ {field_display:30s}: {remaining_count} instance(s) still have values")
            all_cleared = False
    
    print("-" * 70)
    
    if all_cleared:
        print("\n✓ All specified fields have been successfully cleared.")
    else:
        print("\n⚠ Warning: Some fields still have non-null values.")
    
    print("=" * 70)
    print("Operation completed.")


def main():
    """Main entry point for the script."""
    try:
        clear_date_fields()
    except KeyboardInterrupt:
        print("\n\nOperation interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Error occurred: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
