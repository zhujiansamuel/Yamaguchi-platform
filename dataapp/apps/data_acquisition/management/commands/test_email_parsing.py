"""
Django management command to test Email Content Analysis Worker

Usage:
    python manage.py test_email_parsing
"""

from django.core.management.base import BaseCommand
from apps.data_acquisition.EmailParsing.email_content_analysis import (
    EmailContentAnalysisWorker,
    parse_apple_order_email,
)


class Command(BaseCommand):
    help = 'Test Email Content Analysis Worker for Apple order emails'

    def handle(self, *args, **options):
        self.stdout.write("=" * 80)
        self.stdout.write("Testing Email Content Analysis Worker")
        self.stdout.write("=" * 80)

        # Test HTML parsing function with sample data
        self.test_html_parsing()

        # Test the full worker
        self.test_worker()

        self.stdout.write("\n" + "=" * 80)
        self.stdout.write(self.style.SUCCESS("Testing completed!"))
        self.stdout.write("=" * 80)

    def test_html_parsing(self):
        """Test HTML parsing function with sample data"""
        self.stdout.write("\n--- Testing HTML Parsing Function ---\n")

        # Sample HTML (simplified version for testing)
        sample_html = """
        <html>
            <body>
                <div class="order-num">
                    <span>2024/01/15</span>
                </div>
                <a class="aapl-link" href="https://secure2.store.apple.com/vieworder?orderId=W1234567890">
                    W1234567890
                </a>
                <span>お届け予定日：2024/01/20 - 2024/01/25</span>
                <td class="product-name-td">iPhone 15 Pro Max 256GB ナチュラルチタニウム</td>
                <td class="product-quantity">1</td>
                <h3>お届け先住所</h3>
                <div class="gen-txt">
                    123-4567
                    東京都
                    渋谷区神南1-2-3
                    山田太郎
                </div>
                <div>test@example.com</div>
            </body>
        </html>
        """

        result = parse_apple_order_email(sample_html)

        if result:
            self.stdout.write(self.style.SUCCESS("\n✓ HTML parsing successful!"))
            self.stdout.write("\nExtracted data:")
            for key, value in result.items():
                self.stdout.write(f"  • {key}: {value}")
        else:
            self.stdout.write(self.style.ERROR("\n✗ HTML parsing failed"))

    def test_worker(self):
        """Test the full Email Content Analysis Worker"""
        self.stdout.write("\n\n--- Testing Email Content Analysis Worker ---\n")

        worker = EmailContentAnalysisWorker()
        result = worker.run({})

        status = result.get('status')
        self.stdout.write(f"\nWorker Status: {status}")

        if status == 'success':
            self.stdout.write(self.style.SUCCESS("\n✓ Worker executed successfully!"))

            extracted_data = result.get('result', {}).get('extracted_data', {})
            self.stdout.write("\nExtracted data from database:")
            self.stdout.write(f"  • Email ID: {extracted_data.get('email_id')}")
            self.stdout.write(f"  • Order Number: {extracted_data.get('order_number')}")
            self.stdout.write(f"  • Official Query URL: {extracted_data.get('official_query_url')}")
            self.stdout.write(f"  • Confirmed At: {extracted_data.get('confirmed_at')}")
            self.stdout.write(f"  • Estimated Arrival Date: {extracted_data.get('estimated_website_arrival_date')}")
            self.stdout.write(f"  • Estimated Arrival Date 2: {extracted_data.get('estimated_website_arrival_date_2')}")
            self.stdout.write(f"  • Product Name: {extracted_data.get('iphone_product_names')}")
            self.stdout.write(f"  • Quantity: {extracted_data.get('quantities')}")
            self.stdout.write(f"  • Email: {extracted_data.get('email')}")
            self.stdout.write(f"  • Name: {extracted_data.get('name')}")
            self.stdout.write(f"  • Postal Code: {extracted_data.get('postal_code')}")
            self.stdout.write(f"  • Address Line 1: {extracted_data.get('address_line_1')}")
            self.stdout.write(f"  • Address Line 2: {extracted_data.get('address_line_2')}")

        elif status == 'no_email':
            self.stdout.write(self.style.WARNING("\n⚠ No matching emails found in database"))
            self.stdout.write("\nPlease ensure the database contains:")
            self.stdout.write("  • Subject containing 'ご注文ありがとうございます'")
            self.stdout.write("  • From address: 'order_acknowledgment@orders.apple.com'")
            self.stdout.write("  • Associated MailMessageBody with text_html content")

        else:
            self.stdout.write(self.style.ERROR(f"\n✗ Worker execution failed"))
            self.stdout.write(f"Message: {result.get('message')}")
            if 'error' in result:
                self.stdout.write(f"Error: {result.get('error')}")
