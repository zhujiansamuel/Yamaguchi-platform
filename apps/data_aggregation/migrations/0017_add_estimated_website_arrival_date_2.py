from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('data_aggregation', '0016_add_is_extracted_to_mailmessage'),
    ]

    operations = [
        migrations.AddField(
            model_name='purchasing',
            name='estimated_website_arrival_date_2',
            field=models.DateField(
                blank=True,
                help_text='Second estimated arrival date from website',
                null=True,
                verbose_name='官网到达预计时间2',
            ),
        ),
        migrations.AddField(
            model_name='historicalpurchasing',
            name='estimated_website_arrival_date_2',
            field=models.DateField(
                blank=True,
                help_text='Second estimated arrival date from website',
                null=True,
                verbose_name='官网到达预计时间2',
            ),
        ),
    ]
