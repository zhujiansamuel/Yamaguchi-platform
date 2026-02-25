# Generated manually on 2026-01-03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('data_aggregation', '0003_add_payment_models_and_update_payment_method'),
    ]

    operations = [
        migrations.AddField(
            model_name='giftcard',
            name='alternative_name',
            field=models.CharField(blank=True, help_text='Human-friendly alternative name for easy management', max_length=100, verbose_name='别名'),
        ),
        migrations.AddField(
            model_name='creditcard',
            name='alternative_name',
            field=models.CharField(blank=True, help_text='Human-friendly alternative name for easy management', max_length=100, verbose_name='别名'),
        ),
        migrations.AddField(
            model_name='debitcard',
            name='alternative_name',
            field=models.CharField(blank=True, help_text='Human-friendly alternative name for easy management', max_length=100, verbose_name='别名'),
        ),
    ]
