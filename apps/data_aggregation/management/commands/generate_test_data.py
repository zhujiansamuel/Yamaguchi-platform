"""
Django management command to generate test data for data_aggregation app.
"""
import random
from datetime import datetime, timedelta
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.data_aggregation.models import (
    AggregationSource, AggregatedData, AggregationTask,
    iPhone, iPad, TemporaryChannel, LegalPersonOffline,
    EcSite, OfficialAccount, Purchasing, GiftCard,
    DebitCard, DebitCardPayment, CreditCard, CreditCardPayment,
    Inventory
)


class Command(BaseCommand):
    help = 'Generate random test data for all data_aggregation models'

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=10,
            help='Number of records to create for each model (default: 10)'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before generating new data'
        )

    def handle(self, *args, **options):
        count = options['count']
        clear = options['clear']

        if clear:
            self.stdout.write(self.style.WARNING('Clearing existing data...'))
            self.clear_all_data()
            self.stdout.write(self.style.SUCCESS('Data cleared!'))

        self.stdout.write(self.style.SUCCESS(f'Generating {count} records for each model...'))

        # Generate data in order (respecting dependencies)
        self.generate_aggregation_sources(count)
        self.generate_aggregated_data(count)
        self.generate_aggregation_tasks(count)
        self.generate_iphones(count)
        self.generate_ipads(count)
        self.generate_temporary_channels(count)
        self.generate_legal_person_offline(count)
        self.generate_ec_sites(count)
        self.generate_official_accounts(count)
        self.generate_purchasing_orders(count)
        self.generate_gift_cards(count)
        self.generate_debit_cards(count)
        self.generate_credit_cards(count)
        self.generate_debit_card_payments(min(count, 20))
        self.generate_credit_card_payments(min(count, 20))
        self.generate_inventory(count * 2)  # More inventory items

        self.stdout.write(self.style.SUCCESS('✅ All test data generated successfully!'))

    def clear_all_data(self):
        """Clear all existing data"""
        models = [
            Inventory, CreditCardPayment, DebitCardPayment,
            CreditCard, DebitCard, GiftCard, Purchasing,
            OfficialAccount, EcSite, LegalPersonOffline,
            TemporaryChannel, iPad, iPhone,
            AggregationTask, AggregatedData, AggregationSource
        ]
        for model in models:
            count = model.objects.all().delete()[0]
            self.stdout.write(f'  Deleted {count} {model.__name__} records')

    def random_date(self, start_days_ago=365, end_days_ago=0):
        """Generate random date within range"""
        start = timezone.now() - timedelta(days=start_days_ago)
        end = timezone.now() - timedelta(days=end_days_ago)
        delta = end - start
        random_days = random.randint(0, delta.days)
        return start + timedelta(days=random_days)

    def random_datetime(self, start_days_ago=365, end_days_ago=0):
        """Generate random datetime within range"""
        date = self.random_date(start_days_ago, end_days_ago)
        random_hour = random.randint(0, 23)
        random_minute = random.randint(0, 59)
        return date.replace(hour=random_hour, minute=random_minute, second=0, microsecond=0)

    def generate_aggregation_sources(self, count):
        """Generate AggregationSource records"""
        self.stdout.write('Creating AggregationSource records...')
        sources = []
        for i in range(count):
            source = AggregationSource.objects.create(
                name=f'Data Source {i+1}',
                description=f'Test data source number {i+1} for aggregation',
                status=random.choice(['active', 'inactive', 'error']),
                config={'type': 'test', 'priority': random.randint(1, 10)}
            )
            sources.append(source)
        self.stdout.write(self.style.SUCCESS(f'  ✓ Created {len(sources)} AggregationSource records'))

    def generate_aggregated_data(self, count):
        """Generate AggregatedData records"""
        self.stdout.write('Creating AggregatedData records...')
        sources = list(AggregationSource.objects.all())
        if not sources:
            self.stdout.write(self.style.WARNING('  ⚠ No sources available, skipping'))
            return

        data_list = []
        for i in range(count):
            data = AggregatedData.objects.create(
                source=random.choice(sources),
                data={'value': random.randint(100, 1000), 'metric': f'metric_{i}'},
                metadata={'processed': True, 'version': '1.0'},
                aggregated_at=self.random_datetime(30, 0)
            )
            data_list.append(data)
        self.stdout.write(self.style.SUCCESS(f'  ✓ Created {len(data_list)} AggregatedData records'))

    def generate_aggregation_tasks(self, count):
        """Generate AggregationTask records"""
        self.stdout.write('Creating AggregationTask records...')
        sources = list(AggregationSource.objects.all())

        tasks = []
        for i in range(count):
            status = random.choice(['pending', 'running', 'completed', 'failed'])
            started = self.random_datetime(7, 0) if status != 'pending' else None
            completed = self.random_datetime(7, 0) if status in ['completed', 'failed'] else None

            task = AggregationTask.objects.create(
                task_id=f'task-{i+1:04d}-{random.randint(1000, 9999)}',
                source=random.choice(sources) if sources else None,
                status=status,
                result={'count': random.randint(1, 100)} if status == 'completed' else None,
                error_message='Test error' if status == 'failed' else '',
                started_at=started,
                completed_at=completed
            )
            tasks.append(task)
        self.stdout.write(self.style.SUCCESS(f'  ✓ Created {len(tasks)} AggregationTask records'))

    def generate_iphones(self, count):
        """Generate iPhone records"""
        self.stdout.write('Creating iPhone records...')
        models = ['iPhone 15 Pro Max', 'iPhone 15 Pro', 'iPhone 15', 'iPhone 14 Pro', 'iPhone 14', 'iPhone 13']
        colors = ['Natural Titanium', 'Blue Titanium', 'White Titanium', 'Black Titanium', 'Purple', 'Blue', 'Midnight', 'Starlight']
        capacities = [128, 256, 512, 1024]

        iphones = []
        for i in range(count):
            model = random.choice(models)
            capacity = random.choice(capacities)
            color = random.choice(colors)

            iphone = iPhone.objects.create(
                part_number=f'MG{random.randint(100, 999)}{chr(random.randint(65, 90))}/A',
                model_name=model,
                capacity_gb=capacity,
                color=color,
                release_date=self.random_date(365, 30),
                jan=f'45{random.randint(10000000000, 99999999999)}'
            )
            iphones.append(iphone)
        self.stdout.write(self.style.SUCCESS(f'  ✓ Created {len(iphones)} iPhone records'))

    def generate_ipads(self, count):
        """Generate iPad records"""
        self.stdout.write('Creating iPad records...')
        models = ['iPad Pro 12.9"', 'iPad Pro 11"', 'iPad Air', 'iPad mini', 'iPad']
        colors = ['Space Gray', 'Silver', 'Starlight', 'Pink', 'Blue']
        capacities = [64, 128, 256, 512, 1024, 2048]

        ipads = []
        for i in range(count):
            model = random.choice(models)
            capacity = random.choice(capacities)
            color = random.choice(colors)

            ipad = iPad.objects.create(
                part_number=f'MP{random.randint(100, 999)}{chr(random.randint(65, 90))}/A',
                model_name=model,
                capacity_gb=capacity,
                color=color,
                release_date=self.random_date(365, 30),
                jan=f'45{random.randint(10000000000, 99999999999)}'
            )
            ipads.append(ipad)
        self.stdout.write(self.style.SUCCESS(f'  ✓ Created {len(ipads)} iPad records'))

    def generate_temporary_channels(self, count):
        """Generate TemporaryChannel records"""
        self.stdout.write('Creating TemporaryChannel records...')
        channels = []
        for i in range(count):
            channel = TemporaryChannel.objects.create(
                expected_time=self.random_datetime(30, -30),
                record=f'Temporary channel record {i+1} - {random.choice(["Supplier A", "Supplier B", "Supplier C"])}'
            )
            channels.append(channel)
        self.stdout.write(self.style.SUCCESS(f'  ✓ Created {len(channels)} TemporaryChannel records'))

    def generate_legal_person_offline(self, count):
        """Generate LegalPersonOffline records"""
        self.stdout.write('Creating LegalPersonOffline records...')
        first_names = ['Tanaka', 'Suzuki', 'Takahashi', 'Watanabe', 'Yamamoto', 'Nakamura']
        last_names = ['Taro', 'Jiro', 'Hanako', 'Yuki', 'Akira', 'Kenji']

        records = []
        for i in range(count):
            record = LegalPersonOffline.objects.create(
                username=f'{random.choice(first_names)}{random.choice(last_names)}',
                appointment_time=self.random_datetime(30, -30),
                visit_time=self.random_datetime(30, 0)
            )
            records.append(record)
        self.stdout.write(self.style.SUCCESS(f'  ✓ Created {len(records)} LegalPersonOffline records'))

    def generate_ec_sites(self, count):
        """Generate EcSite records"""
        self.stdout.write('Creating EcSite records...')
        methods = ['Apple Store Online', 'Amazon', 'Rakuten', 'Yahoo Shopping']

        sites = []
        for i in range(count):
            site = EcSite.objects.create(
                reservation_number=f'EC-{random.randint(100000, 999999)}',
                username=f'user{random.randint(1000, 9999)}@example.com',
                method=random.choice(methods),
                reservation_time=self.random_datetime(60, 30),
                visit_time=self.random_datetime(30, 0),
                order_detail_url=f'https://example.com/order/{random.randint(100000, 999999)}'
            )
            sites.append(site)
        self.stdout.write(self.style.SUCCESS(f'  ✓ Created {len(sites)} EcSite records'))

    def generate_official_accounts(self, count):
        """Generate OfficialAccount records"""
        self.stdout.write('Creating OfficialAccount records...')
        prefixes = ['tokyo', 'osaka', 'kyoto', 'fukuoka', 'sapporo']

        accounts = []
        for i in range(count):
            prefix = random.choice(prefixes)
            account = OfficialAccount.objects.create(
                account_id=f'{prefix}{random.randint(1000, 9999)}',
                email=f'{prefix}{i+1}@example.com',
                name=f'Test User {i+1}',
                postal_code=f'{random.randint(100, 999)}-{random.randint(1000, 9999)}',
                address_line_1=f'{random.randint(1, 50)}-{random.randint(1, 20)} Chome',
                address_line_2=f'{random.choice(["Shibuya", "Shinjuku", "Minato", "Chiyoda"])}-ku',
                address_line_3='Tokyo',
                passkey=f'pass{random.randint(10000, 99999)}'
            )
            accounts.append(account)
        self.stdout.write(self.style.SUCCESS(f'  ✓ Created {len(accounts)} OfficialAccount records'))

    def generate_purchasing_orders(self, count):
        """Generate Purchasing records"""
        self.stdout.write('Creating Purchasing records...')
        accounts = list(OfficialAccount.objects.all())

        orders = []
        for i in range(count):
            status = random.choice(['pending_confirmation', 'shipped', 'in_delivery', 'delivered'])
            created = self.random_datetime(60, 30)
            confirmed = created + timedelta(hours=random.randint(1, 24)) if status != 'pending_confirmation' else None
            shipped = confirmed + timedelta(days=random.randint(1, 3)) if confirmed and status in ['shipped', 'in_delivery', 'delivered'] else None

            order = Purchasing.objects.create(
                order_number=f'W{random.randint(100000000, 999999999)}',
                official_account=random.choice(accounts) if accounts else None,
                confirmed_at=confirmed,
                shipped_at=shipped,
                estimated_website_arrival_date=(timezone.now() + timedelta(days=random.randint(5, 15))).date(),
                tracking_number=f'{random.randint(1000000000000, 9999999999999)}' if shipped else '',
                estimated_delivery_date=(timezone.now() + timedelta(days=random.randint(3, 10))).date() if shipped else None,
                delivery_status=status,
                last_info_updated_at=self.random_datetime(7, 0),
                account_used=f'account{random.randint(1, 100)}@apple.com',
                payment_method=random.choice(['credit_card', 'gift_card', 'card', 'backup'])
            )
            # Set created_at manually
            order.created_at = created
            order.save(update_fields=['created_at'])
            orders.append(order)
        self.stdout.write(self.style.SUCCESS(f'  ✓ Created {len(orders)} Purchasing records'))

    def generate_gift_cards(self, count):
        """Generate GiftCard records"""
        self.stdout.write('Creating GiftCard records...')
        purchasings = list(Purchasing.objects.all())

        cards = []
        for i in range(count):
            card = GiftCard.objects.create(
                card_number=f'GC{random.randint(1000000000000000, 9999999999999999)}',
                passkey1=f'{random.randint(1000, 9999)}',
                passkey2=f'{random.randint(1000, 9999)}',
                balance=random.randint(1000, 50000)
            )
            # Associate with some purchasing orders
            if purchasings:
                card.purchasings.set(random.sample(purchasings, min(random.randint(0, 3), len(purchasings))))
            cards.append(card)
        self.stdout.write(self.style.SUCCESS(f'  ✓ Created {len(cards)} GiftCard records'))

    def generate_debit_cards(self, count):
        """Generate DebitCard records"""
        self.stdout.write('Creating DebitCard records...')

        cards = []
        for i in range(count):
            card = DebitCard.objects.create(
                card_number=f'{random.randint(4000, 4999)}{random.randint(1000, 9999)}{random.randint(1000, 9999)}{random.randint(1000, 9999)}',
                expiry_month=random.randint(1, 12),
                expiry_year=random.randint(2025, 2030),
                passkey=f'{random.randint(100, 999)}',
                balance=Decimal(str(random.randint(10000, 500000))),
                last_balance_update=self.random_datetime(30, 0)
            )
            cards.append(card)
        self.stdout.write(self.style.SUCCESS(f'  ✓ Created {len(cards)} DebitCard records'))

    def generate_credit_cards(self, count):
        """Generate CreditCard records"""
        self.stdout.write('Creating CreditCard records...')

        cards = []
        for i in range(count):
            card = CreditCard.objects.create(
                card_number=f'{random.randint(5000, 5999)}{random.randint(1000, 9999)}{random.randint(1000, 9999)}{random.randint(1000, 9999)}',
                expiry_month=random.randint(1, 12),
                expiry_year=random.randint(2025, 2030),
                passkey=f'{random.randint(100, 999)}',
                credit_limit=Decimal(str(random.randint(100000, 1000000))),
                last_balance_update=self.random_datetime(30, 0)
            )
            cards.append(card)
        self.stdout.write(self.style.SUCCESS(f'  ✓ Created {len(cards)} CreditCard records'))

    def generate_debit_card_payments(self, count):
        """Generate DebitCardPayment records"""
        self.stdout.write('Creating DebitCardPayment records...')
        debit_cards = list(DebitCard.objects.all())
        purchasings = list(Purchasing.objects.all())

        if not debit_cards or not purchasings:
            self.stdout.write(self.style.WARNING('  ⚠ No debit cards or purchasing orders available, skipping'))
            return

        payments = []
        for i in range(count):
            payment = DebitCardPayment.objects.create(
                debit_card=random.choice(debit_cards),
                purchasing=random.choice(purchasings),
                payment_amount=Decimal(str(random.randint(50000, 300000))),
                payment_status=random.choice(['pending', 'completed', 'failed', 'refunded'])
            )
            payments.append(payment)
        self.stdout.write(self.style.SUCCESS(f'  ✓ Created {len(payments)} DebitCardPayment records'))

    def generate_credit_card_payments(self, count):
        """Generate CreditCardPayment records"""
        self.stdout.write('Creating CreditCardPayment records...')
        credit_cards = list(CreditCard.objects.all())
        purchasings = list(Purchasing.objects.all())

        if not credit_cards or not purchasings:
            self.stdout.write(self.style.WARNING('  ⚠ No credit cards or purchasing orders available, skipping'))
            return

        payments = []
        for i in range(count):
            payment = CreditCardPayment.objects.create(
                credit_card=random.choice(credit_cards),
                purchasing=random.choice(purchasings),
                payment_amount=Decimal(str(random.randint(50000, 300000))),
                payment_status=random.choice(['pending', 'completed', 'failed', 'refunded'])
            )
            payments.append(payment)
        self.stdout.write(self.style.SUCCESS(f'  ✓ Created {len(payments)} CreditCardPayment records'))

    def generate_inventory(self, count):
        """Generate Inventory records"""
        self.stdout.write('Creating Inventory records...')
        iphones = list(iPhone.objects.all())
        ipads = list(iPad.objects.all())
        products = iphones + ipads

        ec_sites = list(EcSite.objects.all())
        purchasings = list(Purchasing.objects.all())
        legal_persons = list(LegalPersonOffline.objects.all())
        temp_channels = list(TemporaryChannel.objects.all())

        if not products:
            self.stdout.write(self.style.WARNING('  ⚠ No products available, skipping'))
            return

        inventories = []
        for i in range(count):
            product = random.choice(products)
            status = random.choice(['in_transit', 'arrived', 'out_of_stock', 'abnormal'])

            # Random source selection
            source_type = random.randint(1, 4)
            source1 = random.choice(ec_sites) if source_type == 1 and ec_sites else None
            source2 = random.choice(purchasings) if source_type == 2 and purchasings else None
            source3 = random.choice(legal_persons) if source_type == 3 and legal_persons else None
            source4 = random.choice(temp_channels) if source_type == 4 and temp_channels else None

            scheduled = self.random_datetime(30, -15)
            actual = scheduled + timedelta(days=random.randint(-2, 5)) if status in ['arrived', 'out_of_stock'] else None

            inventory = Inventory.objects.create(
                flag=f'INV-{i+1:05d}',
                iphone=product if isinstance(product, iPhone) else None,
                ipad=product if isinstance(product, iPad) else None,
                source1=source1,
                source2=source2,
                source3=source3,
                source4=source4,
                transaction_confirmed_at=self.random_datetime(60, 30),
                scheduled_arrival_at=scheduled,
                checked_arrival_at_1=scheduled + timedelta(days=random.randint(-1, 1)) if random.random() > 0.5 else None,
                checked_arrival_at_2=scheduled + timedelta(days=random.randint(-1, 2)) if random.random() > 0.3 else None,
                actual_arrival_at=actual,
                status=status
            )
            inventories.append(inventory)
        self.stdout.write(self.style.SUCCESS(f'  ✓ Created {len(inventories)} Inventory records'))
