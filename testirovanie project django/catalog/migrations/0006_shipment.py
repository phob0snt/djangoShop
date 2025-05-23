# Generated by Django 5.2 on 2025-05-21 09:05

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0005_rename_can_delete_batteries_userrole_can_create_shipment_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Shipment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantity', models.PositiveIntegerField(verbose_name='Количество')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')),
                ('status', models.CharField(choices=[('created', 'Создана'), ('in_progress', 'В обработке'), ('completed', 'Завершена'), ('cancelled', 'Отменена')], default='created', max_length=20, verbose_name='Статус')),
                ('battery', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='catalog.battery', verbose_name='Товар')),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='Создал')),
            ],
            options={
                'verbose_name': 'Партия товара',
                'verbose_name_plural': 'Партии товара',
                'ordering': ['-created_at'],
            },
        ),
    ]
