from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import stripe
from .models import UserSubscription
from django.conf import settings
from django.contrib.auth import get_user_model
from django.http import JsonResponse, HttpResponseBadRequest
from rest_framework.permissions import AllowAny

User = get_user_model()
def get_auth_session(request):
    user = request.user
    if user.is_authenticated:
        return user
    return None

class StripeSubscriptionView(APIView):
    def get(self, request):
        try:
            user = get_auth_session(request)
            if not user:
                return Response("Unauthorized", status=status.HTTP_401_UNAUTHORIZED)

            user_subscription = UserSubscription.objects.filter(user=user).first()

            stripe.api_key = settings.STRIPE_SECRET_KEY

            settings_url = settings.NEXTAUTH_URL + "/settings"

            # cancel at the billing portal
            if user_subscription and user_subscription.stripe_customer_id:
                stripe_session = stripe.billing_portal.Session.create(
                    customer=user_subscription.stripe_customer_id,
                    return_url=settings_url
                )
                return Response({"url": stripe_session.url})

            # user's first time subscribing
            stripe_session = stripe.checkout.Session.create(
                success_url=settings_url,
                cancel_url=settings_url,
                payment_method_types=["card"],
                mode="subscription",
                billing_address_collection="auto",
                customer_email=user.email or None,
                line_items=[
                    {
                        "price_data": {
                            "currency": "USD",
                            "product_data": {
                                "name": "Learning Journey Pro",
                                "description": "unlimited course generation!",
                            },
                            "unit_amount": 2000,
                            "recurring": {
                                "interval": "month",
                            },
                        },
                        "quantity": 1,
                    },
                ],
                metadata={
                    "userId": user.id,
                },
            )
            return Response({"url": stripe_session.url})

        except Exception as e:
            print("[STRIPE ERROR]", str(e))
            return Response("Internal Server Error", status=status.HTTP_500_INTERNAL_SERVER_ERROR)


stripe.api_key = settings.STRIPE_SECRET_KEY

class StripeWebhookView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        payload = request.body
        print("payload",payload)
        sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
        event = None

        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
            )
        except ValueError as e:
            # Invalid payload
            return HttpResponseBadRequest()
        except stripe.error.SignatureVerificationError as e:
            # Invalid signature
            return HttpResponseBadRequest()

        session = event['data']['object']

        if event['type'] == 'checkout.session.completed':
            self.handle_checkout_session_completed(session)
        elif event['type'] == 'invoice.payment_succeeded':
            self.handle_invoice_payment_succeeded(session)

        return JsonResponse({'status': 'success'})

    def handle_checkout_session_completed(self, session):
        subscription = stripe.Subscription.retrieve(session['subscription'])
        user_id = session['metadata'].get('userId')
        if not user_id:
            return HttpResponseBadRequest("User ID not found in session metadata")
        
        User = get_user_model()
        user = User.objects.get(id=user_id)

        UserSubscription.objects.create(
            user=user,
            stripe_subscription_id=subscription.id,
            stripe_customer_id=subscription.customer,
            stripe_price_id=subscription['items']['data'][0]['price']['id'],
            stripe_current_period_end=subscription['current_period_end'] * 1000
        )

    def handle_invoice_payment_succeeded(self, session):
        subscription = stripe.Subscription.retrieve(session['subscription'])
        UserSubscription.objects.filter(
            stripe_subscription_id=subscription.id
        ).update(
            stripe_price_id=subscription['items']['data'][0]['price']['id'],
            stripe_current_period_end=subscription['current_period_end'] * 1000
        )