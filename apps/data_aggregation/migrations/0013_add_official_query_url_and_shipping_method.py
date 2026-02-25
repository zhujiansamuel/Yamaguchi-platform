from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('data_aggregation', '0012_add_batch_fields_to_purchasing'),
    ]

    operations = [
        migrations.AddField(
            model_name='purchasing',
            name='official_query_url',
            field=models.URLField(
                blank=True,
                help_text='Official query URL for order tracking',
                max_length=500,
                null=True,
                verbose_name='官方查询URL',
            ),
        ),
        migrations.AddField(
            model_name='historicalpurchasing',
            name='official_query_url',
            field=models.URLField(
                blank=True,
                help_text='Official query URL for order tracking',
                max_length=500,
                null=True,
                verbose_name='官方查询URL',
            ),
        ),
        migrations.AddField(
            model_name='purchasing',
            name='shipping_method',
            field=models.CharField(
                blank=True,
                help_text='Shipping method (e.g., Standard, Express, DHL, EMS, SF Express)',
                max_length=100,
                null=True,
                verbose_name='快递方式',
            ),
        ),
        migrations.AddField(
            model_name='historicalpurchasing',
            name='shipping_method',
            field=models.CharField(
                blank=True,
                help_text='Shipping method (e.g., Standard, Express, DHL, EMS, SF Express)',
                max_length=100,
                null=True,
                verbose_name='快递方式',
            ),
        ),
    ]
