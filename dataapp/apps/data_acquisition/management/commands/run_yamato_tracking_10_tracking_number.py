"""
Django management command to run Yamato Tracking 10 Tracking Number task

This command triggers the Yamato tracking query task that:
1. Queries Purchasing model for records matching criteria:
   - order_number starts with 'w' (case-insensitive)
   - tracking_number contains 12 digits starting with 4
   - latest_delivery_status is not "配達完了"
2. Extracts up to 10 valid tracking numbers
3. Queries Yamato tracking API in batch
4. Logs results (no retry on failure)

Usage:
    python manage.py run_yamato_tracking_10_tracking_number
"""

from django.core.management.base import BaseCommand
from apps.data_acquisition.tasks import process_yamato_tracking_10_tracking_number


class Command(BaseCommand):
    help = 'Run Yamato Tracking 10 Tracking Number task to query Purchasing records'

    def handle(self, *args, **options):
        self.stdout.write("=" * 80)
        self.stdout.write("Running Yamato Tracking 10 Tracking Number Task")
        self.stdout.write("=" * 80)

        # 触发Celery任务
        result = process_yamato_tracking_10_tracking_number.delay()

        self.stdout.write(f"\n✓ Task triggered successfully!")
        self.stdout.write(f"Task ID: {result.id}")
        self.stdout.write("\nTask will:")
        self.stdout.write("  1. Query Purchasing records with order_number starting with 'w'")
        self.stdout.write("  2. Filter tracking_number with 12 digits starting with 4")
        self.stdout.write("  3. Exclude records with latest_delivery_status='配達完了'")
        self.stdout.write("  4. Query up to 10 tracking numbers via Yamato API")
        self.stdout.write("\nCheck logs for execution details.")

        self.stdout.write("\n" + "=" * 80)
        self.stdout.write(self.style.SUCCESS("Task dispatched!"))
        self.stdout.write("=" * 80)
