"""URL configuration of users app."""
from django.urls import path

from .views import RegisterView, VerifyEmailView

urlpatterns = [
    path('auth/signup/', RegisterView.as_view(), name='user-register'),
    path('auth/verify-email/<str:token>/', VerifyEmailView.as_view(),
         name='verify-email'),
]
