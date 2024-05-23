from django.db import models
from users.models import UserAccount

class UserSubscription(models.Model):
    id = models.AutoField( primary_key=True) 
    user = models.OneToOneField(UserAccount, on_delete=models.CASCADE, related_name='subscription')
    stripe_customer_id = models.CharField(max_length=255, unique=True)
    stripe_subscription_id = models.CharField(max_length=255, unique=True, null=True, blank=True)
    stripe_price_id = models.CharField(max_length=255, null=True, blank=True)
    stripe_current_period_end = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Subscription for {self.user.email}"

