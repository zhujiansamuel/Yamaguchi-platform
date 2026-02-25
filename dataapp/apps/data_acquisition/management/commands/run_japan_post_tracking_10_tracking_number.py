"""
Django management command to trigger Japan Post Tracking 10 Tracking Number task.

Usage:
    python manage.py run_japan_post_tracking_10_tracking_number
"""

from django.core.management.base import BaseCommand
from apps.data_acquisition.workers.tasks_japan_post_tracking_10_tracking_number import process_record


class Command(BaseCommand):
    help = 'Trigger Japan Post Tracking 10 Tracking Number task to query Purchasing model and publish tracking tasks'

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=1,
            help='Number of tasks to queue (default: 1)',
        )

    def handle(self, *args, **options):
        count = options['count']
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Triggering {count} Japan Post Tracking 10 Tracking Number task(s)...'
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
