from datetime import datetime, timedelta
from django.contrib.auth import get_user_model
from .models import Appointment

User = get_user_model()


def get_user_busy_intervals(user, target_date=None, default_duration_minutes = 60) -> list[dict]:
    """
    Извлекает активные встречи пользователя и возвращает список занятых временных интервалов.

    :param user: объект User или ID пользователя
    :param target_date: объект datetime.date (если нужно отфильтровать конкретный день)
    :param default_duration_minutes: длительность встречи в минутах (по умолчанию 60)
    :return: список словарей вида [{'date': date, 'start': time, 'end': time, 'event': str}, ...]
    """
    # Берем только неподтвержденные и подтвержденные встречи (отмененные не занимают время)
    appointments = Appointment.objects.filter(
        user=user,
        status__in=['pending', 'confirmed']
    ).select_related('event').order_by('date', 'time')

    if target_date:
        appointments = appointments.filter(date=target_date)

    busy_intervals = []
    for app in appointments:
        start_dt = datetime.combine(app.date, app.time)
        duration = getattr(app.event, 'duration_minutes', default_duration_minutes)
        end_dt = start_dt + timedelta(minutes=duration)

        busy_intervals.append({
            'date': app.date,
            'start': app.time,
            'end': end_dt.time(),
            'event': app.event.name,
        })

    return busy_intervals
