# Generated by Django 5.2.1 on 2025-05-23 18:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0002_alter_subscription_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='subscription',
            name='screenshot',
            field=models.ImageField(blank=True, null=True, upload_to='screenshot/'),
        ),
    ]
