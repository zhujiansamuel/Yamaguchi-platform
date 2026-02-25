# Generated manually to recreate phantom migration
# This migration adds HistoricalSyncLog model for django-simple-history

import django.db.models.deletion
import simple_history.models
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('data_acquisition', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='HistoricalSyncLog',
            fields=[
                ('id', models.BigIntegerField(auto_created=True, blank=True, db_index=True, verbose_name='ID')),
                ('change_source', models.CharField(
                    choices=[
                        ('admin', 'Admin 管理后台'),
                        ('api', 'REST API'),
                        ('celery', 'Celery 异步任务'),
                        ('sync', 'Nextcloud 同步'),
                        ('shell', 'Django Shell/脚本'),
                        ('onlyoffice_import', 'OnlyOffice 导入'),
                        ('unknown', '未知来源'),
                    ],
                    default='unknown',
                    help_text='Source of the modification',
                    max_length=20,
                    verbose_name='修改来源',
                )),
                ('operation_type', models.CharField(
                    choices=[
                        ('webhook_received', 'Webhook Received'),
                        ('sync_started', 'Sync Started'),
                        ('sync_completed', 'Sync Completed'),
                        ('sync_failed', 'Sync Failed'),
                        ('record_created', 'Record Created'),
                        ('record_updated', 'Record Updated'),
                        ('record_deleted', 'Record Deleted'),
                        ('conflict_detected', 'Conflict Detected'),
                        ('excel_writeback', 'Excel Writeback'),
                        ('writeback_skipped', 'Writeback Skipped'),
                    ],
                    max_length=30,
                    verbose_name='Operation Type'
                )),
                ('celery_task_id', models.CharField(blank=True, max_length=255, verbose_name='Celery Task ID')),
                ('file_path', models.CharField(blank=True, max_length=500, verbose_name='File Path')),
                ('etag', models.CharField(blank=True, max_length=255, verbose_name='ETag')),
                ('message', models.TextField(help_text='Log message', verbose_name='Message')),
                ('details', models.JSONField(blank=True, default=dict, help_text='Additional details (JSON)', verbose_name='Details')),
                ('success', models.BooleanField(default=True, verbose_name='Success')),
                ('error_message', models.TextField(blank=True, verbose_name='Error Message')),
                ('created_at', models.DateTimeField(blank=True, editable=False)),
                ('history_id', models.AutoField(primary_key=True, serialize=False)),
                ('history_date', models.DateTimeField(db_index=True)),
                ('history_change_reason', models.CharField(max_length=100, null=True)),
                ('history_type', models.CharField(
                    max_length=1,
                    choices=[('+', 'Created'), ('~', 'Changed'), ('-', 'Deleted')],
                )),
                ('sync_state', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.DO_NOTHING,
                    db_constraint=False,
                    related_name='+',
                    to='data_acquisition.nextcloudsyncstate',
                    verbose_name='Sync State'
                )),
                ('history_user', models.ForeignKey(
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='+',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                'verbose_name': 'historical Sync Log',
                'verbose_name_plural': 'historical Sync Logs',
                'ordering': ('-history_date', '-history_id'),
                'get_latest_by': ('history_date', 'history_id'),
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
    ]
