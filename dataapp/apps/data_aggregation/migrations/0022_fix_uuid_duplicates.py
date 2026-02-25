from django.db import migrations
from apps.data_aggregation.models import generate_uuid

def gen_uuid(apps, schema_editor):
    EcSite = apps.get_model('data_aggregation', 'EcSite')
    for row in EcSite.objects.all():
        row.uuid = generate_uuid()
        row.save(update_fields=['uuid'])
    
    TemporaryChannel = apps.get_model('data_aggregation', 'TemporaryChannel')
    for row in TemporaryChannel.objects.all():
        row.uuid = generate_uuid()
        row.save(update_fields=['uuid'])

class Migration(migrations.Migration):

    dependencies = [
        ('data_aggregation', '0021_duplicateproduct_and_more'),
    ]

    operations = [
        migrations.RunPython(gen_uuid, reverse_code=migrations.RunPython.noop),
    ]
