"""
Django management command to trigger Temporary Flexible Capture task.

Usage:
    # Show usage help (no filter specified)
    python manage.py run_temporary_flexible_capture

    # Filter by single condition
    python manage.py run_temporary_flexible_capture --confirmed-at null
    python manage.py run_temporary_flexible_capture --latest-delivery-status "配達完了"

    # Filter by multiple conditions (OR relationship)
    python manage.py run_temporary_flexible_capture --confirmed-at null --batch-encoding notnull

    # With batch count and sync mode
    python manage.py run_temporary_flexible_capture --confirmed-at notnull --count 3 --sync

    # Dry run mode (show matching records without publishing)
    python manage.py run_temporary_flexible_capture --batch-level-1 "A" --dry-run

Supported filter fields:
    --confirmed-at              : null/notnull
    --latest-delivery-status    : null/notnull/text
    --batch-encoding            : null/notnull/text
    --batch-level-1             : null/notnull/text
    --batch-level-2             : null/notnull/text
    --batch-level-3             : null/notnull/text
    --estimated-delivery-date   : null/notnull
    --last-info-updated-at      : null/notnull
    --delivery-status-query-time: null/notnull
    --estimated-website-arrival-date: null/notnull
    --tracking-number           : null/notnull/text

Multiple conditions are combined with OR relationship.
"""

from django.core.management.base import BaseCommand
from apps.data_acquisition.workers.tasks_temporary_flexible_capture import process_record
from apps.data_acquisition.workers.temporary_flexible_capture import (
    TemporaryFlexibleCaptureWorker,
    FIELD_MAPPING,
    DATE_ONLY_FIELDS,
    TEXT_FIELDS,
)


class Command(BaseCommand):
    help = (
        'Trigger Temporary Flexible Capture task to query Purchasing model '
        'with flexible filter conditions and publish Apple Store tracking tasks '
        'to WebScraper API. Multiple conditions are combined with OR relationship.'
    )

    def add_arguments(self, parser):
        # Filter arguments
        parser.add_argument(
            '--confirmed-at',
            type=str,
            help='Filter by confirmed_at field (null/notnull)',
        )
        parser.add_argument(
            '--latest-delivery-status',
            type=str,
            help='Filter by latest_delivery_status field (null/notnull/text)',
        )
        parser.add_argument(
            '--batch-encoding',
            type=str,
            help='Filter by batch_encoding field (null/notnull/text)',
        )
        parser.add_argument(
            '--batch-level-1',
            type=str,
            help='Filter by batch_level_1 field (null/notnull/text)',
        )
        parser.add_argument(
            '--batch-level-2',
            type=str,
            help='Filter by batch_level_2 field (null/notnull/text)',
        )
        parser.add_argument(
            '--batch-level-3',
            type=str,
            help='Filter by batch_level_3 field (null/notnull/text)',
        )
        parser.add_argument(
            '--estimated-delivery-date',
            type=str,
            help='Filter by estimated_delivery_date field (null/notnull)',
        )
        parser.add_argument(
            '--last-info-updated-at',
            type=str,
            help='Filter by last_info_updated_at field (null/notnull)',
        )
        parser.add_argument(
            '--delivery-status-query-time',
            type=str,
            help='Filter by delivery_status_query_time field (null/notnull)',
        )
        parser.add_argument(
            '--estimated-website-arrival-date',
            type=str,
            help='Filter by estimated_website_arrival_date field (null/notnull)',
        )
        parser.add_argument(
            '--tracking-number',
            type=str,
            help='Filter by tracking_number field (null/notnull/text)',
        )

        # Control arguments
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

    def _build_filter_dict(self, options) -> dict:
        """Build filter dictionary from command options."""
        # Mapping from command option names to field names
        option_to_field = {
            'confirmed_at': 'confirmed_at',
            'latest_delivery_status': 'latest_delivery_status',
            'batch_encoding': 'batch_encoding',
            'batch_level_1': 'batch_level_1',
            'batch_level_2': 'batch_level_2',
            'batch_level_3': 'batch_level_3',
            'estimated_delivery_date': 'estimated_delivery_date',
            'last_info_updated_at': 'last_info_updated_at',
            'delivery_status_query_time': 'delivery_status_query_time',
            'estimated_website_arrival_date': 'estimated_website_arrival_date',
            'tracking_number': 'tracking_number',
        }

        filter_dict = {}
        for option_name, field_name in option_to_field.items():
            value = options.get(option_name)
            if value is not None:
                filter_dict[field_name] = value

        return filter_dict

    def _print_usage(self):
        """Print usage help message."""
        self.stdout.write('')
        self.stdout.write(self.style.WARNING('No filter conditions specified!'))
        self.stdout.write('')
        self.stdout.write('Usage: python manage.py run_temporary_flexible_capture [OPTIONS]')
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('Filter Options (at least one required):'))
        self.stdout.write('')
        self.stdout.write('  Date/Time fields (supports: null, notnull):')
        self.stdout.write('    --confirmed-at <null|notnull>')
        self.stdout.write('    --estimated-delivery-date <null|notnull>')
        self.stdout.write('    --last-info-updated-at <null|notnull>')
        self.stdout.write('    --delivery-status-query-time <null|notnull>')
        self.stdout.write('    --estimated-website-arrival-date <null|notnull>')
        self.stdout.write('')
        self.stdout.write('  Text fields (supports: null, notnull, or exact text):')
        self.stdout.write('    --latest-delivery-status <null|notnull|text>')
        self.stdout.write('    --batch-encoding <null|notnull|text>')
        self.stdout.write('    --batch-level-1 <null|notnull|text>')
        self.stdout.write('    --batch-level-2 <null|notnull|text>')
        self.stdout.write('    --batch-level-3 <null|notnull|text>')
        self.stdout.write('    --tracking-number <null|notnull|text>')
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('Control Options:'))
        self.stdout.write('    --count <N>     Number of tasks to queue (default: 1)')
        self.stdout.write('    --sync          Run synchronously instead of queuing')
        self.stdout.write('    --dry-run       Show matching records without publishing')
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('Notes:'))
        self.stdout.write('  - Multiple conditions are combined with OR relationship')
        self.stdout.write('  - Implicit conditions always applied:')
        self.stdout.write('    * Has related official_account')
        self.stdout.write('    * official_account.email is not empty')
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('Examples:'))
        self.stdout.write('  # Find records where confirmed_at is NULL')
        self.stdout.write('  python manage.py run_temporary_flexible_capture --confirmed-at null --dry-run')
        self.stdout.write('')
        self.stdout.write('  # Find records with specific delivery status')
        self.stdout.write('  python manage.py run_temporary_flexible_capture --latest-delivery-status "配達完了"')
        self.stdout.write('')
        self.stdout.write('  # Multiple conditions (OR): confirmed_at is NULL OR batch_encoding is not empty')
        self.stdout.write('  python manage.py run_temporary_flexible_capture --confirmed-at null --batch-encoding notnull')
        self.stdout.write('')

    def handle(self, *args, **options):
        count = options['count']
        sync = options['sync']
        dry_run = options['dry_run']

        # Build filter dictionary
        filter_dict = self._build_filter_dict(options)

        # Check if any filter is specified
        if not filter_dict:
            self._print_usage()
            return

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('Filter conditions (OR relationship):'))
        for field, value in filter_dict.items():
            self.stdout.write(f'  {field}: {value}')
        self.stdout.write('')

        if dry_run:
            self._handle_dry_run(filter_dict)
            return

        if sync:
            self._handle_sync(filter_dict)
            return

        self._handle_async(filter_dict, count)

    def _handle_dry_run(self, filter_dict: dict):
        """Show matching records without publishing tasks."""
        self.stdout.write(
            self.style.WARNING('Dry run mode - showing matching records only')
        )
        self.stdout.write('')

        worker = TemporaryFlexibleCaptureWorker()
        records = worker.get_matching_records(filter_dict)

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
            self.stdout.write(f'      confirmed_at: {record.confirmed_at or "NULL"}')
            self.stdout.write(f'      latest_delivery_status: {record.latest_delivery_status or "NULL"}')
            self.stdout.write(f'      batch_encoding: {record.batch_encoding or "NULL"}')
            self.stdout.write(f'      batch_level_1: {record.batch_level_1 or "NULL"}')
            self.stdout.write(f'      batch_level_2: {record.batch_level_2 or "NULL"}')
            self.stdout.write(f'      batch_level_3: {record.batch_level_3 or "NULL"}')
            self.stdout.write(f'      estimated_delivery_date: {record.estimated_delivery_date or "NULL"}')
            self.stdout.write(f'      last_info_updated_at: {record.last_info_updated_at or "NULL"}')
            self.stdout.write(f'      tracking_number: {record.tracking_number or "NULL"}')
            self.stdout.write('')

    def _handle_sync(self, filter_dict: dict):
        """Run the worker synchronously."""
        self.stdout.write(
            self.style.SUCCESS('Running Temporary Flexible Capture task synchronously...')
        )

        worker = TemporaryFlexibleCaptureWorker()
        result = worker.run({'filter_dict': filter_dict})

        if result.get('status') == 'success':
            total = result.get('total_records', 0)
            dispatched = result.get('dispatched_count', 0)
            batch_uuid = result.get('batch_uuid', 'N/A')

            self.stdout.write('')
            self.stdout.write(
                self.style.SUCCESS('Task completed successfully!')
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

    def _handle_async(self, filter_dict: dict, count: int):
        """Queue tasks to Celery."""
        self.stdout.write(
            self.style.SUCCESS(
                f'Triggering {count} Temporary Flexible Capture task(s)...'
            )
        )

        results = []
        for i in range(count):
            result = process_record.delay(filter_dict=filter_dict)
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
