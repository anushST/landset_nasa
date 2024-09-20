"""URL configuration of users app."""
from django.urls import path

from .views import (
    LoginAPIView, RefreshTokenAPIView, RegisterView, VerifyEmailView)

urlpatterns = [
    path('auth/signup/', RegisterView.as_view(), name='user-register'),
    path('auth/login/', LoginAPIView.as_view(), name='login'),
    path('auth/token/refresh/', RefreshTokenAPIView.as_view(),
         name='token-refresh'),
    path('auth/verify-email/<str:token>/', VerifyEmailView.as_view(),
         name='verify-email'),
]
