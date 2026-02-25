# Generated manually on 2026-01-16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('data_aggregation', '0015_mailaccount_official_account_link'),
    ]

    operations = [
        # 为 MailMessage 添加 is_extracted 字段
        migrations.AddField(
            model_name='mailmessage',
            name='is_extracted',
            field=models.BooleanField(
                default=False,
                help_text='Whether information has been extracted from this email',
                verbose_name='是否已提取信息'
            ),
        ),
    ]
