"""Views of api app."""
from datetime import datetime
from random import randint

import redis
import json
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from .models import Reminder, SatelliteAcqusition
from .serializers import ReminderSerializer, LandsatSearchSerializer, SatelliteAcqusitionSerializer

r = redis.Redis(host='redis', port=6379, db=0)

def get_thumbnail(id):
    url = 'https://landsatlook.usgs.gov/gen-browse?size=rrb&type=refl&product_id='

    data = id.split('_')
    if data[0] == 'LC09':
        data[4] = data[3]
    data[1] = 'L1TP'
    data.pop(-1)
    new_id = '_'.join(data)

    return url+new_id


@swagger_auto_schema(
    method='post',
    operation_description="Retrieve scenes from Landsat based on time range, location, and cloud cover percentage.",
    request_body=LandsatSearchSerializer,
    responses={
        200: openapi.Response(
            'Success', 
            openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'count': openapi.Schema(type=openapi.TYPE_INTEGER, description='Number of scenes found'),
                    'scenes': openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        items=openapi.Schema(
                            type=openapi.TYPE_OBJECT
                        )
                    )
                }
            )
        ),
        400: openapi.Response('Bad request'),
        401: 'Unauthorized',
    },
    operation_summary="Retrieve Landsat scenes based on search parameters",
    tags=['Scenes']
)
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def scenes(request):
    """Get scenes."""
    serializer = LandsatSearchSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    time_range = serializer.validated_data['time_range']
    latitude = serializer.validated_data['latitude']
    longitude = serializer.validated_data['longitude']
    min_cloud_cover = serializer.validated_data.get('min_cloud_cover', 0)
    max_cloud_cover = serializer.validated_data.get('max_cloud_cover', 100)
    request_id = randint(100000, 999999)

    task = {
        "request_id": request_id,
        "lon": longitude,
        "lat": latitude,
        "min_cloud": min_cloud_cover,
        "max_cloud": max_cloud_cover,
        "time_range": time_range,
    }

    r.lpush("request_queue", json.dumps(task))

    return Response({"status": "request_sent", "request_id": request_id},
                    status=status.HTTP_202_ACCEPTED)


@swagger_auto_schema(
    methods=['get'],
    manual_parameters=[
        openapi.Parameter(
            'request_id',
            openapi.IN_QUERY,
            description="ID of the request to check the status of the scene.",
            type=openapi.TYPE_STRING,
            required=True
        ),
    ],
    responses={
        200: 'Successful Response',
        202: 'In Progress',
        400: 'Bad Request',
        401: 'Unauthorized',
    },
    operation_description="Checks the status of the requested scenes by their request ID.",
    operation_summary="Get Scene Request Status",
    tags=['Scenes']
)
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def scenes_request_status(request):
    request_id = request.GET.get('request_id')

    result = r.get(f"result:{request_id}")

    if result:
        data = json.loads(result)
        items = []
        for item in data:
            properties = item.get('properties', {})
            assets = item.get('assets', {})

            items.append({
                "id": item.get('id'),
                "cloud_cover": properties.get('eo:cloud_cover'),
                "scene_datetime": properties.get('datetime'),
                "platform": properties.get('platform'),
                'wrs_path': properties.get('landsat:wrs_path'),
                'wrs_row': properties.get('landsat:wrs_row'),
                "sun_azimuth": properties.get('view:sun_azimuth'),
                "sun_elevation": properties.get('view:sun_elevation'),
                "thumbnail": get_thumbnail(item.get('id')),
            })

        return Response({
            "count": len(items),
            "products": items
        })
    else:
        return Response({"status": "in_progress"}, status=status.HTTP_202_ACCEPTED)


@swagger_auto_schema(
        method='get',
        operation_description="Retrieve the current user's data.",
        responses={
            200: openapi.Response('User data retrieved successfully'),
            401: 'Unauthorized',
        },
        operation_summary="Get current user data",
        tags=['Scenes']
    )
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def scene(request):
    """Get scene."""
    return Response({}, status=status.HTTP_200_OK)


@swagger_auto_schema(
    method='get',
    manual_parameters=[
        openapi.Parameter(
            'datetime',
            openapi.IN_QUERY,
            description="Date in YYYY-MM-DD format.",
            type=openapi.TYPE_STRING,
            required=True
        ),
    ],
    responses={
        200: "A list of satellite acquisition data.",
        400: "Invalid date format.",
    },
    tags=['Scenes']
)
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def satellate_data(request):
    """Get scene."""
    dt= request.GET.get('datetime')

    if not dt:
        return Response({"error": "datetime parameter is required"}, status=status.HTTP_400_BAD_REQUEST)

    date: datetime = datetime.strptime(dt, "%Y-%m-%d")

    data = SatelliteAcqusition.objects.filter(datetime__date=dt)

    result = [{"path": item.path, "row": item.row, "satellite": item.satellite, "datetime": item.datetime} for item in data]

    return Response(result, status=status.HTTP_200_OK)


@swagger_auto_schema(
        method='get',
        operation_description="Retrieve the current user's data.",
        responses={
            200: openapi.Response('User data retrieved successfully'),
            401: 'Unauthorized',
        },
        operation_summary="Get current user data",
        tags=['Scenes']
    )
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def acquisitions(request):
    """Return the accqusitions."""
    return Response({}, status=status.HTTP_200_OK)


class ReminderViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Reminder objects.

    This ViewSet provides actions to list, create, update, and delete
    reminders for authenticated users. The reminders are filtered by
    the currently authenticated user, ensuring that users only access
    their own reminders.

    **Permissions**:
    - Only authenticated users can access this ViewSet.
    """

    queryset = Reminder.objects.all()
    serializer_class = ReminderSerializer
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        responses={
            200: openapi.Response('List of Reminders',
                                  ReminderSerializer(many=True)),
            401: 'Unauthorized'
        },
        operation_description=("Retrieve all reminders for the "
                               "authenticated user."),
        operation_summary="List Reminders",
        tags=['Reminder']
    )
    def list(self, request, *args, **kwargs):
        """Retrieve a list of reminders for the current authenticated user."""
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        responses={
            200: openapi.Response('Retrieved Reminder', ReminderSerializer),
            404: 'Not Found',
            401: 'Unauthorized'
        },
        operation_description=("Retrieve a specific reminder for the"
                               " authenticated user."),
        operation_summary="Retrieve Reminder",
        tags=['Reminder']
    )
    def retrieve(self, request, *args, **kwargs):
        """Retrieve a specific reminder for the current authenticated user."""
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        request_body=ReminderSerializer,
        responses={
            200: openapi.Response('Reminder updated successfully',
                                  ReminderSerializer),
            400: 'Bad Request',
            404: 'Not Found',
            401: 'Unauthorized'
        },
        operation_description=("Partially update an existing reminder for the "
                               "authenticated user."),
        operation_summary="Partial Update Reminder",
        tags=['Reminder']
    )
    def partial_update(self, request, *args, **kwargs):
        """Update partialy an existing reminder for the current user."""
        return super().partial_update(request, *args, **kwargs)

    @swagger_auto_schema(
        request_body=ReminderSerializer,
        responses={
            201: openapi.Response('Reminder created successfully',
                                  ReminderSerializer),
            400: 'Bad Request',
            401: 'Unauthorized'
        },
        operation_description=("Create a new reminder for the authenticated"
                               "user."),
        operation_summary="Create Reminder",
        tags=('Reminder',)
    )
    def create(self, request, *args, **kwargs):
        """Create a new reminder for the current authenticated user."""
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        request_body=ReminderSerializer,
        responses={
            200: openapi.Response('Reminder updated successfully',
                                  ReminderSerializer),
            400: 'Bad Request',
            401: 'Unauthorized'
        },
        operation_description=("Update an existing reminder for the "
                               "authenticated user."),
        operation_summary="Update Reminder",
        tags=('Reminder',)
    )
    def update(self, request, *args, **kwargs):
        """Update an existing reminder for the current authenticated user."""
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(
        responses={
            204: 'Reminder deleted successfully',
            401: 'Unauthorized'
        },
        operation_description="Delete a reminder for the authenticated user.",
        operation_summary="Delete Reminder",
        tags=('Reminder',)
    )
    def destroy(self, request, *args, **kwargs):
        """Delete a reminder for the current authenticated user."""
        return super().destroy(request, *args, **kwargs)

    def get_queryset(self):
        """Return the queryset of reminders belonging to the current user."""
        return Reminder.objects.filter(user_id=self.request.user)

    def perform_create(self, serializer):
        """Save a new reminder with the current user as the owner."""
        serializer.save(user_id=self.request.user)
