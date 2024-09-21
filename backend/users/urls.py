"""URL configuration of users app."""
from django.urls import include, path
from rest_framework.routers import SimpleRouter

from .views import (
    LoginAPIView, UserViewSet, RefreshTokenAPIView, RegisterView,
    VerifyEmailView)

router = SimpleRouter()
router.register('users', UserViewSet, basename='user')

urlpatterns = [
    path('', include(router.urls)),
    path('auth/signup/', RegisterView.as_view(), name='user-register'),
    path('auth/login/', LoginAPIView.as_view(), name='login'),
    path('auth/token/refresh/', RefreshTokenAPIView.as_view(),
         name='token-refresh'),
    path('auth/verify-email/<str:token>/', VerifyEmailView.as_view(),
         name='verify-email'),
]
