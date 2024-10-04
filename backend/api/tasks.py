"""Tasks of the api app."""
import sqlite3
from datetime import datetime
from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from django.contrib.auth import get_user_model
import requests

User = get_user_model()


@shared_task
def acqusition_remind(message, user_id):
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        print(f"User with id {user_id} does not exist")
    send_mail(
            'Confirm your email',
            message,
            settings.EMAIL_HOST_USER,
            [user.email],
            fail_silently=False,
        )
    
@shared_task(bind=True)
def plan_remind(self, user_id, data, attempt=1, now=None):
    if attempt >= 72:
        return  # Завершить задачу после 24 попыток

    if now is None:
        now = datetime.utcnow()  # Текущее время по UTC

    now = now.strftime('%Y-%m-%dT%H:%M:%SZ')

    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        print(f"User with id {user_id} does not exist")
        return
    
    params = {
        'satellites': data['satellites'],
        'areas': data['areas'],
        'request_day': now
    }
    response = requests.get(f'http://backend:8000/api/v1/reminders/plan_remind_extra/', params=params)

    results = response.json()['acquisitions']
    if results:
        # Формируем сообщение для каждого найденного результата
        message = "Upcoming satellite acquisitions:\n"
        for data in results:
            message += f"- Satellite {data['satellite']} will acquire data on {data['datetime']} for path {data['path']}, row {data['row']}.\n"

        send_mail(
            'Satellite Acquisition Reminder',
            message,
            settings.EMAIL_HOST_USER,
            [user.email],
            fail_silently=False,
        )
        return

    # Если данные не найдены, планируем следующую попытку через 3 часа
    self.apply_async((user_id, data, attempt + 1, now), countdown=3600 * 3)