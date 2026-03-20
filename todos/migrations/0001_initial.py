# Generated migration for RestockTodo model

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='RestockTodo',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('product_name', models.CharField(help_text='Name of product to be restocked', max_length=200)),
                ('category', models.CharField(help_text='Product category', max_length=100)),
                ('quantity_needed', models.IntegerField(help_text='Number of units to restock')),
                ('estimated_cost_per_unit', models.DecimalField(decimal_places=0, help_text='Estimated cost price per unit in XAF', max_digits=10)),
                ('supplier_name', models.CharField(blank=True, help_text='Supplier name (optional)', max_length=200, null=True)),
                ('notes', models.TextField(blank=True, help_text='Additional notes about this restock task', null=True)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('completed', 'Completed'), ('postponed', 'Postponed')], default='pending', help_text='Current status of the restock task', max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True, help_text='When this todo was created')),
                ('updated_at', models.DateTimeField(auto_now=True, help_text='Last time this todo was updated')),
                ('completed_at', models.DateTimeField(blank=True, help_text='When this task was marked completed', null=True)),
            ],
            options={
                'verbose_name': 'Restock Todo',
                'verbose_name_plural': 'Restock Todos',
                'ordering': ['-created_at'],
            },
        ),
    ]
