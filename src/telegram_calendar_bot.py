import os
import sys
import logging
import django
from asgiref.sync import sync_to_async
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    filters,
)
import src.secrets as secrets

# 1. Инициализация Django (строго до импорта моделей и сервисов)
DJANGO_PROJECT_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'Calbot'))
if DJANGO_PROJECT_PATH not in sys.path:
    sys.path.append(DJANGO_PROJECT_PATH)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Calbot.settings")
django.setup()

# 2. Импорт сервисов Django ORM
from AppCalbot import services

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Шаги диалога
EDIT_DATA = 1

HELP_TEXT = """Бот для работы с событиями календаря.
Команды:
/start - запуск бота
/cancel - выход из диалога
/key_on - включение виртуальной клавиатуры
/key_off - выключение виртуальной клавиатуры
/create_event <название события> - создание события
/read_event <название события> - чтение события
/edit_event <название события> - редактирование события
/delete_event <название события> - удаление события
/display_event - вывод списка событий
/register <логин пользователя> - регистрация пользователя
/help - выводит справку по командам"""


# --- Обработчики команд ---

async def start_handler(update, context) -> None:
    tg_user_id = update.message.from_user.id
    is_new = await sync_to_async(services.check_new_user_today)(tg_user_id)
    if is_new:
        await sync_to_async(services.increment_statistic)('user_count')

    await update.message.reply_text(HELP_TEXT)


async def help_handler(update, _) -> None:
    await update.message.reply_text(HELP_TEXT)


async def key_on(update, _) -> None:
    reply_keyboard = [
        ['/start', '/help'],
        ['/create_event', '/display_event'],
        ['/read_event', '/edit_event'],
        ['/delete_event', '/register'],
        ['/key_off'],
    ]
    await update.message.reply_text(
        'Виртуальная клавиатура добавлена в бот.',
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard,
            resize_keyboard=True,
            one_time_keyboard=True,
            input_field_placeholder='Выберите команду'
        ),
    )


async def key_off(update, _) -> None:
    await update.message.reply_text(
        'Виртуальная клавиатура убрана из бота.',
        reply_markup=ReplyKeyboardRemove(),
    )


async def register_handler(update, _) -> None:
    tg_login = update.message.text.replace('/register', '').strip()
    tg_user_id = update.message.from_user.id
    result_text = await sync_to_async(services.register_telegram_user)(tg_login, tg_user_id)
    await update.message.reply_text(result_text)


async def event_create_handler(update, _) -> None:
    event_name = update.message.text.replace('/create_event', '').strip()
    tg_user_id = update.message.from_user.id
    result_text = await sync_to_async(services.create_user_event)(tg_user_id, event_name)
    await update.message.reply_text(result_text)


async def event_read_handler(update, _) -> None:
    event_name = update.message.text.replace('/read_event', '').strip()
    tg_user_id = update.message.from_user.id
    result_text = await sync_to_async(services.read_user_event)(tg_user_id, event_name)
    await update.message.reply_text(result_text)


async def event_display_handler(update, _) -> None:
    tg_user_id = update.message.from_user.id
    result_text = await sync_to_async(services.display_user_events)(tg_user_id)
    await update.message.reply_text(result_text)


async def event_delete_handler(update, _) -> None:
    event_name = update.message.text.replace('/delete_event', '').strip()
    tg_user_id = update.message.from_user.id
    result_text = await sync_to_async(services.delete_user_event)(tg_user_id, event_name)
    await update.message.reply_text(result_text)


# --- Диалог редактирования события ---

async def event_edit_start(update, context) -> int:
    event_name = update.message.text.replace('/edit_event', '').strip()
    if not event_name:
        await update.message.reply_text("Укажите название события: /edit_event <название>")
        return ConversationHandler.END

    context.user_data['editing_event_name'] = event_name
    await update.message.reply_text(
        'Введите через запятую новую дату и описание события:\n'
        'Формат: <ГГГГ-ММ-ДД>, <Описание события>'
    )
    return EDIT_DATA


async def event_edit_save(update, context) -> int:
    parts = [item.strip() for item in update.message.text.split(',', maxsplit=1) if item.strip()]
    if len(parts) < 2:
        await update.message.reply_text(
            "Ошибка! Введите данные в формате: <ГГГГ-ММ-ДД>, <Описание события>"
        )
        return EDIT_DATA

    event_name = context.user_data.pop('editing_event_name', None)
    tg_user_id = update.message.from_user.id

    # Передаем parts[0] как новую дату и parts[1] как новое описание
    result_text, _ = await sync_to_async(services.edit_user_event)(
        tg_user_id, event_name, parts[0], parts[1]
    )
    await update.message.reply_text(result_text)
    return ConversationHandler.END


async def cancel(update, context) -> int:
    context.user_data.pop('editing_event_name', None)
    await sync_to_async(services.increment_statistic)('cancelled_events')
    await update.message.reply_text('Запрос данных прерван пользователем.')
    return ConversationHandler.END


def main() -> None:
    """Запуск бота."""
    application = Application.builder().token(secrets.API_TOKEN).build()

    conv_handler_edit = ConversationHandler(
        entry_points=[CommandHandler('edit_event', event_edit_start)],
        states={
            EDIT_DATA: [MessageHandler(filters.TEXT & ~filters.COMMAND, event_edit_save)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    application.add_handler(CommandHandler('start', start_handler))
    application.add_handler(CommandHandler('help', help_handler))
    application.add_handler(CommandHandler('key_on', key_on))
    application.add_handler(CommandHandler('key_off', key_off))
    application.add_handler(CommandHandler('register', register_handler))
    application.add_handler(CommandHandler('create_event', event_create_handler))
    application.add_handler(CommandHandler('read_event', event_read_handler))
    application.add_handler(CommandHandler('display_event', event_display_handler))
    application.add_handler(CommandHandler('delete_event', event_delete_handler))
    application.add_handler(conv_handler_edit)

    application.run_polling()


if __name__ == '__main__':
    main()
