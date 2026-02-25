from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('data_aggregation', '0019_add_creation_source_to_purchasing'),
    ]

    operations = [
        migrations.AddField(
            model_name='purchasing',
            name='delivery_status_query_time',
            field=models.DateTimeField(
                blank=True,
                help_text='Delivery status query time',
                null=True,
                verbose_name='配送状态查询时间',
            ),
        ),
        migrations.AddField(
            model_name='purchasing',
            name='delivery_status_query_source',
            field=models.CharField(
                blank=True,
                help_text='Delivery status query source',
                max_length=100,
                null=True,
                verbose_name='配送状态查询来源',
            ),
        ),
        migrations.AddField(
            model_name='historicalpurchasing',
            name='delivery_status_query_time',
            field=models.DateTimeField(
                blank=True,
                help_text='Delivery status query time',
                null=True,
                verbose_name='配送状态查询时间',
            ),
        ),
        migrations.AddField(
            model_name='historicalpurchasing',
            name='delivery_status_query_source',
            field=models.CharField(
                blank=True,
                help_text='Delivery status query source',
                max_length=100,
                null=True,
                verbose_name='配送状态查询来源',
            ),
        ),
    ]
