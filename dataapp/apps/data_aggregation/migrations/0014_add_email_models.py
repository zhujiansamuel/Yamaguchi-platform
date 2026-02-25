# Generated manually on 2026-01-16

import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('data_aggregation', '0013_add_official_query_url_and_shipping_method'),
    ]

    operations = [
        migrations.CreateModel(
            name='MailAccount',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('provider', models.CharField(choices=[('gmail', 'Gmail'), ('imap', 'IMAP')], default='gmail', max_length=32)),
                ('email_address', models.EmailField(max_length=254, unique=True)),
                ('last_history_id', models.CharField(blank=True, default='', max_length=64)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='MailLabel',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('provider_label_id', models.CharField(max_length=128)),
                ('name', models.CharField(blank=True, default='', max_length=255)),
                ('is_system', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('account', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='labels', to='data_aggregation.mailaccount')),
            ],
        ),
        migrations.CreateModel(
            name='MailThread',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('provider_thread_id', models.CharField(max_length=128)),
                ('subject_norm', models.CharField(blank=True, default='', max_length=512)),
                ('last_message_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('account', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='threads', to='data_aggregation.mailaccount')),
            ],
        ),
        migrations.CreateModel(
            name='MailMessage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('provider_message_id', models.CharField(max_length=128)),
                ('provider_thread_id', models.CharField(blank=True, default='', max_length=128)),
                ('rfc_message_id', models.CharField(blank=True, default='', max_length=255)),
                ('date_header_at', models.DateTimeField(blank=True, null=True)),
                ('internal_at', models.DateTimeField(blank=True, null=True)),
                ('subject', models.TextField(blank=True, default='')),
                ('snippet', models.TextField(blank=True, default='')),
                ('size_estimate', models.PositiveIntegerField(default=0)),
                ('has_attachments', models.BooleanField(default=False)),
                ('from_address', models.EmailField(blank=True, default='', max_length=254)),
                ('from_name', models.CharField(blank=True, default='', max_length=255)),
                ('sender_domain', models.CharField(blank=True, default='', max_length=255)),
                ('to_recipients', models.JSONField(blank=True, default=list)),
                ('to_text', models.TextField(blank=True, default='')),
                ('raw_headers', models.JSONField(blank=True, default=dict)),
                ('ingested_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('account', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='messages', to='data_aggregation.mailaccount')),
                ('thread', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='messages', to='data_aggregation.mailthread')),
            ],
        ),
        migrations.CreateModel(
            name='MailMessageBody',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('text_plain', models.TextField(blank=True, default='')),
                ('text_html', models.TextField(blank=True, default='')),
                ('text_as_html', models.TextField(blank=True, default='')),
                ('text_normalized', models.TextField(blank=True, default='')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('message', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='body', to='data_aggregation.mailmessage')),
            ],
        ),
        migrations.CreateModel(
            name='MailMessageLabel',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('label', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='data_aggregation.maillabel')),
                ('message', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='data_aggregation.mailmessage')),
            ],
        ),
        migrations.CreateModel(
            name='MailAttachment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('provider_attachment_id', models.CharField(blank=True, default='', max_length=255)),
                ('filename', models.CharField(blank=True, default='', max_length=512)),
                ('mime_type', models.CharField(blank=True, default='', max_length=255)),
                ('size_bytes', models.PositiveIntegerField(default=0)),
                ('storage_key', models.CharField(blank=True, default='', max_length=1024)),
                ('sha256', models.CharField(blank=True, default='', max_length=64)),
                ('is_inline', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('message', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='attachments', to='data_aggregation.mailmessage')),
            ],
        ),
        migrations.AddField(
            model_name='mailmessage',
            name='labels',
            field=models.ManyToManyField(blank=True, related_name='messages', through='data_aggregation.MailMessageLabel', to='data_aggregation.maillabel'),
        ),
        migrations.AddConstraint(
            model_name='maillabel',
            constraint=models.UniqueConstraint(fields=('account', 'provider_label_id'), name='uniq_label_per_account'),
        ),
        migrations.AddConstraint(
            model_name='mailthread',
            constraint=models.UniqueConstraint(fields=('account', 'provider_thread_id'), name='uniq_thread_per_account'),
        ),
        migrations.AddConstraint(
            model_name='mailmessage',
            constraint=models.UniqueConstraint(fields=('account', 'provider_message_id'), name='uniq_message_per_account'),
        ),
        migrations.AddConstraint(
            model_name='mailmessagelabel',
            constraint=models.UniqueConstraint(fields=('message', 'label'), name='uniq_message_label'),
        ),
        migrations.AddIndex(
            model_name='maillabel',
            index=models.Index(fields=['account', 'provider_label_id'], name='data_aggreg_account_e15ee9_idx'),
        ),
        migrations.AddIndex(
            model_name='maillabel',
            index=models.Index(fields=['account', 'name'], name='data_aggreg_account_2cc41f_idx'),
        ),
        migrations.AddIndex(
            model_name='mailthread',
            index=models.Index(fields=['account', 'last_message_at'], name='data_aggreg_account_01f748_idx'),
        ),
        migrations.AddIndex(
            model_name='mailmessage',
            index=models.Index(fields=['account', '-date_header_at'], name='data_aggreg_account_22f6bb_idx'),
        ),
        migrations.AddIndex(
            model_name='mailmessage',
            index=models.Index(fields=['account', '-internal_at'], name='data_aggreg_account_3cb72e_idx'),
        ),
        migrations.AddIndex(
            model_name='mailmessage',
            index=models.Index(fields=['account', 'from_address'], name='data_aggreg_account_1bc6db_idx'),
        ),
        migrations.AddIndex(
            model_name='mailmessage',
            index=models.Index(fields=['account', 'sender_domain'], name='data_aggreg_account_c4ce7f_idx'),
        ),
        migrations.AddIndex(
            model_name='mailmessage',
            index=models.Index(fields=['account', 'provider_thread_id'], name='data_aggreg_account_e3a825_idx'),
        ),
        migrations.AddIndex(
            model_name='mailmessagelabel',
            index=models.Index(fields=['label', 'message'], name='data_aggreg_label_i_da5c5e_idx'),
        ),
        migrations.AddIndex(
            model_name='mailmessagelabel',
            index=models.Index(fields=['message', 'label'], name='data_aggreg_message_56a79c_idx'),
        ),
        migrations.AddIndex(
            model_name='mailattachment',
            index=models.Index(fields=['message'], name='data_aggreg_message_7b1e24_idx'),
        ),
        migrations.AddIndex(
            model_name='mailattachment',
            index=models.Index(fields=['mime_type'], name='data_aggreg_mime_ty_d1c0c7_idx'),
        ),
        migrations.AddIndex(
            model_name='mailattachment',
            index=models.Index(fields=['sha256'], name='data_aggreg_sha256_fb9ff5_idx'),
        ),
    ]
