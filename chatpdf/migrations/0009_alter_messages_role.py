# Generated by Django 4.2.1 on 2024-06-03 11:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chatpdf', '0008_pdfdocument_pdf_name'),
    ]

    operations = [
        migrations.AlterField(
            model_name='messages',
            name='role',
            field=models.CharField(choices=[('system', 'system'), ('user', 'user')], max_length=20),
        ),
    ]
