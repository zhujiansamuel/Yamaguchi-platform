# Generated manually for data_aggregation app

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('data_aggregation', '0002_add_planned_status_and_update_order_number'),
    ]

    operations = [
        # Change payment_method from CharField with choices to TextField
        migrations.AlterField(
            model_name='purchasing',
            name='payment_method',
            field=models.TextField(
                blank=True,
                help_text='Payment method used or unmatched payment cards info',
                verbose_name='使用付款方式'
            ),
        ),

        # Create GiftCardPayment model
        migrations.CreateModel(
            name='GiftCardPayment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('payment_amount', models.DecimalField(blank=True, decimal_places=2, help_text='Amount paid with this gift card', max_digits=12, null=True, verbose_name='支付金额')),
                ('payment_time', models.DateTimeField(auto_now_add=True, help_text='Time when the payment was made', verbose_name='支付时间')),
                ('payment_status', models.CharField(choices=[('pending', '待处理'), ('completed', '已完成'), ('failed', '失败'), ('refunded', '已退款')], default='pending', help_text='Status of the payment', max_length=20, verbose_name='支付状态')),
                ('created_at', models.DateTimeField(auto_now_add=True, help_text='Record creation time', verbose_name='Created At')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Updated At')),
                ('gift_card', models.ForeignKey(help_text='Gift card used for this payment', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='payments', to='data_aggregation.giftcard', verbose_name='Gift Card')),
                ('purchasing', models.ForeignKey(help_text='Purchasing order for this payment', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='gift_card_payments', to='data_aggregation.purchasing', verbose_name='Purchasing Order')),
            ],
            options={
                'verbose_name': 'Gift Card Payment',
                'verbose_name_plural': 'Gift Card Payments',
                'db_table': 'gift_card_payments',
                'ordering': ['-payment_time'],
            },
        ),

        # Create OtherPayment model
        migrations.CreateModel(
            name='OtherPayment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('payment_info', models.TextField(help_text='Payment information including method and card details', verbose_name='支付信息')),
                ('payment_amount', models.DecimalField(blank=True, decimal_places=2, help_text='Payment amount', max_digits=12, null=True, verbose_name='支付金额')),
                ('payment_time', models.DateTimeField(auto_now_add=True, help_text='Time when the payment was made', verbose_name='支付时间')),
                ('payment_status', models.CharField(choices=[('pending', '待处理'), ('completed', '已完成'), ('failed', '失败'), ('refunded', '已退款')], default='pending', help_text='Status of the payment', max_length=20, verbose_name='支付状态')),
                ('created_at', models.DateTimeField(auto_now_add=True, help_text='Record creation time', verbose_name='Created At')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Updated At')),
                ('purchasing', models.ForeignKey(help_text='Purchasing order for this payment', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='other_payments', to='data_aggregation.purchasing', verbose_name='Purchasing Order')),
            ],
            options={
                'verbose_name': 'Other Payment',
                'verbose_name_plural': 'Other Payments',
                'db_table': 'other_payments',
                'ordering': ['-payment_time'],
            },
        ),

        # Add indexes for GiftCardPayment
        migrations.AddIndex(
            model_name='giftcardpayment',
            index=models.Index(fields=['payment_status'], name='gift_card_p_payment_b6e8e5_idx'),
        ),
        migrations.AddIndex(
            model_name='giftcardpayment',
            index=models.Index(fields=['-payment_time'], name='gift_card_p_payment_5a1c0f_idx'),
        ),

        # Add indexes for OtherPayment
        migrations.AddIndex(
            model_name='otherpayment',
            index=models.Index(fields=['payment_status'], name='other_payme_payment_3f8e2b_idx'),
        ),
        migrations.AddIndex(
            model_name='otherpayment',
            index=models.Index(fields=['-payment_time'], name='other_payme_payment_8c7d4a_idx'),
        ),

        # Remove the old ManyToMany field from GiftCard and recreate with through
        migrations.RemoveField(
            model_name='giftcard',
            name='purchasings',
        ),
        migrations.AddField(
            model_name='giftcard',
            name='purchasings',
            field=models.ManyToManyField(
                blank=True,
                help_text='Purchasing orders associated with this gift card',
                related_name='gift_cards',
                through='data_aggregation.GiftCardPayment',
                to='data_aggregation.purchasing',
                verbose_name='Purchasing Orders'
            ),
        ),
    ]
