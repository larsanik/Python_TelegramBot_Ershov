"""Телеграмм бот календарь
Задание #8
Чистый код
pylint & flake8"""

import logging
import datetime
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ConversationHandler
)
import src.secrets as secrets  # API_TOKEN = '<ТОКЕN>'

import psycopg

# Включение логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

# шаги ввода данных
ID = range(1)


async def cancel(update, context) -> int:
    """Выход из диалога по команде /cancel."""
    try:
        user = update.message.from_user
        logger.info(f"Пользователь {user.first_name} вышел из диалога.")
        await update.message.reply_text('Запрос данных прерван пользователем.')
        return ConversationHandler.END
    except AttributeError as err:
        logger.error(f'Произошла ошибка: {err}')
        return ConversationHandler.END


# обработчик для команды /start
async def create_start_handler(update, context):
    """Формирование сообщения пользователю по команде start."""
    try:
        msg_start = """ Бот для работы с событиями календаря.
        Команды:
        /start - запуск бота
        /cancel - выход из диалога
        /key_on - включение виртуальной клавиатуры
        /key_off - выключение виртуальной клавиатуры
        /create_event <название события> - создание события
        /read_event <номер события> - чтение события
        /edit_event <номер события> - редактирование события
        /delete_event <номер события> - удаление события
        /display_event - вывод списка событий
        /help - выводит справку по командам
        """
        await context.bot.send_message(chat_id=update.message.chat_id, text=msg_start)
    except AttributeError as err:
        # Отправить пользователю сообщение об ошибке
        await context.bot.send_message(chat_id=update.message.chat_id, text=f"Произошла ошибка: {err}")


async def key_on(update, context) -> None:
    """Добавляет виртуальную клавиатуру с командами"""
    reply_keyboard = [['/start'],
                      ['/key_off'],
                      ['/help'],
                      ['/create_event'],
                      ['/read_event'],
                      ['/edit_event'],
                      ['/delete_event'],
                      ['/display_event']]

    await update.message.reply_text(
        'Виртуальная клавиатура добавлена в бот.',
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, resize_keyboard=True, one_time_keyboard=True,
            input_field_placeholder='Выберите команду или введите ответ на запрос'
        ),
    )


async def key_off(update, context) -> None:
    """Убирает виртуальную клавиатуру с командами"""
    await update.message.reply_text(
        'Виртуальная клавиатура убрана из бота.',
        reply_markup=ReplyKeyboardRemove(),
    )


async def help_view(update, context) -> None:
    """Выводит справку по командам"""
    await update.message.reply_text(""" Бот для работы с заметками.
        Команды:
        /start - запуск бота
        /cancel - выход из диалога
        /key_on - включение виртуальной клавиатуры
        /key_off - выключение виртуальной клавиатуры
        /create_event <название события> - создание события
        /read_event <номер события> - чтение события
        /edit_event <номер события> - редактирование события
        /delete_event <номер события> - удаление события
        /display_event - вывод списка событий
        /help - выводит справку по командам
        """
                              )


# Создать класс Calendar
class Calendar:
    def __init__(self, conn):
        self.events = {} # todo убрать когда перепишу все методы под БД
        self.conn = conn

    # метод create_event
    def create_event(self, event_name, event_date, event_time, event_details) -> int:
        cursor = self.conn.cursor()
        cursor.execute(
        f"""INSERT
        INTO
        events(name, date, time, details)
        VALUES(
            '{event_name}',
            '{event_date}',
            '{event_time}',
            '{event_details}'
            )
        RETURNING id;
        """
        )
        event_id = cursor.fetchone()[0]
        self.conn.commit()
        return event_id

    # метод read_event
    def read_event(self, id_event) -> str:
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT name, date, time, details 
            FROM events 
            WHERE id = %s
            """, (id_event,))
        row = cursor.fetchone()
        if row:
            name, date, time, details = row
            str_out = f"Событие номер {id_event}:\nНаименование: {name}\nДата: {date}\nВремя: {time}\nДетали: {details}"
        else:
            str_out = f"Событие номер {id_event} не найдено"
        return str_out

    # метод display_event
    def display_event(self) -> str:
        cursor = self.conn.cursor()
        cursor.execute("""
                    SELECT id, name, date, time, details 
                    FROM events
                    """)
        rows = cursor.fetchall()
        str_out = ''
        for id_event, name, date, time, details in rows:
            line = f"Событие номер {id_event} | Наименование: {name}| Дата: {date} | Время: {time} | Детали: {details} \n"
            str_out = str_out + line
        return str_out

    # метод edit_event
    def edit_event(self, id_event, new_event_details) -> None:
        self.events[id_event]['details'] = new_event_details

    # метод delete_event
    def delete_event(self, id_event) -> str:
        del self.events[id_event]
        return f'Событие номер {id_event} удалено.'

# функция подключения к БД и создания таблицы событий, если нет
def conn_db(db_conn):
    try:
        # Подключение к базе данных
        conn = psycopg.connect(
            client_encoding=db_conn['CLIENT_ENCODING'],
            host=db_conn['HOST'],
            dbname=db_conn['DBNAME'],
            user=db_conn['USER'],
            password=db_conn['PASSWORD']
        )

        # Создание таблицы, если ее нет
        cursor = conn.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id serial PRIMARY KEY,
            name text NOT NULL,
            date date NOT NULL,
            time time NOT NULL,
            details text NOT NULL
        );
        """)
        conn.commit()
        return conn

    except Exception as err:
        logger.error(err)




def main() -> None:
    """Запуск бота."""
    try:
        # создание обработчика с токеном
        application = Application.builder().token(secrets.API_TOKEN).build()

        # обработка команды /start
        application.add_handler(CommandHandler('start', create_start_handler))

        # обработка команды /key_on
        application.add_handler(CommandHandler('key_on', key_on))

        # обработка команды /key_off
        application.add_handler(CommandHandler('key_off', key_off))

        # обработка команды /help
        application.add_handler(CommandHandler('help', help_view))

        # подключение к БД и создание таблицы, если ее нет
        conn = conn_db(secrets.DB_CONN)

        # ***************************
        # глобально доступный объект календаря
        calendar = Calendar(conn)

        # обработчик для создания событий
        async def event_create_handler(update, context) -> None:
            try:
                # Взять данные о событии из сообщения пользователя
                event_name = update.message.text[14:]
                event_date = datetime.datetime.now().strftime('%Y-%m-%d')
                event_time = datetime.datetime.now().time().strftime('%H:%M:%S')
                event_details = "Описание события"

                # Создать событие с помощью метода create_event класса Calendar
                event_id = calendar.create_event(event_name, event_date, event_time, event_details)

                # Отправить пользователю подтверждение
                await context.bot.send_message(chat_id=update.message.chat_id,
                                         text=f"Событие {event_name} создано и имеет номер {event_id}.")
            except AttributeError as error_info:
                # Отправить пользователю сообщение об ошибке
                await context.bot.send_message(chat_id=update.message.chat_id,
                                         text=f'При создании события произошла ошибка {error_info}.')

        # Зарегистрировать обработчик, чтобы он вызывался по команде /create_event
        application.add_handler(CommandHandler('create_event', event_create_handler))

        # обработчик для чтения событий
        async def event_read_handler(update, context) -> None:
            try:
                text = update.message.text.replace('/read_event', '').replace(' ', '')  # оставляем только номер
                if text.isdigit():  # проверяем, что номер события число
                    id_event = int(text)
                    await context.bot.send_message(chat_id=update.message.chat_id,
                                             text=calendar.read_event(id_event=id_event))
                else:
                    await context.bot.send_message(chat_id=update.message.chat_id,
                                             text=f'Не верный формат номера события!'
                                                  f'\nБыло введен номер события: {text}'
                                                  f'\nНомер события должен быть целым числом.')
            except AttributeError as error_info:
                # Отправить пользователю сообщение об ошибке
                await context.bot.send_message(chat_id=update.message.chat_id,
                                         text=f'При чтении события произошла ошибка {error_info}.')

        # Зарегистрировать обработчик, чтобы он вызывался по команде /read_event
        application.add_handler(CommandHandler('read_event', event_read_handler))

        # обработчик для редактирования событий
        async def event_edit_handler(update, context) -> int | range :
            try:
                text = update.message.text.replace('/edit_event', '').replace(' ', '')  # оставляем только номер
                if text.isdigit():  # проверяем, что номер события число
                    id_event = int(text)
                else:
                    id_event = 0  # так как нумерация событий начинается с 1
                if id_event in calendar.events.keys():
                    context.user_data['id_event'] = id_event
                    await context.bot.send_message(chat_id=update.message.chat_id,
                                             text='Введите новое описание события.')
                    return ID
                else:
                    await context.bot.send_message(chat_id=update.message.chat_id,
                                             text=f'Событие с номером {text} не найдено. Формат команды: '
                                                  f'/edit_event <номер события> ')
                    return 0
            except AttributeError as error_info:
                # Отправить пользователю сообщение об ошибке
                await context.bot.send_message(chat_id=update.message.chat_id,
                                         text=f'При редактировании события произошла ошибка {error_info}.')
                return 9


        # редактирование события
        async def edit_event(update, context) -> None:
            try:
                calendar.edit_event(context.user_data['id_event'], update.message.text)
                # Отправить пользователю подтверждение
                await context.bot.send_message(chat_id=update.message.chat_id,
                                         text=f"Событие {context.user_data['id_event']} отредактировано.")
            except AttributeError as error_info:
                # Отправить пользователю сообщение об ошибке
                await context.bot.send_message(chat_id=update.message.chat_id,
                                         text=f'При редактировании события произошла ошибка {error_info}.')

        # диалог для редактирования события, шаги ID, TEXT
        conv_handler_edit_event = ConversationHandler(
            entry_points=[CommandHandler('edit_event', event_edit_handler)],
            states={
                ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_event)],
            },
            fallbacks=[CommandHandler('cancel', cancel)],  # принудительный выход из диалога по команде /cancel
        )
        application.add_handler(conv_handler_edit_event)

        # обработчик для удаления событий
        async def event_delete_handler(update, context) -> None:
            try:
                text = update.message.text.replace('/delete_event', '').replace(' ', '')  # оставляем только номер
                if text.isdigit():  # проверяем, что номер события число
                    id_event = int(text)
                else:
                    id_event = 0  # так как нумерация событий начинается с 1
                if id_event in calendar.events.keys():
                    await context.bot.send_message(chat_id=update.message.chat_id,
                                             text=calendar.delete_event(id_event=id_event))
                else:
                    await context.bot.send_message(chat_id=update.message.chat_id,
                                             text=f'Событие с номером {text} не найдено. Формат команды: '
                                                  f'/delete_event <номер события> ')
            except AttributeError as error_info:
                # Отправить пользователю сообщение об ошибке
                await context.bot.send_message(chat_id=update.message.chat_id,
                                         text=f'При удалении события произошла ошибка {error_info}.')

        # Зарегистрировать обработчик, чтобы он вызывался по команде /delete_event
        application.add_handler(CommandHandler('delete_event', event_delete_handler))

        # обработчик для вывода списка событий
        async def event_display_handler(update, context) -> None:
            try:
                if True: # calendar.events: todo сделать проверку на наличие записей и откорректировать сообщения
                    await context.bot.send_message(chat_id=update.message.chat_id,
                                             text=calendar.display_event())
                else:
                    await context.bot.send_message(chat_id=update.message.chat_id,
                                             text='В календаре нет событий.')
            except AttributeError as error_info:
                # Отправить пользователю сообщение об ошибке
                await context.bot.send_message(chat_id=update.message.chat_id,
                                         text=f'При удалении события произошла ошибка {error_info}.')

        # Зарегистрировать обработчик, чтобы он вызывался по команде /delete_event
        application.add_handler(CommandHandler('display_event', event_display_handler))

        # запуск бота
        application.run_polling()

    except AttributeError as err:
        logger.error(f'Произошла ошибка: {err}')

if __name__ == '__main__':
    main()
