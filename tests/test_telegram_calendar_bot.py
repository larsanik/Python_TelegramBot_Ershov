import pytest
from unittest.mock import MagicMock, patch
import datetime
from src.telegram_calendar_bot import Calendar


@pytest.fixture
def calendar_with_mock_db():
    """Фикстура создает экземпляр Calendar с замоканным подключением к БД."""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    return Calendar(mock_conn), mock_conn, mock_cursor


def test_new_user_today_first_visit(calendar_with_mock_db):
    """Тест: пользователь заходит впервые за день (БД возвращает id новой записи)."""
    calendar, mock_conn, mock_cursor = calendar_with_mock_db
    mock_cursor.fetchone.return_value = (1,)  # Имитируем успешную вставку строки
    tg_user_id = 123456789

    with patch('src.telegram_calendar_bot.datetime') as mock_datetime:
        mock_datetime.datetime.now.return_value = datetime.datetime(2026, 11, 17, 15, 0, 0)
        result = calendar.new_user_today(tg_user_id)

    assert result is True
    mock_cursor.execute.assert_called_once()

    # Проверяем, что в запрос переданы правильные дата, время и ID пользователя
    args, _ = mock_cursor.execute.call_args
    assert "INSERT INTO bot_users_entry" in args[0]
    assert args[1] == ('2026-11-17', '15:00:00', tg_user_id)

    mock_conn.commit.assert_called_once()
    mock_conn.rollback.assert_not_called()


def test_new_user_today_repeat_visit(calendar_with_mock_db):
    """Тест: пользователь заходит повторно в тот же день (ON CONFLICT возвращает None)."""
    calendar, mock_conn, mock_cursor = calendar_with_mock_db
    mock_cursor.fetchone.return_value = None  # Имитируем пропуск вставки (запись уже есть)
    tg_user_id = 123456789

    result = calendar.new_user_today(tg_user_id)

    assert result is False
    mock_conn.commit.assert_called_once()
    mock_conn.rollback.assert_not_called()


def test_new_user_today_db_error(calendar_with_mock_db):
    """Тест: при ошибке БД выполняется rollback и пробрасывается исключение."""
    calendar, mock_conn, mock_cursor = calendar_with_mock_db
    mock_cursor.execute.side_effect = Exception("Ошибка соединения с PostgreSQL")
    tg_user_id = 123456789

    with pytest.raises(Exception, match="Ошибка соединения с PostgreSQL"):
        calendar.new_user_today(tg_user_id)

    mock_conn.rollback.assert_called_once()
    mock_conn.commit.assert_not_called()
