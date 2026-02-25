"""
Django management command to reset all MailMessage is_extracted flags

This command sets is_extracted=False for all MailMessage records,
allowing emails to be processed again.

Usage:
    python manage.py reset_email_extraction
    python manage.py reset_email_extraction --confirm  # Skip confirmation prompt
"""

from django.core.management.base import BaseCommand
from apps.data_aggregation.models import MailMessage


class Command(BaseCommand):
    help = 'Reset is_extracted flag to False for all MailMessage records'

    def add_arguments(self, parser):
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Skip confirmation prompt',
        )

    def handle(self, *args, **options):
        self.stdout.write("=" * 80)
        self.stdout.write("Reset Email Extraction Flags")
        self.stdout.write("=" * 80)

        # Count total emails and extracted emails
        total_count = MailMessage.objects.count()
        extracted_count = MailMessage.objects.filter(is_extracted=True).count()
        unextracted_count = total_count - extracted_count

        self.stdout.write(f"\nTotal emails: {total_count}")
        self.stdout.write(f"  • Extracted (is_extracted=True): {extracted_count}")
        self.stdout.write(f"  • Unextracted (is_extracted=False): {unextracted_count}")

        if extracted_count == 0:
            self.stdout.write(self.style.SUCCESS("\n✓ All emails are already unextracted!"))
            return

        # Confirmation prompt unless --confirm flag is used
        if not options['confirm']:
            self.stdout.write(self.style.WARNING(f"\n⚠ This will reset is_extracted=False for {extracted_count} emails"))
            confirm = input("Are you sure you want to continue? [y/N]: ")
            if confirm.lower() != 'y':
                self.stdout.write(self.style.ERROR("\n✗ Operation cancelled"))
                return

        # Reset all is_extracted flags to False
        self.stdout.write(f"\nResetting is_extracted to False for {extracted_count} emails...")

        updated_count = MailMessage.objects.filter(is_extracted=True).update(is_extracted=False)

        self.stdout.write(self.style.SUCCESS(f"\n✓ Successfully reset {updated_count} emails"))
        self.stdout.write(f"All {total_count} emails are now available for processing")

        self.stdout.write("\n" + "=" * 80)
        self.stdout.write(self.style.SUCCESS("Reset completed!"))
        self.stdout.write("=" * 80)
