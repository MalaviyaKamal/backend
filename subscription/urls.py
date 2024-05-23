# from django.urls import path
# from .views import StripeSubscriptionView

# urlpatterns = [
#     path('subscribe/', StripeSubscriptionView.as_view(), name='subscribe'),
# ]
from django.urls import path
from .views import StripeSubscriptionView,StripeWebhookView

urlpatterns = [
    path('subscription/', StripeSubscriptionView.as_view(), name='stripe-subscription'),
    path('webhook/', StripeWebhookView.as_view(), name='stripe-webhook'),

]
