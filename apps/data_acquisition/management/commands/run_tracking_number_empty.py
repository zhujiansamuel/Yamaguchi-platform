"""
Django management command to trigger Tracking Number Empty task.

Usage:
    python manage.py run_tracking_number_empty
    python manage.py run_tracking_number_empty --count 3
    python manage.py run_tracking_number_empty --sync
"""

from django.core.management.base import BaseCommand
from apps.data_acquisition.workers.tasks_tracking_number_empty import process_record
from apps.data_acquisition.workers.tracking_number_empty import TrackingNumberEmptyWorker


class Command(BaseCommand):
    help = (
        'Trigger Tracking Number Empty task to query Purchasing model '
        '(empty tracking_number, order_number starting with "w") '
        'and publish Apple Store tracking tasks to WebScraper API'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=1,
            help='Number of tasks to queue (default: 1)',
        )
        parser.add_argument(
            '--sync',
            action='store_true',
            help='Run synchronously instead of queuing to Celery',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show matching records without publishing tasks',
        )

    def handle(self, *args, **options):
        count = options['count']
        sync = options['sync']
        dry_run = options['dry_run']

        if dry_run:
            self._handle_dry_run()
            return

        if sync:
            self._handle_sync()
            return

        self._handle_async(count)

    def _handle_dry_run(self):
        """Show matching records without publishing tasks."""
        self.stdout.write(
            self.style.WARNING('Dry run mode - showing matching records only')
        )

        worker = TrackingNumberEmptyWorker()
        records = worker.get_matching_records()

        if not records:
            self.stdout.write(
                self.style.WARNING('No matching records found')
            )
            return

        self.stdout.write(
            self.style.SUCCESS(f'Found {len(records)} matching records:')
        )
        self.stdout.write('')

        for idx, record in enumerate(records):
            email = record.official_account.email if record.official_account else 'N/A'
            url = worker.construct_url(record.order_number, email)

            self.stdout.write(f'  [{idx+1}] ID: {record.id}')
            self.stdout.write(f'      Order: {record.order_number}')
            self.stdout.write(f'      Email: {email}')
            self.stdout.write(f'      URL: {url}')
            self.stdout.write(f'      Status: {record.latest_delivery_status or "N/A"}')
            self.stdout.write('')

    def _handle_sync(self):
        """Run the worker synchronously."""
        self.stdout.write(
            self.style.SUCCESS('Running Tracking Number Empty task synchronously...')
        )

        worker = TrackingNumberEmptyWorker()
        result = worker.run()

        if result.get('status') == 'success':
            total = result.get('total_records', 0)
            dispatched = result.get('dispatched_count', 0)
            batch_uuid = result.get('batch_uuid', 'N/A')

            self.stdout.write('')
            self.stdout.write(
                self.style.SUCCESS(f'Task completed successfully!')
            )
            self.stdout.write(f'  Total records: {total}')
            self.stdout.write(f'  Dispatched tasks: {dispatched}')
            self.stdout.write(f'  Batch UUID: {batch_uuid}')

            if result.get('custom_ids'):
                self.stdout.write('')
                self.stdout.write('  Custom IDs:')
                for custom_id in result['custom_ids']:
                    self.stdout.write(f'    - {custom_id}')
        else:
            self.stdout.write(
                self.style.WARNING(f'Task result: {result}')
            )

    def _handle_async(self, count):
        """Queue tasks to Celery."""
        self.stdout.write(
            self.style.SUCCESS(
                f'Triggering {count} Tracking Number Empty task(s)...'
            )
        )

        results = []
        for i in range(count):
            result = process_record.delay()
            results.append(result.id)
            self.stdout.write(f'  Task {i+1}/{count}: {result.id}')

        self.stdout.write(
            self.style.SUCCESS(
                f'\nSuccessfully queued {len(results)} task(s)'
            )
        )
        self.stdout.write('Task IDs:')
        for task_id in results:
            self.stdout.write(f'  - {task_id}')
