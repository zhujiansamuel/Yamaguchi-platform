# Generated manually to recreate phantom migration
# This migration adds new operation_type choices for OnlyOffice and Nextcloud operations

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('data_acquisition', '0002_historicalsynclog'),
    ]

    operations = [
        migrations.AlterField(
            model_name='historicalsynclog',
            name='operation_type',
            field=models.CharField(
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
                    ('onlyoffice_callback', 'OnlyOffice Callback'),
                    ('onlyoffice_document_processed', 'OnlyOffice Document Processed'),
                    ('onlyoffice_process_failed', 'OnlyOffice Process Failed'),
                    ('onlyoffice_import_skipped', 'OnlyOffice Import Skipped'),
                    ('onlyoffice_import_completed', 'OnlyOffice Import Completed'),
                    ('onlyoffice_missing_url', 'OnlyOffice Missing URL'),
                    ('nextcloud_forward_failed', 'Nextcloud Forward Failed'),
                ],
                max_length=30,
                verbose_name='Operation Type'
            ),
        ),
        migrations.AlterField(
            model_name='synclog',
            name='operation_type',
            field=models.CharField(
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
                    ('onlyoffice_callback', 'OnlyOffice Callback'),
                    ('onlyoffice_document_processed', 'OnlyOffice Document Processed'),
                    ('onlyoffice_process_failed', 'OnlyOffice Process Failed'),
                    ('onlyoffice_import_skipped', 'OnlyOffice Import Skipped'),
                    ('onlyoffice_import_completed', 'OnlyOffice Import Completed'),
                    ('onlyoffice_missing_url', 'OnlyOffice Missing URL'),
                    ('nextcloud_forward_failed', 'Nextcloud Forward Failed'),
                ],
                max_length=30,
                verbose_name='Operation Type'
            ),
        ),
    ]
