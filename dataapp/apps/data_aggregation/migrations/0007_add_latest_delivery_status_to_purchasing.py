from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('data_aggregation', '0006_historicalaggregateddata_historicalaggregationsource_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='purchasing',
            name='latest_delivery_status',
            field=models.CharField(
                blank=True,
                help_text='Latest delivery status in Japanese (max 10 characters)',
                max_length=10,
                null=True,
                verbose_name='最新送达状态',
            ),
        ),
        migrations.AddField(
            model_name='historicalpurchasing',
            name='latest_delivery_status',
            field=models.CharField(
                blank=True,
                help_text='Latest delivery status in Japanese (max 10 characters)',
                max_length=10,
                null=True,
                verbose_name='最新送达状态',
            ),
        ),
    ]
