from datetime import date, time
from unittest.mock import patch

import pytest
from AppCalbot.models import Appointment, Event
from AppCalbot.services import user_invitations_to_event
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.fixture
def test_user(db):
    return User.objects.create_user(username="invitee_user", password="123")


@pytest.fixture
def test_event(db):
    return Event.objects.create(
        name="Командный синк",
        date=date(2026, 11, 20),
        time=time(14, 0),
        duration_minutes=60,
    )


@pytest.mark.django_db
def test_user_invitation_success_when_free(test_user, test_event):
    """Если слот свободен, возвращается True и создается Appointment со статусом pending."""
    busy_intervals = [
        {"date": date(2026, 11, 20), "start": time(10, 0), "end": time(11, 0)},
        {"date": date(2026, 11, 20), "start": time(16, 0), "end": time(17, 0)},
    ]

    with patch(
        "AppCalbot.services.get_user_busy_intervals",
        return_value=busy_intervals,
    ):
        result = user_invitations_to_event(test_user, test_event)

    assert result is True

    appointment = Appointment.objects.get(user=test_user, event=test_event)
    assert appointment.status == "pending"
    assert appointment.date == test_event.date
    assert appointment.time == test_event.time


@pytest.mark.django_db
def test_user_invitation_fails_when_busy(test_user, test_event):
    """Если время события попадает в занятый интервал (не первый в списке), возвращается False."""
    busy_intervals = [
        {"date": date(2026, 11, 20), "start": time(9, 0), "end": time(10, 0)},
        {"date": date(2026, 11, 20), "start": time(13, 30), "end": time(14, 30)},
    ]

    with patch(
        "AppCalbot.services.get_user_busy_intervals",
        return_value=busy_intervals,
    ):
        result = user_invitations_to_event(test_user, test_event)

    assert result is False
    assert not Appointment.objects.filter(
        user=test_user, event=test_event
    ).exists()


@pytest.mark.django_db
def test_user_invitation_success_when_no_appointments(test_user, test_event):
    """Если у пользователя вообще нет занятых интервалов, приглашение проходит успешно."""
    with patch("AppCalbot.services.get_user_busy_intervals", return_value=[]):
        result = user_invitations_to_event(test_user, test_event)

    assert result is True
    assert Appointment.objects.filter(
        user=test_user, event=test_event, status="pending"
    ).exists()
