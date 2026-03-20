# Generated migration to create the megaglow admin user for Excel import login.

from django.db import migrations


def create_megaglow_user(apps, schema_editor):
    User = apps.get_model('auth', 'User')
    if User.objects.filter(username='megaglow').exists():
        return
    User.objects.create_user(
        username='megaglow',
        password='mega123glow',
        is_staff=True,
        is_superuser=False,
    )


def remove_megaglow_user(apps, schema_editor):
    User = apps.get_model('auth', 'User')
    User.objects.filter(username='megaglow').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0001_initial'),
        ('auth', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_megaglow_user, remove_megaglow_user),
    ]
