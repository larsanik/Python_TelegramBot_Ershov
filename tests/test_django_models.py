import pytest
from datetime import date
from AppCalbot.models import BotStatistics


@pytest.mark.django_db
def test_bot_statistics_creation():
    today = date.today()
    stat = BotStatistics.objects.create(
        date=today,
        user_count=1,
        event_count=2,
        edited_events=0,
        cancelled_events=0
    )

    assert BotStatistics.objects.count() == 1
    assert stat.user_count == 1
    assert today.strftime('%d.%m.%Y') in str(stat)
