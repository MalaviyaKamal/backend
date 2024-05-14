from django.urls import path, re_path
from .views import (
    CustomTokenObtainPairView,
    CustomTokenRefreshView,
    CustomTokenVerifyView,
    CurrentUserView,
    LogoutView,
)

urlpatterns = [
    path("jwt/create/", CustomTokenObtainPairView.as_view()),
    path("jwt/refresh/", CustomTokenRefreshView.as_view()),
    path("jwt/verify/", CustomTokenVerifyView.as_view()),
    path('current-user/', CurrentUserView.as_view(), name='current-user'),
    path("logout/", LogoutView.as_view()),
]
