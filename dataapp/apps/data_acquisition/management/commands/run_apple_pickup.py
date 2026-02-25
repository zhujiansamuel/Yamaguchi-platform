"""
Django management command to trigger Apple Store pickup contact update task.

Usage:
    python manage.py run_apple_pickup \
        --apple-id "user@example.com" \
        --password "xxx" \
        --newname "山田 太郎" \
        --ordernumber "W123456789"

Options:
    --apple-id: Apple ID email (required)
    --password: Apple ID password (required)
    --newname: New pickup contact name (required, format: "姓 名")
    --ordernumber: Order number (optional, will search by product if not provided)
    --product-fallback: Product name to search if order number not found (default: "iPhone")
    --item-id: Order item ID for element selectors (default: "0000101")
    --sync: Run synchronously instead of as Celery task
"""

from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = 'Trigger Apple Store pickup contact update task'

    def add_arguments(self, parser):
        parser.add_argument(
            '--apple-id',
            type=str,
            required=True,
            help='Apple ID email address',
        )
        parser.add_argument(
            '--password',
            type=str,
            required=True,
            help='Apple ID password',
        )
        parser.add_argument(
            '--newname',
            type=str,
            required=True,
            help='New pickup contact name (format: "姓 名")',
        )
        parser.add_argument(
            '--ordernumber',
            type=str,
            default=None,
            help='Order number (optional)',
        )
        parser.add_argument(
            '--product-fallback',
            type=str,
            default='iPhone',
            help='Product name to search if order number not found (default: iPhone)',
        )
        parser.add_argument(
            '--item-id',
            type=str,
            default='0000101',
            help='Order item ID for element selectors (default: 0000101)',
        )
        parser.add_argument(
            '--sync',
            action='store_true',
            help='Run synchronously instead of as Celery task',
        )

    def handle(self, *args, **options):
        apple_id = options['apple_id']
        password = options['password']
        newname = options['newname']
        ordernumber = options['ordernumber']
        product_fallback = options['product_fallback']
        item_id = options['item_id']
        sync = options['sync']

        # Validate inputs
        if not apple_id or not apple_id.strip():
            raise CommandError('Apple ID is required')
        if not password or not password.strip():
            raise CommandError('Password is required')
        if not newname or not newname.strip():
            raise CommandError('New name is required')

        self.stdout.write(f"Apple ID: {apple_id}")
        self.stdout.write(f"Order: {ordernumber or '(search by product)'}")
        self.stdout.write(f"New Name: {newname}")
        self.stdout.write(f"Product Fallback: {product_fallback}")
        self.stdout.write(f"Item ID: {item_id}")
        self.stdout.write("")

        if sync:
            # Run synchronously
            self.stdout.write(self.style.WARNING("Running synchronously..."))
            import asyncio
            from apps.data_acquisition.workers.tasks_playwright_apple_pickup import run_pickup_update

            result = asyncio.run(
                run_pickup_update(
                    apple_id=apple_id,
                    password=password,
                    newname=newname,
                    ordernumber=ordernumber,
                    product_fallback=product_fallback,
                    item_id=item_id,
                    headless=True,
                )
            )

            if result.get('success'):
                self.stdout.write(self.style.SUCCESS(f"Success: {result}"))
            else:
                self.stdout.write(self.style.ERROR(f"Failed: {result}"))

        else:
            # Submit as Celery task
            from apps.data_acquisition.workers.tasks_playwright_apple_pickup import (
                process_apple_pickup_contact_update,
            )

            self.stdout.write("Submitting Celery task...")

            task = process_apple_pickup_contact_update.delay(
                apple_id=apple_id,
                password=password,
                newname=newname,
                ordernumber=ordernumber,
                product_fallback=product_fallback,
                item_id=item_id,
            )

            self.stdout.write(self.style.SUCCESS(f"Task submitted: {task.id}"))
            self.stdout.write(f"Monitor at: Flower dashboard or check logs")
