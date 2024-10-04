"""Remind views."""
from datetime import datetime, timedelta
from random import randint

import redis
import json
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from .tasks import acqusition_remind, plan_remind
from .models import SatelliteAcqusition


@swagger_auto_schema(
    method='get',
    manual_parameters=[
        openapi.Parameter('begin_time', openapi.IN_QUERY, description="Начальное время съемки (формат ISO 8601)", type=openapi.TYPE_STRING, required=True),
        openapi.Parameter('seconds', openapi.IN_QUERY, description="Сколько секунд до съемки нужно напомнить", type=openapi.TYPE_INTEGER, required=True)
    ],
    responses={200: openapi.Response('Remind set successfully', openapi.Schema(type=openapi.TYPE_OBJECT, properties={
        'status': openapi.Schema(type=openapi.TYPE_STRING)
    }))},
    tags=['Reminders']
)
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def acqusition_remind_view(request):
    """
    Напоминание пользователю за несколько минут до начала съемки.
    
    Аргументы:
    - `begin_time`: Время начала съемки в формате ISO 8601 (например, 2024-10-04T12:00:00Z).
    - `seconds`: Сколько секунд до съемки необходимо напомнить.
    """
    try:
        begin_time = request.GET.get('begin_time')
        seconds = int(request.GET.get('seconds'))
        
        # Парсим дату начала
        date = datetime.strptime(begin_time, '%Y-%m-%dT%H:%M:%SZ')
        remind_time = date - timedelta(seconds=seconds)
        
        # Текущее время
        now = datetime.utcnow()

        # Рассчитываем разницу в секундах
        if remind_time > now:
            countdown = (remind_time - now).total_seconds()
        else:
            return Response({'status': 'Время напоминания уже прошло'}, status=status.HTTP_400_BAD_REQUEST)

        # Уведомление через Celery
        message = 'Your data is on the way'
        acqusition_remind.apply_async((message, request.user.id), countdown=int(countdown))

        return Response({'status': 'Remind set successfully'}, status=status.HTTP_200_OK)

    except ValueError:
        return Response({'error': 'Invalid time format or seconds'}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    


@swagger_auto_schema(
    method='get',
    manual_parameters=[
        openapi.Parameter(
            'satellites',
            openapi.IN_QUERY,
            description="Comma-separated list of satellite names",
            type=openapi.TYPE_STRING,
            required=True
        ),
        openapi.Parameter(
            'areas',
            openapi.IN_QUERY,
            description="List of areas in the format 'PATH|ROW,PATH|ROW'",
            type=openapi.TYPE_STRING,
            required=True
        ),
    ],
    responses={
        200: openapi.Response('Success', openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'status': openapi.Schema(type=openapi.TYPE_STRING, description='Status message'),
            }
        )),
        400: openapi.Response('Bad Request', openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'detail': openapi.Schema(type=openapi.TYPE_STRING, description='Error message'),
            }
        )),
    },
    tags=['Reminders']
)
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def plan_remind_view(request):
    satellites = request.GET.get('satellites')
    areas = request.GET.get('areas') # 'PATH|ROW,PATH|ROW'

    plan_remind.delay(request.user.id, {'satellites': satellites, 'areas': areas})

    return Response({'status': 'Message set successfully'})


@swagger_auto_schema(auto_schema=None)
@api_view(['GET'])
def plan_remind_view_new(request):
    satellites = request.GET.get('satellites', '').split(',')
    areas = request.GET.get('areas', '').split(',')
    areas = [area.split('|') for area in areas]  # Пример: ['PATH', 'ROW']
    request_day = request.GET.get('request_day')

    date = datetime.strptime(request_day, '%Y-%m-%dT%H:%M:%SZ')

    results = []
    for area in areas:
        acquisitions = SatelliteAcqusition.objects.filter(
            satellite__in=satellites,
            path=area[0],
            row=area[1],
            datetime__gt=date
        )
        results.append(acquisitions)

    data = []

    for acqs in results:
        for acq in acqs:
            data.append(
                {
                    'satellite': acq.satellite,
                    'path': acq.path,
                    'row': acq.row,
                    'datetime': acq.datetime
                }
            )

    return Response({'acquisitions': data}, status=status.HTTP_200_OK)



@swagger_auto_schema(
    method='get',
    manual_parameters=[
        openapi.Parameter(
            'pathrow',
            openapi.IN_QUERY,
            description="Path and Row in the format 'PATH|ROW', for example '160|41'",
            type=openapi.TYPE_STRING,
            required=True
        )
    ],
    responses={
        200: openapi.Response(
            description="List of acquisitions",
            examples={
                'application/json': {
                    'acquisitions': [
                        {
                            'satellite': 'Landsat-8',
                            'path': '160',
                            'row': '41',
                            'datetime': '2024-10-04T04:46:34.734275Z'
                        }
                    ]
                }
            }
        ),
        400: 'Bad Request'
    },
    tags=['Reminders']
)
@api_view(['GET'])
def get_square_acqusitions(request):
    pathrow = request.GET.get('pathrow', '').split('|')
    date = datetime.utcnow()
    satellites = 'Landsat-8,Landsat-9'.split(',')

    results = []
    acquisitions = SatelliteAcqusition.objects.filter(
        satellite__in=satellites,
        path=pathrow[0],
        row=pathrow[1],
        datetime__gt=date
    )
    results.append(acquisitions)

    data = []

    for acqs in results:
        for acq in acqs:
            data.append(
                {
                    'satellite': acq.satellite,
                    'path': acq.path,
                    'row': acq.row,
                    'datetime': acq.datetime
                }
            )

    return Response({'acquisitions': data}, status=status.HTTP_200_OK)
