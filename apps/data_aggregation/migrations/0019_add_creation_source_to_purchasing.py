from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('data_aggregation', '0018_add_order_conflict_models'),
    ]

    operations = [
        migrations.AddField(
            model_name='purchasing',
            name='creation_source',
            field=models.CharField(
                blank=True,
                help_text='Source of order creation (e.g., API, manual import, auto sync)',
                max_length=200,
                null=True,
                verbose_name='创建来源',
            ),
        ),
        migrations.AddField(
            model_name='historicalpurchasing',
            name='creation_source',
            field=models.CharField(
                blank=True,
                help_text='Source of order creation (e.g., API, manual import, auto sync)',
                max_length=200,
                null=True,
                verbose_name='创建来源',
            ),
        ),
    ]
