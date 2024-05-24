
from django.urls import path
from .views import StripeSubscriptionView,StripeWebhookView,CheckSubscriptionView

urlpatterns = [
    path('subscription/', StripeSubscriptionView.as_view(), name='stripe-subscription'),
    path('webhook/', StripeWebhookView.as_view(), name='stripe-webhook'),
    path('check-subscription/', CheckSubscriptionView.as_view(), name='check-subscription'),

]
