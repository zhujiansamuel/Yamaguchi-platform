from django.db import migrations, models
import apps.data_aggregation.models


class Migration(migrations.Migration):

    dependencies = [
        ('data_aggregation', '0017_add_estimated_website_arrival_date_2'),
    ]

    operations = [
        migrations.CreateModel(
            name='OrderConflict',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.CharField(
                    default=apps.data_aggregation.models.generate_uuid,
                    help_text='48-character globally unique identifier',
                    max_length=59,
                    unique=True,
                    verbose_name='UUID',
                )),
                ('created_at', models.DateTimeField(
                    auto_now_add=True,
                    help_text='When this conflict record was created',
                    verbose_name='创建时间',
                )),
                ('is_processed', models.BooleanField(
                    default=False,
                    help_text='Whether this conflict has been processed/resolved',
                    verbose_name='已处理',
                )),
                ('purchasing', models.OneToOneField(
                    help_text='The purchasing order associated with this conflict',
                    on_delete=models.deletion.PROTECT,
                    related_name='conflict',
                    to='data_aggregation.purchasing',
                    verbose_name='订单',
                )),
            ],
            options={
                'verbose_name': 'Order Conflict',
                'verbose_name_plural': 'Order Conflicts',
                'db_table': 'order_conflict',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='OrderConflictField',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.CharField(
                    default=apps.data_aggregation.models.generate_uuid,
                    help_text='48-character globally unique identifier',
                    max_length=59,
                    unique=True,
                    verbose_name='UUID',
                )),
                ('field_name', models.CharField(
                    help_text='Name of the conflicting field (e.g., order_number, delivery_status)',
                    max_length=100,
                    verbose_name='冲突字段名',
                )),
                ('old_value', models.CharField(
                    blank=True,
                    help_text='The original/existing value of the field',
                    max_length=255,
                    verbose_name='旧字段值',
                )),
                ('incoming_value', models.CharField(
                    blank=True,
                    help_text='The incoming/new value that conflicts with the existing value',
                    max_length=255,
                    verbose_name='传入字段值',
                )),
                ('source', models.CharField(
                    blank=True,
                    help_text='Source of the incoming data (e.g., API, manual import, auto sync)',
                    max_length=100,
                    verbose_name='传入途径',
                )),
                ('detected_at', models.DateTimeField(
                    help_text='When this field conflict was detected',
                    verbose_name='冲突检测时间',
                )),
                ('is_processed', models.BooleanField(
                    default=False,
                    help_text='Whether this field conflict has been processed/resolved',
                    verbose_name='已处理',
                )),
                ('order_conflict', models.ForeignKey(
                    help_text='The order conflict this field belongs to',
                    on_delete=models.deletion.CASCADE,
                    related_name='conflict_fields',
                    to='data_aggregation.orderconflict',
                    verbose_name='订单冲突',
                )),
            ],
            options={
                'verbose_name': 'Order Conflict Field',
                'verbose_name_plural': 'Order Conflict Fields',
                'db_table': 'order_conflict_field',
                'ordering': ['-detected_at'],
            },
        ),
        migrations.AddIndex(
            model_name='orderconflict',
            index=models.Index(fields=['uuid'], name='order_confl_uuid_8d71d1_idx'),
        ),
        migrations.AddIndex(
            model_name='orderconflict',
            index=models.Index(fields=['is_processed'], name='order_confl_is_proc_5e4c3a_idx'),
        ),
        migrations.AddIndex(
            model_name='orderconflict',
            index=models.Index(fields=['-created_at'], name='order_confl_created_1a2b3c_idx'),
        ),
        migrations.AddIndex(
            model_name='orderconflictfield',
            index=models.Index(fields=['uuid'], name='order_confl_uuid_4d5e6f_idx'),
        ),
        migrations.AddIndex(
            model_name='orderconflictfield',
            index=models.Index(fields=['field_name'], name='order_confl_field_n_7g8h9i_idx'),
        ),
        migrations.AddIndex(
            model_name='orderconflictfield',
            index=models.Index(fields=['is_processed'], name='order_confl_is_proc_a1b2c3_idx'),
        ),
        migrations.AddIndex(
            model_name='orderconflictfield',
            index=models.Index(fields=['-detected_at'], name='order_confl_detecte_d4e5f6_idx'),
        ),
    ]
