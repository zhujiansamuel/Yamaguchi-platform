# Generated manually on 2026-01-16

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('data_aggregation', '0014_add_email_models'),
    ]

    operations = [
        # 修改 OfficialAccount.name 字段，使其可选
        migrations.AlterField(
            model_name='officialaccount',
            name='name',
            field=models.CharField(
                blank=True,
                default='',
                help_text='Account holder name',
                max_length=50,
                verbose_name='姓名'
            ),
        ),
        # 为 MailAccount 添加 official_account 一对一关联字段
        migrations.AddField(
            model_name='mailaccount',
            name='official_account',
            field=models.OneToOneField(
                blank=True,
                help_text='Associated official account',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='mail_account',
                to='data_aggregation.officialaccount',
                verbose_name='关联官方账号'
            ),
        ),
    ]
