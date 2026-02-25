# Generated manually for data_aggregation app

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('data_aggregation', '0001_initial'),
    ]

    operations = [
        # Add 'planned' status to Inventory.STATUS_CHOICES and update default
        migrations.AlterField(
            model_name='inventory',
            name='status',
            field=models.CharField(
                choices=[
                    ('planned', '计划中'),
                    ('in_transit', '到达中'),
                    ('arrived', '到达'),
                    ('out_of_stock', '出库'),
                    ('abnormal', '异常')
                ],
                default='planned',
                max_length=20,
                verbose_name='Status'
            ),
        ),
        # Update Purchasing.order_number to be optional (nullable and not unique)
        migrations.AlterField(
            model_name='purchasing',
            name='order_number',
            field=models.CharField(
                blank=True,
                help_text='Purchase order number',
                max_length=50,
                null=True,
                verbose_name='订单号'
            ),
        ),
    ]
