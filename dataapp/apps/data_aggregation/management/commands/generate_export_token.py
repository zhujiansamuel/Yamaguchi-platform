"""
Django management command to display API token usage.
显示 API Token 使用方法的 Django 管理命令。

Usage:
    python manage.py generate_export_token

Note:
    This command now displays the BATCH_STATS_API_TOKEN usage.
    All APIs use the same token configured in settings/environment.
"""
from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    help = 'Display API token usage for export and other APIs'

    def handle(self, *args, **options):
        # Get token from settings
        token = getattr(settings, 'BATCH_STATS_API_TOKEN', '')

        # Display token information
        self.stdout.write(self.style.SUCCESS('\n' + '='*80))
        self.stdout.write(self.style.SUCCESS('API Token Usage'))
        self.stdout.write(self.style.SUCCESS('='*80 + '\n'))

        if not token or token == 'change-this-to-a-secure-token':
            self.stdout.write(self.style.WARNING(
                'Warning: BATCH_STATS_API_TOKEN is not configured or using default value.\n'
                'Please set BATCH_STATS_API_TOKEN in your .env file or settings.\n'
            ))
        else:
            # Show masked token
            masked_token = token[:4] + '*' * (len(token) - 8) + token[-4:] if len(token) > 8 else '****'
            self.stdout.write(f"Token (masked): {masked_token}\n")

        self.stdout.write(self.style.WARNING('Configuration:\n'))
        self.stdout.write('# In .env file:')
        self.stdout.write('BATCH_STATS_API_TOKEN=your-secure-token-here\n')

        self.stdout.write(self.style.WARNING('Usage examples:\n'))
        
        self.stdout.write('# Export to Excel API:')
        self.stdout.write('curl -X POST http://localhost:8000/api/aggregation/export-to-excel/ \\')
        self.stdout.write('  -H "Authorization: Bearer <BATCH_STATS_API_TOKEN>" \\')
        self.stdout.write('  -H "Content-Type: application/json" \\')
        self.stdout.write('  -d \'{"models": ["iPhone", "iPad"]}\'\n')

        self.stdout.write('# ViewSet APIs (e.g., iPhones):')
        self.stdout.write('curl http://localhost:8000/api/aggregation/iphones/ \\')
        self.stdout.write('  -H "Authorization: Bearer <BATCH_STATS_API_TOKEN>"\n')

        self.stdout.write('# Historical Data Stats API:')
        self.stdout.write('curl "http://localhost:8000/api/aggregation/v1/historical-data/batch-stats/?token=<BATCH_STATS_API_TOKEN>"\n')

        self.stdout.write('# Order Planning API:')
        self.stdout.write('curl -X POST http://localhost:8000/api/acquisition/order-planning/ \\')
        self.stdout.write('  -H "Authorization: Bearer <BATCH_STATS_API_TOKEN>" \\')
        self.stdout.write('  -H "Content-Type: application/json" \\')
        self.stdout.write('  -d \'{"batch_encoding": "BATCH-2026-01", "jan": "4547597992388", "inventory_count": 2, "cards_per_group": 2, "card_type": "GiftCard"}\'\n')

        self.stdout.write(self.style.SUCCESS('='*80 + '\n'))
