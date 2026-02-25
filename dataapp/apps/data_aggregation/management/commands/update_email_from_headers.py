"""
Django management command to update from_address and from_name for all MailMessage instances.
从 raw_headers 中重新提取所有邮件的发件人地址和姓名。

Usage:
    python manage.py update_email_from_headers [--dry-run] [--batch-size N]
"""
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from apps.data_aggregation.models import MailMessage
from email.utils import parseaddr


class Command(BaseCommand):
    help = 'Update from_address and from_name for all MailMessage instances from raw_headers'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Preview changes without actually updating the database',
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=100,
            help='Number of records to process in each batch (default: 100)',
        )
        parser.add_argument(
            '--limit',
            type=int,
            help='Limit the number of messages to process (for testing)',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        batch_size = options['batch_size']
        limit = options.get('limit')

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be saved'))
            self.stdout.write('')

        # Get all MailMessage instances
        queryset = MailMessage.objects.all()
        total_count = queryset.count()

        if limit:
            queryset = queryset[:limit]
            self.stdout.write(self.style.WARNING(f'Processing limited to {limit} messages'))
            self.stdout.write('')

        self.stdout.write(f'Total MailMessage records: {total_count}')
        self.stdout.write(f'Processing: {queryset.count()} messages')
        self.stdout.write(f'Batch size: {batch_size}')
        self.stdout.write('')

        # Statistics
        updated_count = 0
        skipped_count = 0
        error_count = 0
        unchanged_count = 0

        # Process in batches
        batch_num = 0
        messages = list(queryset.iterator(chunk_size=batch_size))

        for i in range(0, len(messages), batch_size):
            batch = messages[i:i + batch_size]
            batch_num += 1

            self.stdout.write(f'Processing batch {batch_num} ({len(batch)} messages)...')

            for message in batch:
                try:
                    # Extract from raw_headers
                    raw_headers = message.raw_headers or {}
                    raw_from = raw_headers.get('from', '')

                    new_from_address = ''
                    new_from_name = ''

                    if raw_from:
                        # Remove "From: " prefix if present
                        if raw_from.startswith('From: '):
                            raw_from = raw_from[6:]

                        # Parse the email address and name using parseaddr
                        parsed_name, parsed_address = parseaddr(raw_from)
                        new_from_address = parsed_address
                        new_from_name = parsed_name

                    # If raw_headers parsing failed, keep existing values
                    if not new_from_address:
                        skipped_count += 1
                        if options['verbosity'] >= 2:
                            self.stdout.write(
                                f'  Skipped message {message.id}: No valid from in raw_headers'
                            )
                        continue

                    # Check if values actually changed
                    if (message.from_address == new_from_address and
                        message.from_name == new_from_name):
                        unchanged_count += 1
                        if options['verbosity'] >= 2:
                            self.stdout.write(
                                f'  Unchanged message {message.id}: Values already match'
                            )
                        continue

                    # Update the message
                    if not dry_run:
                        old_address = message.from_address
                        old_name = message.from_name

                        message.from_address = new_from_address
                        message.from_name = new_from_name

                        # Update sender_domain as well
                        message.sender_domain = (
                            new_from_address.split('@')[-1]
                            if '@' in new_from_address else ''
                        )

                        message.save(update_fields=['from_address', 'from_name', 'sender_domain'])

                        updated_count += 1

                        if options['verbosity'] >= 2:
                            self.stdout.write(
                                self.style.SUCCESS(
                                    f'  ✓ Updated message {message.id}:\n'
                                    f'    Address: "{old_address}" → "{new_from_address}"\n'
                                    f'    Name: "{old_name}" → "{new_from_name}"'
                                )
                            )
                    else:
                        # Dry run - just show what would change
                        updated_count += 1
                        if options['verbosity'] >= 1:
                            self.stdout.write(
                                f'  [DRY RUN] Would update message {message.id}:\n'
                                f'    Address: "{message.from_address}" → "{new_from_address}"\n'
                                f'    Name: "{message.from_name}" → "{new_from_name}"'
                            )

                except Exception as e:
                    error_count += 1
                    self.stdout.write(
                        self.style.ERROR(
                            f'  ✗ Error processing message {message.id}: {str(e)}'
                        )
                    )

            # Progress update
            processed = min(i + batch_size, len(messages))
            self.stdout.write(
                f'Progress: {processed}/{len(messages)} messages processed'
            )
            self.stdout.write('')

        # Print summary
        self.stdout.write('')
        self.stdout.write('=' * 80)
        self.stdout.write(self.style.SUCCESS('Update Complete!'))
        self.stdout.write('=' * 80)
        self.stdout.write(f'Total processed:  {len(messages)}')
        self.stdout.write(self.style.SUCCESS(f'Updated:          {updated_count}'))
        self.stdout.write(self.style.WARNING(f'Unchanged:        {unchanged_count}'))
        self.stdout.write(self.style.WARNING(f'Skipped:          {skipped_count} (no valid from in raw_headers)'))

        if error_count > 0:
            self.stdout.write(self.style.ERROR(f'Errors:           {error_count}'))
        else:
            self.stdout.write(f'Errors:           {error_count}')

        self.stdout.write('=' * 80)

        if dry_run:
            self.stdout.write('')
            self.stdout.write(
                self.style.WARNING(
                    'This was a DRY RUN - no changes were saved to the database.'
                )
            )
            self.stdout.write(
                self.style.WARNING(
                    'Run without --dry-run to apply these changes.'
                )
            )
