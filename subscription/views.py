from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import stripe
import json
from .models import UserSubscription
from django.conf import settings
from django.contrib.auth import get_user_model
from django.http import JsonResponse, HttpResponseBadRequest
from rest_framework.permissions import AllowAny
from datetime import datetime,timedelta
from django.utils import timezone

stripe.api_key = settings.STRIPE_SECRET_KEY
STRIPE_WEBHOOK_SECRET=settings.STRIPE_WEBHOOK_SECRET

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

            url = settings.NEXTAUTH_URL+ "/dashboard"

            if user_subscription and user_subscription.stripe_customer_id:
                stripe_session = stripe.billing_portal.Session.create(
                    customer=user_subscription.stripe_customer_id,
                    return_url=url
                )
                return Response({"url": stripe_session.url})

            stripe_session = stripe.checkout.Session.create(
                success_url=url,
                cancel_url=url,
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
                                "description": "Unlimited course generation!",
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

class StripeWebhookView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        payload = request.body.decode('utf-8')
        sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
        event = None

        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, STRIPE_WEBHOOK_SECRET
            )
        except ValueError as e:
            print(f"Invalid payload: {e}")
            return HttpResponseBadRequest(f"Invalid payload: {e}")
        except stripe.error.SignatureVerificationError as e:
            print(f"Invalid signature: {e}")
            return HttpResponseBadRequest(f"Invalid signature: {e}")

        event_type = event.get('type')
        session = event.get('data', {}).get('object', {})

        if not session:
            print("Missing session data in event")
            return HttpResponseBadRequest("Missing session data in event")

        try:
            if event_type == 'checkout.session.completed':
                self.handle_checkout_session_completed(session)
            elif event_type == 'invoice.payment_succeeded':
                self.handle_invoice_payment_succeeded(session)
            else:
                print(f"Unhandled event type: {event_type}")
                return HttpResponseBadRequest(f"Unhandled event type: {event_type}")
        except Exception as e:
            print(f"Error handling event: {e}")
            return HttpResponseBadRequest(f"Error handling event: {e}")

        return JsonResponse({'status': 'success'})

    def handle_checkout_session_completed(self, session):
        try:
            subscription = stripe.Subscription.retrieve(session['subscription'])
            user_id = session['metadata'].get('userId')
            if not user_id:
                raise ValueError("User ID not found in session metadata")

            user = User.objects.get(id=user_id)

            UserSubscription.objects.create(
                user=user,
                stripe_subscription_id=subscription.id,
                stripe_customer_id=subscription.customer,
                stripe_price_id=subscription['items']['data'][0]['price']['id'],
                stripe_current_period_end=datetime.fromtimestamp(subscription['current_period_end'])
            )
        except Exception as e:
            print(f"Error in handle_checkout_session_completed: {e}")
            raise

    def handle_invoice_payment_succeeded(self, session):
        try:
            subscription = stripe.Subscription.retrieve(session['subscription'])
            UserSubscription.objects.filter(
                stripe_subscription_id=subscription.id
            ).update(
                stripe_price_id=subscription['items']['data'][0]['price']['id'],
                stripe_current_period_end=datetime.fromtimestamp(subscription['current_period_end'])
            )
        except Exception as e:
            print(f"Error in handle_invoice_payment_succeeded: {e}")
            raise

class CheckSubscriptionView(APIView):
    
    def get_auth_session(self, request):
        user = request.user
        if user.is_authenticated:
            return user
        return None

    def get(self, request):
        user = self.get_auth_session(request)
        if not user:
            return Response({"detail": "Unauthorized"}, status=status.HTTP_401_UNAUTHORIZED)
        
        try:
            user_subscription = UserSubscription.objects.filter(user=user).first()
            if not user_subscription:
                return Response({"isValid": False, "next_billing_date": None})

            DAY_IN_MS = timedelta(days=1)
            current_time = timezone.now()

            is_valid = (
                user_subscription.stripe_price_id and
                user_subscription.stripe_current_period_end and
                (user_subscription.stripe_current_period_end + DAY_IN_MS) > current_time
            )

            next_billing_date = user_subscription.stripe_current_period_end + DAY_IN_MS if user_subscription.stripe_current_period_end else None

            return Response({
                "isValid": bool(is_valid),
                "next_billing_date": next_billing_date
            })

        except Exception as e:
            print(f"Error checking subscription: {e}")
            return Response({"detail": "Internal Server Error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)