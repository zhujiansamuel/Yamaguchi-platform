"""
Django management command to run Email Content Analysis Worker

This command processes up to 10 unprocessed emails:
1. Fetches up to 10 unprocessed emails from the database
2. Classifies them by type (order confirmation or shipping notification)
3. Parses and extracts information
4. Triggers appropriate tasks
5. Marks emails as extracted

Usage:
    python manage.py run_email_content_analysis
"""

from django.core.management.base import BaseCommand
from apps.data_acquisition.EmailParsing.email_content_analysis import EmailContentAnalysisWorker


class Command(BaseCommand):
    help = 'Run Email Content Analysis Worker to process up to 10 emails'

    def handle(self, *args, **options):
        self.stdout.write("=" * 80)
        self.stdout.write("Running Email Content Analysis Worker")
        self.stdout.write("=" * 80)

        worker = EmailContentAnalysisWorker()
        result = worker.run({})

        status = result.get('status')
        self.stdout.write(f"\nWorker Status: {status}")

        if status == 'success':
            exec_result = result.get('result', {})
            if exec_result.get('status') == 'success':
                processed_count = exec_result.get('processed_count', 0)
                skipped_count = exec_result.get('skipped_count', 0)
                processed_emails = exec_result.get('processed_emails', [])

                self.stdout.write(self.style.SUCCESS(f"\n✓ Processing completed!"))
                self.stdout.write(f"\nProcessed: {processed_count} emails")
                self.stdout.write(f"Skipped: {skipped_count} emails")

                if processed_emails:
                    self.stdout.write("\n--- Processed Emails ---")
                    for email in processed_emails:
                        self.stdout.write(f"\n  Email ID: {email.get('email_id')}")
                        self.stdout.write(f"    Type: {email.get('type')}")
                        self.stdout.write(f"    Order Number: {email.get('order_number')}")
                        self.stdout.write(f"    Task ID: {email.get('task_id')}")

                self.stdout.write(self.style.SUCCESS(f"\n✓ {processed_count} email(s) marked as extracted"))

            elif exec_result.get('status') == 'no_email':
                self.stdout.write(self.style.WARNING("\n⚠ No unprocessed emails found"))
                self.stdout.write("\nPlease ensure the database contains emails with:")
                self.stdout.write("  • is_extracted is not True")
                self.stdout.write("  • Associated MailMessageBody with text_html content")

            else:
                self.stdout.write(self.style.ERROR(f"\n✗ Unknown execution status: {exec_result.get('status')}"))
                self.stdout.write(f"Message: {exec_result.get('message')}")

        elif status == 'error':
            self.stdout.write(self.style.ERROR("\n✗ Worker execution failed"))
            self.stdout.write(f"Error: {result.get('error')}")

        else:
            self.stdout.write(self.style.ERROR(f"\n✗ Unknown worker status: {status}"))

        self.stdout.write("\n" + "=" * 80)
        self.stdout.write(self.style.SUCCESS("Processing completed!"))
        self.stdout.write("=" * 80)
