# Generated manually on 2026-01-09 to add TrackingBatch and TrackingJob models

import django.db.models.deletion
import django.utils.timezone
import simple_history.models
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('data_acquisition', '0003_alter_historicalsynclog_operation_type_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='TrackingBatch',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('batch_uuid', models.UUIDField(unique=True, db_index=True, verbose_name='Batch UUID', help_text='批次唯一标识符')),
                ('task_name', models.CharField(max_length=100, db_index=True, verbose_name='Task Name', help_text='任务类型（如 official_website_redirect_to_yamato_tracking）')),
                ('file_path', models.CharField(max_length=500, verbose_name='File Path', help_text='Nextcloud 文件路径')),
                ('celery_task_id', models.CharField(max_length=255, blank=True, verbose_name='Celery Task ID', help_text='阶段二的 Celery 任务 ID')),
                ('total_jobs', models.IntegerField(default=0, verbose_name='Total Jobs', help_text='总任务数（成功创建的爬虫任务数）')),
                ('completed_jobs', models.IntegerField(default=0, verbose_name='Completed Jobs', help_text='已完成任务数')),
                ('failed_jobs', models.IntegerField(default=0, verbose_name='Failed Jobs', help_text='失败任务数')),
                ('status', models.CharField(
                    max_length=20,
                    choices=[
                        ('pending', 'Pending'),
                        ('processing', 'Processing'),
                        ('completed', 'Completed'),
                        ('partial', 'Partial Complete'),
                    ],
                    default='pending',
                    db_index=True,
                    verbose_name='Status'
                )),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True, verbose_name='Created At')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Updated At')),
                ('completed_at', models.DateTimeField(null=True, blank=True, verbose_name='Completed At', help_text='所有任务完成的时间')),
            ],
            options={
                'verbose_name': 'Tracking Batch',
                'verbose_name_plural': 'Tracking Batches',
                'db_table': 'acquisition_tracking_batch',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='HistoricalTrackingBatch',
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
                ('batch_uuid', models.UUIDField(db_index=True, verbose_name='Batch UUID', help_text='批次唯一标识符')),
                ('task_name', models.CharField(max_length=100, db_index=True, verbose_name='Task Name', help_text='任务类型（如 official_website_redirect_to_yamato_tracking）')),
                ('file_path', models.CharField(max_length=500, verbose_name='File Path', help_text='Nextcloud 文件路径')),
                ('celery_task_id', models.CharField(max_length=255, blank=True, verbose_name='Celery Task ID', help_text='阶段二的 Celery 任务 ID')),
                ('total_jobs', models.IntegerField(default=0, verbose_name='Total Jobs', help_text='总任务数（成功创建的爬虫任务数）')),
                ('completed_jobs', models.IntegerField(default=0, verbose_name='Completed Jobs', help_text='已完成任务数')),
                ('failed_jobs', models.IntegerField(default=0, verbose_name='Failed Jobs', help_text='失败任务数')),
                ('status', models.CharField(
                    max_length=20,
                    choices=[
                        ('pending', 'Pending'),
                        ('processing', 'Processing'),
                        ('completed', 'Completed'),
                        ('partial', 'Partial Complete'),
                    ],
                    default='pending',
                    db_index=True,
                    verbose_name='Status'
                )),
                ('created_at', models.DateTimeField(blank=True, editable=False, db_index=True, verbose_name='Created At')),
                ('updated_at', models.DateTimeField(blank=True, editable=False, verbose_name='Updated At')),
                ('completed_at', models.DateTimeField(null=True, blank=True, verbose_name='Completed At', help_text='所有任务完成的时间')),
                ('history_id', models.AutoField(primary_key=True, serialize=False)),
                ('history_date', models.DateTimeField(db_index=True)),
                ('history_change_reason', models.CharField(max_length=100, null=True)),
                ('history_type', models.CharField(
                    max_length=1,
                    choices=[('+', 'Created'), ('~', 'Changed'), ('-', 'Deleted')],
                )),
                ('history_user', models.ForeignKey(
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='+',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                'verbose_name': 'historical Tracking Batch',
                'verbose_name_plural': 'historical Tracking Batches',
                'ordering': ('-history_date', '-history_id'),
                'get_latest_by': ('history_date', 'history_id'),
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
        migrations.CreateModel(
            name='TrackingJob',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('batch', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='jobs',
                    to='data_acquisition.trackingbatch',
                    verbose_name='Batch',
                    help_text='所属批次'
                )),
                ('job_id', models.CharField(
                    max_length=100,
                    unique=True,
                    db_index=True,
                    blank=True,
                    verbose_name='WebScraper Job ID',
                    help_text='WebScraper 返回的 job_id（如果 API 返回了）'
                )),
                ('custom_id', models.CharField(
                    max_length=200,
                    db_index=True,
                    verbose_name='Custom ID',
                    help_text='自定义 ID，格式：{prefix}-{batch_uuid_short}-{序号}'
                )),
                ('target_url', models.TextField(
                    verbose_name='Target URL',
                    help_text='要爬取的目标 URL'
                )),
                ('index', models.IntegerField(
                    verbose_name='Index',
                    help_text='在 Excel 中的序号（从 0 开始）'
                )),
                ('status', models.CharField(
                    max_length=20,
                    choices=[
                        ('pending', 'Pending'),
                        ('completed', 'Completed'),
                        ('failed', 'Failed'),
                    ],
                    default='pending',
                    db_index=True,
                    verbose_name='Status'
                )),
                ('error_message', models.TextField(
                    blank=True,
                    verbose_name='Error Message',
                    help_text='错误信息（如果失败）'
                )),
                ('created_at', models.DateTimeField(
                    auto_now_add=True,
                    verbose_name='Created At'
                )),
                ('completed_at', models.DateTimeField(
                    null=True,
                    blank=True,
                    verbose_name='Completed At',
                    help_text='完成时间（成功或失败）'
                )),
            ],
            options={
                'verbose_name': 'Tracking Job',
                'verbose_name_plural': 'Tracking Jobs',
                'db_table': 'acquisition_tracking_job',
                'ordering': ['batch', 'index'],
            },
        ),
        migrations.CreateModel(
            name='HistoricalTrackingJob',
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
                ('job_id', models.CharField(
                    max_length=100,
                    db_index=True,
                    blank=True,
                    verbose_name='WebScraper Job ID',
                    help_text='WebScraper 返回的 job_id（如果 API 返回了）'
                )),
                ('custom_id', models.CharField(
                    max_length=200,
                    db_index=True,
                    verbose_name='Custom ID',
                    help_text='自定义 ID，格式：{prefix}-{batch_uuid_short}-{序号}'
                )),
                ('target_url', models.TextField(
                    verbose_name='Target URL',
                    help_text='要爬取的目标 URL'
                )),
                ('index', models.IntegerField(
                    verbose_name='Index',
                    help_text='在 Excel 中的序号（从 0 开始）'
                )),
                ('status', models.CharField(
                    max_length=20,
                    choices=[
                        ('pending', 'Pending'),
                        ('completed', 'Completed'),
                        ('failed', 'Failed'),
                    ],
                    default='pending',
                    db_index=True,
                    verbose_name='Status'
                )),
                ('error_message', models.TextField(
                    blank=True,
                    verbose_name='Error Message',
                    help_text='错误信息（如果失败）'
                )),
                ('created_at', models.DateTimeField(
                    blank=True,
                    editable=False,
                    verbose_name='Created At'
                )),
                ('completed_at', models.DateTimeField(
                    null=True,
                    blank=True,
                    verbose_name='Completed At',
                    help_text='完成时间（成功或失败）'
                )),
                ('history_id', models.AutoField(primary_key=True, serialize=False)),
                ('history_date', models.DateTimeField(db_index=True)),
                ('history_change_reason', models.CharField(max_length=100, null=True)),
                ('history_type', models.CharField(
                    max_length=1,
                    choices=[('+', 'Created'), ('~', 'Changed'), ('-', 'Deleted')],
                )),
                ('batch', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.DO_NOTHING,
                    db_constraint=False,
                    related_name='+',
                    to='data_acquisition.trackingbatch',
                    verbose_name='Batch',
                    help_text='所属批次'
                )),
                ('history_user', models.ForeignKey(
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='+',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                'verbose_name': 'historical Tracking Job',
                'verbose_name_plural': 'historical Tracking Jobs',
                'ordering': ('-history_date', '-history_id'),
                'get_latest_by': ('history_date', 'history_id'),
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
        # Add indexes for TrackingBatch
        migrations.AddIndex(
            model_name='trackingbatch',
            index=models.Index(fields=['task_name', 'status', '-created_at'], name='acq_track_batch_task_status_idx'),
        ),
        migrations.AddIndex(
            model_name='trackingbatch',
            index=models.Index(fields=['status', '-created_at'], name='acq_track_batch_status_idx'),
        ),
        # Add indexes for TrackingJob
        migrations.AddIndex(
            model_name='trackingjob',
            index=models.Index(fields=['batch', 'status'], name='acq_track_job_batch_status_idx'),
        ),
        migrations.AddIndex(
            model_name='trackingjob',
            index=models.Index(fields=['custom_id'], name='acq_track_job_custom_id_idx'),
        ),
    ]
