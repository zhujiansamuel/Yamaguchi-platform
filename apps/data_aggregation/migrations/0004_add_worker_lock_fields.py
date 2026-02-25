# Generated migration for adding worker lock fields to Purchasing model

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('data_aggregation', '0003_add_payment_models_and_update_payment_method'),
    ]

    operations = [
        migrations.AddField(
            model_name='purchasing',
            name='is_locked',
            field=models.BooleanField(
                default=False,
                help_text='Whether this record is locked by a worker',
                verbose_name='Is Locked'
            ),
        ),
        migrations.AddField(
            model_name='purchasing',
            name='locked_at',
            field=models.DateTimeField(
                blank=True,
                help_text='Timestamp when the record was locked',
                null=True,
                verbose_name='Locked At'
            ),
        ),
        migrations.AddField(
            model_name='purchasing',
            name='locked_by_worker',
            field=models.CharField(
                blank=True,
                help_text='Name of the worker that locked this record',
                max_length=50,
                verbose_name='Locked By Worker'
            ),
        ),
        migrations.AddIndex(
            model_name='purchasing',
            index=models.Index(fields=['is_locked'], name='purchasing_is_lock_idx'),
        ),
    ]
