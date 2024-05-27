from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
    
)
from datetime import datetime,timedelta
from rest_framework.permissions import IsAuthenticated,IsAuthenticatedOrReadOnly
from .serializers import UserAccountSerializer
from rest_framework.generics import RetrieveUpdateDestroyAPIView
from .models import UserAccount

class CustomTokenObtainPairView(TokenObtainPairView):
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)

        if response.status_code == 200:
            access_token = response.data.get("access")
            refresh_token = response.data.get("refresh")

            response.set_cookie(
                "access",
                access_token,
                max_age=settings.AUTH_COOKIE_MAX_AGE,
                path=settings.AUTH_COOKIE_PATH,
                secure=settings.AUTH_COOKIE_SECURE,
                httponly=settings.AUTH_COOKIE_HTTP_ONLY,
                samesite=settings.AUTH_COOKIE_SAMESITE,
            )
            response.set_cookie(
                "refresh",
                refresh_token,
                max_age=settings.AUTH_COOKIE_MAX_AGE,
                path=settings.AUTH_COOKIE_PATH,
                secure=settings.AUTH_COOKIE_SECURE,
                httponly=settings.AUTH_COOKIE_HTTP_ONLY,
                samesite=settings.AUTH_COOKIE_SAMESITE,
            )

        return response


class CustomTokenRefreshView(TokenRefreshView):
    def post(self, request, *args, **kwargs):
        refresh_token = request.COOKIES.get("refresh")

        if refresh_token:
            request.data["refresh"] = refresh_token

        response = super().post(request, *args, **kwargs)

        if response.status_code == 200:
            access_token = response.data.get("access")

            response.set_cookie(
                "access",
                access_token,
                max_age=settings.AUTH_COOKIE_MAX_AGE,
                path=settings.AUTH_COOKIE_PATH,
                secure=settings.AUTH_COOKIE_SECURE,
                httponly=settings.AUTH_COOKIE_HTTP_ONLY,
                samesite=settings.AUTH_COOKIE_SAMESITE,
            )

        return response


class CustomTokenVerifyView(TokenVerifyView):
    def post(self, request, *args, **kwargs):
        access_token = request.COOKIES.get("access")

        if access_token:
            request.data["token"] = access_token

        return super().post(request, *args, **kwargs)

class CurrentUserView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserAccountSerializer(request.user)
        return Response(serializer.data)

class LogoutView(APIView):
    def post(self, request, *args, **kwargs):
        response = Response(status=status.HTTP_204_NO_CONTENT)
        # response.delete_cookie("access")
        # response.delete_cookie("refresh")
        past_date = datetime.utcnow() - timedelta(days=10)
        response.set_cookie(
            "access",
            "",
            max_age=0,
            path=settings.AUTH_COOKIE_PATH,
            secure=settings.AUTH_COOKIE_SECURE,
            httponly=settings.AUTH_COOKIE_HTTP_ONLY,
            samesite=settings.AUTH_COOKIE_SAMESITE,
        )
        response.set_cookie(
            "refresh",
            "",
            max_age=0,
            path=settings.AUTH_COOKIE_PATH,
            secure=settings.AUTH_COOKIE_SECURE,
            httponly=settings.AUTH_COOKIE_HTTP_ONLY,
            samesite=settings.AUTH_COOKIE_SAMESITE,
        )
        return response
    


class UserProfile(RetrieveUpdateDestroyAPIView):
    queryset = UserAccount.objects.all()
    serializer_class = UserAccountSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_object(self):
        # Return the currently authenticated user
        return self.request.user

    def retrieve(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            serializer = self.get_serializer(request.user)
            return Response(serializer.data)
        else:
            return Response("Not authenticated", status=status.HTTP_401_UNAUTHORIZED)

    def perform_update(self, serializer):
        serializer.save()
        return super().perform_update(serializer)

    def delete(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.is_deleted = True
        instance.save()
        return Response(status=status.HTTP_204_NO_CONTENT)