import pytest
from unittest.mock import AsyncMock, MagicMock
from AppCalbot.models import BotStatistics
from src.telegram_calendar_bot import help_handler, start_handler


@pytest.mark.asyncio
async def test_help_handler():
    # Создаем имитацию объектов update и context от Telegram
    update = MagicMock()
    update.message.reply_text = AsyncMock()
    context = MagicMock()

    # Вызываем асинхронный обработчик
    await help_handler(update, context)

    # Проверяем, что бот вызвал reply_text ровно 1 раз и в тексте есть нужные команды
    update.message.reply_text.assert_called_once()
    sent_text = update.message.reply_text.call_args[0][0]
    assert "/create_event" in sent_text
    assert "/display_event" in sent_text


@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
async def test_start_handler_updates_statistics():
    update = MagicMock()
    update.message.chat_id = 123456789
    update.message.from_user.id = 123456789
    update.message.from_user.username = "test_user"
    update.message.reply_text = AsyncMock()

    context = MagicMock()

    # Запускаем /start первый раз за день
    await start_handler(update, context)

    # Проверяем, что приветственное сообщение отправлено и статистика выросла на 1
    update.message.reply_text.assert_called_once()
    stat = await BotStatistics.objects.afirst()
    assert stat is not None
    assert stat.user_count == 1
