# Generated manually to resolve migration conflict
# This migration was auto-generated at some point but the file was lost.
# Re-creating it to match the database state.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('data_aggregation', '0006_historicalaggregateddata_historicalaggregationsource_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='creditcard',
            name='alternative_name',
            field=models.CharField(
                blank=True,
                null=True,
                max_length=100,
                verbose_name='别名',
                help_text='Human-friendly alternative name for easy management'
            ),
        ),
        migrations.AlterField(
            model_name='debitcard',
            name='alternative_name',
            field=models.CharField(
                blank=True,
                null=True,
                max_length=100,
                verbose_name='别名',
                help_text='Human-friendly alternative name for easy management'
            ),
        ),
        migrations.AlterField(
            model_name='giftcard',
            name='alternative_name',
            field=models.CharField(
                blank=True,
                null=True,
                max_length=100,
                verbose_name='别名',
                help_text='Human-friendly alternative name for easy management'
            ),
        ),
    ]
