# Generated manually on 2026-01-03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('data_aggregation', '0004_add_worker_lock_fields'),
        ('data_aggregation', '0004_add_alternative_name_to_cards'),
    ]

    operations = [
        migrations.AddField(
            model_name='officialaccount',
            name='batch_encoding',
            field=models.CharField(blank=True, help_text='Batch encoding for grouping related records', max_length=100, verbose_name='批次编号'),
        ),
        migrations.AddField(
            model_name='giftcard',
            name='batch_encoding',
            field=models.CharField(blank=True, help_text='Batch encoding for grouping related records', max_length=100, verbose_name='批次编号'),
        ),
        migrations.AddField(
            model_name='debitcard',
            name='batch_encoding',
            field=models.CharField(blank=True, help_text='Batch encoding for grouping related records', max_length=100, verbose_name='批次编号'),
        ),
        migrations.AddField(
            model_name='creditcard',
            name='batch_encoding',
            field=models.CharField(blank=True, help_text='Batch encoding for grouping related records', max_length=100, verbose_name='批次编号'),
        ),
    ]
