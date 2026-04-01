"""Проект:
разработайте Telegram-бот
с функцией календаря,
часть 1"""

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
ID = 1


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
        /read_event <название события> - чтение события
        /edit_event <название события> - редактирование события
        /delete_event <название события> - удаление события
        /display_event - вывод списка событий
        /register <логин пользователя> - регистрация пользователя
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
                      ['/display_event'],
                      ['/register']]

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
        /read_event <название события> - чтение события
        /edit_event <название события> - редактирование события
        /delete_event <название события> - удаление события
        /display_event - вывод списка событий
        /register <логин пользователя> - регистрация пользователя
        /help - выводит справку по командам
        """
                              )


# класс Calendar
class Calendar:
    def __init__(self, conn):
        self.conn = conn

    # метод create_event
    def create_event(self, event_name, event_date, event_time, event_details, tg_user_id) -> int:
        cursor = self.conn.cursor()
        cursor.execute(
        f"""INSERT
        INTO
        events(name, date, time, details, tg_user_id)
        VALUES(
            '{event_name}',
            '{event_date}',
            '{event_time}',
            '{event_details}',
            '{tg_user_id}'
            )
        RETURNING id;
        """
        )
        event_id = cursor.fetchone()[0]
        self.conn.commit()
        return event_id

    # метод read_event
    def read_event(self, event_name, tg_user_id) -> str:
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT id, name, date, time, details 
            FROM events 
            WHERE name = %s
            AND tg_user_id = %s
            """, (event_name, tg_user_id))
        row = cursor.fetchone()
        if row:
            event_id, event_name, event_date, event_time, event_details = row
            str_out = (f"Событие номер {event_id}:\nНаименование: {event_name}\nДата: {event_date}\n"
                       f"Время: {event_time}\nДетали: {event_details}")
        else:
            str_out = f"Событие c именем {event_name} не найдено"
        return str_out

    # метод display_event
    def display_event(self, tg_user_id) -> str:
        cursor = self.conn.cursor()
        cursor.execute("""
                    SELECT id, name, date, time, details 
                    FROM events
                    WHERE tg_user_id = %s
                    """, (tg_user_id,))
        rows = cursor.fetchall()
        if rows:
            str_out = ''
            for id_event, name, date, time, details in rows:
                line = f"Событие номер {id_event} | Наименование: {name}| Дата: {date} | Время: {time} | Детали: {details} \n"
                str_out = str_out + line
            return str_out
        else:
            return "События не найдены."

    # метод edit_event
    def edit_event(self, event_name,tg_user_id, new_date=None, new_description=None) -> tuple [str, int]:
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                           UPDATE events SET date = %s, details = %s WHERE name = %s AND tg_user_id = %s
                           """, (new_date, new_description, event_name, tg_user_id))
            if cursor.rowcount == 0:
                self.conn.commit()
                return "Событие не найдено.", 0
            else:
                self.conn.commit()
                return f"Обновлено строк: {cursor.rowcount}", 1
        except Exception as e:
            self.conn.rollback()
            return f"Ошибка БД: {e}", 0

    # метод delete_event
    def delete_event(self, event_name, tg_user_id) -> str:
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                           DELETE FROM events WHERE name = %s AND tg_user_id = %s 
                           """, (event_name, tg_user_id))
            if cursor.rowcount == 0:
                self.conn.commit()
                return f"Запись c именем {event_name} не найдена. Строка не удалена."
            else:
                self.conn.commit()
                return (f"Запись с именем {event_name} удалена.\n"
                        f"Удалено записей: {cursor.rowcount}")
        except Exception as e:
            self.conn.rollback()
            return f"Ошибка БД: {e}"

    # метод register
    def register(self, tg_login, tg_user_id) -> str:
        try:
            cursor = self.conn.cursor()
            cursor.execute(
            f"""INSERT
            INTO
            bot_users(tg_login, tg_user_id)
            VALUES(
                '{tg_login}',
                '{tg_user_id}'
                )
            """
            )
            if cursor.rowcount == 0:
                self.conn.commit()
                return f"Пользователь с логином {tg_login} не зарегистрирован."
            else:
                self.conn.commit()
                return f"Пользователь с логином {tg_login} зарегистрирован."
        except Exception as e:
            self.conn.rollback()
            return f"Ошибка БД: {e}"

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
            details text NOT NULL,
            tg_user_id BIGINT UNIQUE NOT NULL
        );
        """)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS bot_users (
            id serial PRIMARY KEY,
            tg_login VARCHAR(50) UNIQUE NOT NULL,
            tg_user_id BIGINT UNIQUE NOT NULL
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
                tg_user_id = update.message.from_user.id # получаем id пользователя в telegram
                # Создать событие с помощью метода create_event класса Calendar
                event_id = calendar.create_event(event_name, event_date, event_time,
                                                 event_details, tg_user_id)

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
                event_name = update.message.text.replace('/read_event', '').strip()
                await context.bot.send_message(chat_id=update.message.chat_id,
                                             text=calendar.read_event(event_name=event_name, tg_user_id=update.message.from_user.id))
            except AttributeError as error_info:
                # Отправить пользователю сообщение об ошибке
                await context.bot.send_message(chat_id=update.message.chat_id,
                                         text=f'При чтении события произошла ошибка {error_info}.')

        # Зарегистрировать обработчик, чтобы он вызывался по команде /read_event
        application.add_handler(CommandHandler('read_event', event_read_handler))

        # обработчик для редактирования событий
        async def event_edit_handler(update, context) -> int:
            try:
                event_name = update.message.text.replace('/edit_event', '').strip() # оставляем строку без пробелов в начале и конце
                context.user_data['editing_event_name'] = event_name
                await context.bot.send_message(chat_id=update.message.chat_id,
                                              text='Введите через запятую новую дату и описание события \n'
                                                   'Формат: <ГГГГ-ММ-ДД>, <Описание события>')
                return ID
            except AttributeError as error_info:
                # Отправить пользователю сообщение об ошибке
                await context.bot.send_message(chat_id=update.message.chat_id,
                                         text=f'При редактировании события произошла ошибка {error_info}.')
                return 9


        # редактирование события
        async def edit_event(update, context) -> int|range|None:
            try:
                list_par = tuple(item.strip() for item in update.message.text.split(',') if item.strip())
                if len(list_par) < 2:
                    await update.message.reply_text("Ошибка! Введите данные в формате: <ГГГГ-ММ-ДД>, <Описание события>")
                    return ID  # Остаемся в этом же состоянии, ждем корректный ввод
                res_db = calendar.edit_event(context.user_data['editing_event_name'],
                                             update.message.from_user.id,
                                             list_par[0],
                                             list_par[1] )
                # Отправить пользователю подтверждение
                if res_db[1] == 1:
                    await context.bot.send_message(chat_id=update.message.chat_id,
                                             text=f"Событие с именем {context.user_data['editing_event_name']} отредактировано.\n"
                                                  f"{res_db[0]}")
                if res_db[1] == 0:
                    await context.bot.send_message(chat_id=update.message.chat_id,
                                                   text=f"{res_db[0]}")

                # Очищаем временные данные
                context.user_data.pop('editing_event_name', None)
                return ConversationHandler.END  # завершаем диалог, чтобы команды снова работали
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
            fallbacks=[CommandHandler('cancel', cancel)],  # принудительный выход из диалога по команде
            # /cancel
        )
        application.add_handler(conv_handler_edit_event)

        # обработчик для удаления событий
        async def event_delete_handler(update, context) -> None:
            try:
                text = update.message.text.replace('/delete_event', '').strip()  # оставляем только название
                await context.bot.send_message(chat_id=update.message.chat_id,
                                             text=calendar.delete_event(text, tg_user_id=update.message.from_user.id))
            except AttributeError as error_info:
                # Отправить пользователю сообщение об ошибке
                await context.bot.send_message(chat_id=update.message.chat_id,
                                         text=f'При удалении события произошла ошибка {error_info}.')

        # Зарегистрировать обработчик, чтобы он вызывался по команде /delete_event
        application.add_handler(CommandHandler('delete_event', event_delete_handler))

        # обработчик для вывода списка событий
        async def event_display_handler(update, context) -> None:
            try:
                if calendar.display_event(tg_user_id=update.message.from_user.id,):
                    await context.bot.send_message(chat_id=update.message.chat_id,
                                             text=calendar.display_event(tg_user_id=update.message.from_user.id))
                else:
                    await context.bot.send_message(chat_id=update.message.chat_id,
                                             text='В календаре нет событий.')
            except AttributeError as error_info:
                # Отправить пользователю сообщение об ошибке
                await context.bot.send_message(chat_id=update.message.chat_id,
                                         text=f'При чтении событий календаря произошла ошибка {error_info}.')

        # Зарегистрировать обработчик, чтобы он вызывался по команде /display_event
        application.add_handler(CommandHandler('display_event', event_display_handler))

        # обработчик для регистрации пользователя
        async def register_handler(update, context) -> None:
            try:
                text = update.message.text.replace('/register', '').strip()  # оставляем только название
                await context.bot.send_message(chat_id=update.message.chat_id,
                                             text=calendar.register(text, tg_user_id=update.message.from_user.id))
            except AttributeError as error_info:
                # Отправить пользователю сообщение об ошибке
                await context.bot.send_message(chat_id=update.message.chat_id,
                                         text=f'При регистрации пользователя произошла ошибка {error_info}.')

        # Зарегистрировать обработчик, чтобы он вызывался по команде /register
        application.add_handler(CommandHandler('register', register_handler))



        # запуск бота
        application.run_polling()

    except AttributeError as err:
        logger.error(f'Произошла ошибка: {err}')

if __name__ == '__main__':
    main()
