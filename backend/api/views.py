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
from .message_retreive import get_scene_data

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
                "id": item.get('id')[:-3],
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
    manual_parameters=[
        openapi.Parameter(
            'lat',
            openapi.IN_QUERY,
            description="Широта (lat)",
            type=openapi.TYPE_STRING,
            required=True
        ),
        openapi.Parameter(
            'lon',
            openapi.IN_QUERY,
            description="Долгота (lon)",
            type=openapi.TYPE_STRING,
            required=True
        ),
        openapi.Parameter(
            'product_id',
            openapi.IN_QUERY,
            description="Идентификатор продукта (product_id)",
            type=openapi.TYPE_STRING,
            required=True
        ),
    ],
    responses={
        200: 'Success',
        400: 'Invalid Input'
    }
)
@api_view(['GET'])
def get_scene_data_view(request):
    lat = request.GET.get('lat', None)
    lon = request.GET.get('lon', None)
    product_id = request.GET.get('product_id', None)

    # Проверка, что все параметры переданы
    if not lat or not lon or not product_id:
        return Response({"error": "Параметры lat, lon и product_id обязательны."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        # Вызов функции для получения данных сцены
        data = get_scene_data(product_id, lat, lon)
        return Response(data, status=status.HTTP_200_OK)
    except Exception as e:
        # Обработка любых ошибок
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)