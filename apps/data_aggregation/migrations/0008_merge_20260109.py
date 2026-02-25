# Generated manually to merge conflicting 0007 migrations

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('data_aggregation', '0007_add_latest_delivery_status_to_purchasing'),
        ('data_aggregation', '0007_alter_creditcard_alternative_name_and_more'),
    ]

    operations = [
        # No operations needed - this is just a merge migration to resolve
        # the conflict between two parallel 0007 migrations
    ]
