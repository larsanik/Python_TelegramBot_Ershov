from datetime import date, datetime, timedelta
from django.contrib.auth import get_user_model
from django.db.models import F
from .models import Appointment, BotStatistics, Event, TelegramUser, UserDailyEntry

User = get_user_model()


def get_django_user(tg_user_id: int):
    profile = TelegramUser.objects.select_related('user').filter(tg_user_id=tg_user_id).first()
    return profile.user if profile else None


def register_telegram_user(tg_login: str, tg_user_id: int) -> str:
    if not tg_login:
        return "Укажите логин после команды: /register <логин>"
    if TelegramUser.objects.filter(tg_user_id=tg_user_id).exists():
        return "Вы уже зарегистрированы в системе."

    user, _ = User.objects.get_or_create(username=tg_login)
    TelegramUser.objects.create(user=user, tg_user_id=tg_user_id, tg_login=tg_login)
    return f"Пользователь с логином {tg_login} зарегистрирован."


def check_new_user_today(tg_user_id: int) -> bool:
    _, created = UserDailyEntry.objects.get_or_create(
        tg_user_id=tg_user_id,
        date=date.today()
    )
    return created


def increment_statistic(field_name: str) -> None:
    today = date.today()
    BotStatistics.objects.get_or_create(
        date=today,
        defaults={'user_count': 0, 'event_count': 0, 'edited_events': 0, 'cancelled_events': 0}
    )
    BotStatistics.objects.filter(date=today).update(**{field_name: F(field_name) + 1})


def get_user_busy_intervals(user, target_date=None) -> list[dict]:
    """Извлекает активные встречи пользователя и возвращает занятые интервалы."""
    appointments = Appointment.objects.filter(
        user=user,
        status__in=['pending', 'confirmed']
    ).select_related('event').order_by('date', 'time')

    if target_date:
        appointments = appointments.filter(date=target_date)

    busy_intervals = []
    for app in appointments:
        start_dt = datetime.combine(app.date, app.time)
        end_dt = start_dt + timedelta(minutes=app.event.duration_minutes)
        busy_intervals.append({
            'date': app.date,
            'start': app.time,
            'end': end_dt.time(),
            'event': app.event.name,
        })
    return busy_intervals


# --- CRUD для встреч пользователя через бота ---

def create_user_event(tg_user_id: int, event_name: str) -> str:
    user = get_django_user(tg_user_id)
    if not user:
        return "Сначала зарегистрируйтесь через /register <логин>."
    if not event_name:
        return "Укажите название события: /create_event <название>"

    now = datetime.now()
    current_date = now.date()
    current_time = now.time().replace(microsecond=0)

    # Находим или создаем базовое событие в справочнике Event
    event, _ = Event.objects.get_or_create(
        name=event_name,
        defaults={'date': current_date, 'time': current_time, 'duration_minutes': 60}
    )

    appointment = Appointment.objects.create(
        user=user,
        event=event,
        date=current_date,
        time=current_time,
        details="Описание события",
        status='confirmed'
    )
    increment_statistic('event_count')
    return f"Событие «{event.name}» создано и имеет номер {appointment.id}."


def read_user_event(tg_user_id: int, event_name: str) -> str:
    user = get_django_user(tg_user_id)
    if not user:
        return "Сначала зарегистрируйтесь через /register <логин>."

    app = Appointment.objects.select_related('event').filter(
        user=user, event__name=event_name
    ).first()
    if not app:
        return f"Событие с именем «{event_name}» не найдено."

    return (
        f"Событие номер {app.id}:\n"
        f"Наименование: {app.event.name}\n"
        f"Дата: {app.date}\n"
        f"Время: {app.time}\n"
        f"Длительность: {app.event.duration_minutes} мин.\n"
        f"Детали: {app.details}"
    )


def display_user_events(tg_user_id: int) -> str:
    user = get_django_user(tg_user_id)
    if not user:
        return "Сначала зарегистрируйтесь через /register <логин>."

    appointments = Appointment.objects.select_related('event').filter(
        user=user
    ).exclude(status='cancelled').order_by('date', 'time')

    if not appointments:
        return "В календаре нет событий."

    lines = [
        f"Событие №{a.id} | {a.event.name} | Дата: {a.date} | Время: {a.time} | Детали: {a.details}"
        for a in appointments
    ]
    return "\n".join(lines)


def edit_user_event(tg_user_id: int, event_name: str, new_date: str, new_details: str) -> tuple[str, bool]:
    user = get_django_user(tg_user_id)
    if not user:
        return "Сначала зарегистрируйтесь через /register <логин>.", False

    updated = Appointment.objects.filter(user=user, event__name=event_name).update(
        date=new_date,
        details=new_details
    )
    if updated == 0:
        return "Событие не найдено.", False

    increment_statistic('edited_events')
    return f"Событие «{event_name}» обновлено.", True


def delete_user_event(tg_user_id: int, event_name: str) -> str:
    user = get_django_user(tg_user_id)
    if not user:
        return "Сначала зарегистрируйтесь через /register <логин>."

    deleted_count, _ = Appointment.objects.filter(user=user, event__name=event_name).delete()
    if deleted_count == 0:
        return f"Запись с именем «{event_name}» не найдена."
    return f"Запись с именем «{event_name}» удалена."
