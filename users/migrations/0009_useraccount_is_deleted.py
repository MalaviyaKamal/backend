# Generated by Django 4.2.1 on 2024-05-28 06:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0008_alter_useraccount_image'),
    ]

    operations = [
        migrations.AddField(
            model_name='useraccount',
            name='is_deleted',
            field=models.BooleanField(default=False),
        ),
    ]