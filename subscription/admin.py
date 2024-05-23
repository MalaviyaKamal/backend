from django.contrib import admin
from .models import UserSubscription
# Register your models here.
@admin.register(UserSubscription)
class UserSubscriptionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'stripe_customer_id', 'stripe_subscription_id', 'stripe_price_id', 'stripe_current_period_end')
    list_filter = ('user', 'stripe_current_period_end')
    search_fields = ('user__email', 'stripe_customer_id', 'stripe_subscription_id', 'stripe_price_id')
