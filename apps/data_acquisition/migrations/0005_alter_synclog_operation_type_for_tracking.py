# Generated manually on 2026-01-09 to fix operation_type field length and add tracking operation types
# This fixes the StringDataRightTruncation error: value too long for type character varying(30)

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('data_acquisition', '0004_trackingbatch_trackingjob'),
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
                    # Tracking task operation types
                    ('official_website_redirect_to_yamato_tracking_triggered', 'OWRYT Tracking Triggered'),
                    ('official_website_redirect_to_yamato_tracking_completed', 'OWRYT Tracking Completed'),
                    ('japan_post_tracking_triggered', 'Japan Post Tracking Triggered'),
                    ('japan_post_tracking_completed', 'Japan Post Tracking Completed'),
                    ('official_website_tracking_triggered', 'Official Website Tracking Triggered'),
                    ('official_website_tracking_completed', 'Official Website Tracking Completed'),
                    ('yamato_tracking_triggered', 'Yamato Tracking Triggered'),
                    ('yamato_tracking_completed', 'Yamato Tracking Completed'),
                ],
                max_length=60,
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
                    # Tracking task operation types
                    ('official_website_redirect_to_yamato_tracking_triggered', 'OWRYT Tracking Triggered'),
                    ('official_website_redirect_to_yamato_tracking_completed', 'OWRYT Tracking Completed'),
                    ('japan_post_tracking_triggered', 'Japan Post Tracking Triggered'),
                    ('japan_post_tracking_completed', 'Japan Post Tracking Completed'),
                    ('official_website_tracking_triggered', 'Official Website Tracking Triggered'),
                    ('official_website_tracking_completed', 'Official Website Tracking Completed'),
                    ('yamato_tracking_triggered', 'Yamato Tracking Triggered'),
                    ('yamato_tracking_completed', 'Yamato Tracking Completed'),
                ],
                max_length=60,
                verbose_name='Operation Type'
            ),
        ),
    ]
