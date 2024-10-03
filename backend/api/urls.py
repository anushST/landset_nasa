"""URL configuration of api app."""
from django.urls import include, path
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions
from rest_framework.routers import DefaultRouter

from .constants import API_VERSION
from .views import acquisitions, scenes_request_status, scene, scenes, ReminderViewSet, satellate_data

router = DefaultRouter()
router.register('reminders', ReminderViewSet)

urlpatterns = [
    path(f'{API_VERSION}/', include(router.urls)),
    path(f'{API_VERSION}/satellate-data/', satellate_data, name='satellate_data'),
    path(f'{API_VERSION}/get_scenes/', scenes_request_status, name='scenes_status'),
    path(f'{API_VERSION}/pend_scenes/', scenes, name='scenes'),
    path(f'{API_VERSION}/scene/', scene, name='scene'),
    path(f'{API_VERSION}/acquisitions/', acquisitions, name='acquisitions'),
]

schema_view = get_schema_view(
    openapi.Info(
        title="Restaurant API",
        default_version='v1',
        description="Документация для приложения cats проекта Kittygram",
        # terms_of_service="URL страницы с пользовательским соглашением",
        contact=openapi.Contact(email="admin@kittygram.ru"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns += [
    path(f'{API_VERSION}/swagger/', schema_view.with_ui('swagger',
         cache_timeout=0),
         name='schema-swagger-ui'),
    path(f'{API_VERSION}/redoc/', schema_view.with_ui('redoc',
         cache_timeout=0),
         name='schema-redoc'),
]
