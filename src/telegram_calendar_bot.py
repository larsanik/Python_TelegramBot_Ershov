"""Проект:
разработайте Telegram-бот
с функцией календаря,
часть 2. В процессе"""

import os
import sys
import django
from datetime import date
from asgiref.sync import sync_to_async

# Настройка путей к Django проекту
DJANGO_PROJECT_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'Calbot'))
sys.path.append(DJANGO_PROJECT_PATH)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Calbot.settings")
django.setup()

# Теперь импортируем модель Django и F-выражения для атомарных обновлений
from AppCalbot.models import BotStatistics
from django.db.models import F

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


async def cancel(update, _) -> int:
    """Выход из диалога по команде /cancel."""
    try:
        user = update.message.from_user
        logger.info(f"Пользователь {user.first_name} вышел из диалога.")
        # Фиксируем отмену действий/событий в Django БД
        await increment_statistic('cancelled_events')
        await update.message.reply_text('Запрос данных прерван пользователем.')
        return ConversationHandler.END
    except AttributeError as err:
        logger.error(f'Произошла ошибка: {err}')
        return ConversationHandler.END


# обработчик для команды /start
async def create_start_handler(update, context):
    """Формирование сообщения пользователю по команде start."""
    try:
        # Увеличиваем счетчик пользователей (вызывать только если это действительно новый юзер)
        tg_user_id = update.message.from_user.id
        calendar = context.bot_data['calendar']
        if calendar.new_user_today(tg_user_id):
            await increment_statistic('user_count')

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


async def key_on(update, _) -> None:
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


async def key_off(update, _) -> None:
    """Убирает виртуальную клавиатуру с командами"""
    await update.message.reply_text(
        'Виртуальная клавиатура убрана из бота.',
        reply_markup=ReplyKeyboardRemove(),
    )


async def help_view(update, _) -> None:
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
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                    """
                    INSERT INTO events (name, date, time, details, tg_user_id)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id;
                    """,
                    (event_name, event_date, event_time, event_details, tg_user_id)
            )
            event_id = cursor.fetchone()[0]
            self.conn.commit()
            return event_id
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Ошибка БД при создании события: {e}")
            raise


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
            for id_event, name, event_date, time, details in rows:
                line = f"Событие номер {id_event} | Наименование: {name}| Дата: {event_date} | Время: {time} | Детали: {details} \n"
                str_out = str_out + line
            return str_out
        else:
            return "События не найдены."

    # метод edit_event
    def edit_event(self, event_name, tg_user_id, new_date=None, new_description=None) -> tuple[str, int]:
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

    # метод для определения суточной уникальности пользователя
    def new_user_today(self, tg_user_id: int) -> bool:
        try:
            now = datetime.datetime.now()
            enter_date = now.strftime('%Y-%m-%d')
            enter_time = now.strftime('%H:%M:%S')

            cursor = self.conn.cursor()
            cursor.execute(
                """
                INSERT INTO bot_users_entry (date, time, tg_user_id)
                VALUES (%s, %s, %s)
                ON CONFLICT (tg_user_id, date) DO NOTHING
                RETURNING id;
                """,
                (enter_date, enter_time, tg_user_id)
            )
            # Если вставка прошла (первый заход за день), вернется кортеж с id.
            # Если запись уже была — вернется None.
            inserted = cursor.fetchone()
            self.conn.commit()
            return inserted is not None

        except Exception as e:
            self.conn.rollback()
            logger.error(f"Ошибка БД при проверке входа пользователя: {e}")
            raise




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
            tg_user_id BIGINT NOT NULL
        );
        """)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS bot_users (
            id serial PRIMARY KEY,
            tg_login VARCHAR(50) UNIQUE NOT NULL,
            tg_user_id BIGINT UNIQUE NOT NULL
        );
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bot_users_entry (
            id serial PRIMARY KEY,
            date date NOT NULL,
            time time NOT NULL,
            tg_user_id BIGINT NOT NULL,
            UNIQUE (tg_user_id, date)
        );
        """)
        conn.commit()
        return conn

    except Exception as err:
        logger.error(err)


# Метод для ведения статистики
@sync_to_async
def increment_statistic(field_name: str, increment_user: bool = False) -> None:
    """
    Атомарно увеличивает выбранный счетчик статистики за текущий день.
    Если строки за сегодня нет — создается новая.
    """
    today = date.today()

    # 1. Пытаемся получить или создать запись за сегодня с дефолтными нулями
    BotStatistics.objects.get_or_create(
        date=today,
        defaults={
            'user_count': 0,
            'event_count': 0,
            'edited_events': 0,
            'cancelled_events': 0
        }
    )

    # 2. Атомарно увеличиваем нужный счетчик прямо в базе данных
    update_kwargs = {field_name: F(field_name) + 1}
    if increment_user:
        update_kwargs['user_count'] = F('user_count') + 1

    BotStatistics.objects.filter(date=today).update(**update_kwargs)



def main() -> None:
    """Запуск бота."""
    try:
        # подключение к БД и создание таблицы, если ее нет
        conn = conn_db(secrets.DB_CONN)

        # ***************************
        # глобально доступный объект календаря
        calendar = Calendar(conn)

        # создание обработчика с токеном
        application = Application.builder().token(secrets.API_TOKEN).build()

        application.bot_data['calendar'] = calendar

        # обработка команды /start
        application.add_handler(CommandHandler('start', create_start_handler))
        # обработка команды /key_on
        application.add_handler(CommandHandler('key_on', key_on))

        # обработка команды /key_off
        application.add_handler(CommandHandler('key_off', key_off))

        # обработка команды /help
        application.add_handler(CommandHandler('help', help_view))

        # обработчик для создания событий
        async def event_create_handler(update, context) -> None:
            try:
                # Взять данные о событии из сообщения пользователя
                event_name = update.message.text[14:]
                event_date = datetime.datetime.now().strftime('%Y-%m-%d')
                event_time = datetime.datetime.now().time().strftime('%H:%M:%S')
                event_details = "Описание события"
                tg_user_id = update.message.from_user.id  # получаем id пользователя в telegram
                # Создать событие с помощью метода create_event класса Calendar
                event_id = calendar.create_event(event_name, event_date, event_time,
                                                 event_details, tg_user_id)
                # Фиксируем создание события в Django БД
                await increment_statistic('event_count')
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
                                               text=calendar.read_event(event_name=event_name,
                                                                        tg_user_id=update.message.from_user.id))
            except AttributeError as error_info:
                # Отправить пользователю сообщение об ошибке
                await context.bot.send_message(chat_id=update.message.chat_id,
                                               text=f'При чтении события произошла ошибка {error_info}.')

        # Зарегистрировать обработчик, чтобы он вызывался по команде /read_event
        application.add_handler(CommandHandler('read_event', event_read_handler))

        # обработчик для редактирования событий
        async def event_edit_handler(update, context) -> int:
            try:
                event_name = update.message.text.replace('/edit_event',
                                                         '').strip()  # оставляем строку без пробелов в начале и конце
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
        async def edit_event(update, context) -> int | range | None:
            try:
                list_par = tuple(item.strip() for item in update.message.text.split(',') if item.strip())
                if len(list_par) < 2:
                    await update.message.reply_text(
                        "Ошибка! Введите данные в формате: <ГГГГ-ММ-ДД>, <Описание события>")
                    return ID  # Остаемся в этом же состоянии, ждем корректный ввод
                res_db = calendar.edit_event(context.user_data['editing_event_name'],
                                             update.message.from_user.id,
                                             list_par[0],
                                             list_par[1])
                # Отправить пользователю подтверждение
                if res_db[1] == 1:
                    await context.bot.send_message(chat_id=update.message.chat_id,
                                                   text=f"Событие с именем {context.user_data['editing_event_name']} отредактировано.\n"
                                                        f"{res_db[0]}")
                    # Фиксируем редактирование события в Django БД
                    await increment_statistic('edited_events')
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
                if calendar.display_event(tg_user_id=update.message.from_user.id, ):
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
