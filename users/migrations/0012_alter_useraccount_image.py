# Generated by Django 4.2.1 on 2024-05-28 12:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0011_alter_useraccount_image'),
    ]

    operations = [
        migrations.AlterField(
            model_name='useraccount',
            name='image',
            field=models.ImageField(default='user_images/default_image.jpg', upload_to='user_images/'),
        ),
    ]