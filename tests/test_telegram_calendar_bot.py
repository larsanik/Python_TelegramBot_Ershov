import pytest
from AppCalbot.models import UserDailyEntry
from AppCalbot.services import check_new_user_today


@pytest.mark.django_db
def test_check_new_user_today_first_and_repeat_visit():
    tg_user_id = 123456789

    # 1. Первый заход за сегодня должен вернуть True и создать 1 запись
    first_result = check_new_user_today(tg_user_id)
    assert first_result is True
    assert UserDailyEntry.objects.filter(tg_user_id=tg_user_id).count() == 1

    # 2. Повторный заход в этот же день должен вернуть False без дублирования записи
    second_result = check_new_user_today(tg_user_id)
    assert second_result is False
    assert UserDailyEntry.objects.filter(tg_user_id=tg_user_id).count() == 1
