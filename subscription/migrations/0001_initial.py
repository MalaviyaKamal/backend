# Generated by Django 4.2.1 on 2024-05-23 08:39

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='UserSubscription',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('stripe_customer_id', models.CharField(db_column='stripe_customer_id', max_length=255, unique=True)),
                ('stripe_subscription_id', models.CharField(blank=True, db_column='stripe_subscription_id', max_length=255, null=True, unique=True)),
                ('stripe_price_id', models.CharField(blank=True, db_column='stripe_price_id', max_length=255, null=True)),
                ('stripe_current_period_end', models.DateTimeField(blank=True, db_column='stripe_current_period_end', null=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='subscription', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
