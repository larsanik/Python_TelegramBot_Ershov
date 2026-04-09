# *****************************************************************************
# Основы объектно-ориентированного программирования
# Задание 8.
# Добавьте в приложение класс Calendar
# 1. Добавьте в приложение класс Calendar который будет содержать методы для создания, чтения, редактирования и
# удаления событий, а также отображения всех событий. Для работы с календарем вам потребуются библиотеки os и datetime.
# Импортируйте их в начале кода.
# 2. Добавьте и зарегистрируйте обработчики команд для создания, чтения, редактирования и удаления событий, а также
# отображения всех событий.
# 3. Затем включите этот класс в основную функцию приложения (функция main()), чтобы дать пользователю возможность
# создавать, читать, редактировать и удалять события, а также отображать весь список событий.
# *****************************************************************************
import logging
import os
import datetime
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    ConversationHandler  # ,
    # CallbackContext
)
import secrets  # API_TOKEN = '<ТОКЕN>'

# Включение логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

# шаги ввода данных
NAME, TEXT, READ, ID = range(4)


# создаем заметку по полученным данным
def build_note(lc_note_text, lc_note_name) -> str:
    """Получает название и текст заметки, а затем создает текстовый файл с этим названием и текстом"""
    try:
        if lc_note_text == '':
            logger.error("Текст заметки не может быть пустым.")
            return "Текст заметки не может быть пустым."
        else:
            with open(f"{lc_note_name}.txt", "w", encoding="utf-8") as file:
                file.write(lc_note_text)
            logger.info(f"Заметка {lc_note_name} создана.")
            return f"Заметка {lc_note_name} создана."
    except AttributeError as err:
        logger.error(f'Произошла ошибка: {err}')


# запуск ввода данных для создания заметок
def create_note_handler(update, context) -> int:
    """Запрос имени заметки."""
    try:
        update.message.reply_text('Введите имя заметки: ')
        return NAME
    except AttributeError as err:
        logger.error(f'Произошла ошибка: {err}')


# получение имени заметки для создания
def get_name_note_create(update, context) -> int:
    """Запрос текста заметки."""
    try:
        user = update.message.from_user
        logger.info(f"Пользователь:  {user.first_name}. Имя создаваемой заметки: {update.message.text}.")
        context.user_data['note_name'] = update.message.text
        update.message.reply_text('Введите текст заметки: ')
        return TEXT
    except AttributeError as err:
        logger.error(f'Произошла ошибка: {err}')


# получение текста заметки + создание заметки
def get_text_note(update, context) -> int:
    """Выход из опроса."""
    try:
        user = update.message.from_user
        logger.info(f"Пользователь:  {user.first_name}. Текст создаваемой заметки: {update.message.text}")
        context.user_data['note_text'] = update.message.text
        # создаем заметку и выводим сообщение о результате
        update.message.reply_text(build_note(context.user_data['note_text'], context.user_data['note_name']))  #
        return ConversationHandler.END
    except AttributeError as err:
        logger.error(f'Произошла ошибка: {err}')


def cancel(update, context) -> int:
    """Выход из диалога по команде /cancel."""
    try:
        user = update.message.from_user
        logger.info(f"Пользователь {user.first_name} вышел из диалога.")
        update.message.reply_text('Запрос данных прерван пользователем.')
        return ConversationHandler.END
    except AttributeError as err:
        logger.error(f'Произошла ошибка: {err}')


# обработчик для команды /start
def create_start_handler(update, context):
    """Формирование сообщения пользователю по команде start."""
    try:
        msg_start = """ Бот для работы с заметками.
        Команды:
        /start - запуск бота
        /create - создание заметки
        /cancel - выход из диалога
        /read - чтение заметки
        /edit - замена текста заметки
        /delete - удаление заметки
        /display - вывод списка заметок в порядке уменьшения длинны
        /key_on - включение виртуальной клавиатуры
        /key_off - выключение виртуальной клавиатуры
        /create_event <название события> - создание события
        /read_event <номер события> - чтение события
        /edit_event <номер события> - редактирование события
        /delete_event <номер события> - удаление события
        /display_event - вывод списка событий
        /help - выводит справку по командам
        """
        context.bot.send_message(chat_id=update.message.chat_id, text=msg_start)
    except AttributeError as err:
        # Отправить пользователю сообщение об ошибке
        context.bot.send_message(chat_id=update.message.chat_id, text=f"Произошла ошибка: {err}")


def read_note(note_name) -> str:
    """Читает заметку. Если файл с таким названием существует, функция считывает содержимое
    файла и выводит его на экран. Если файла не существует, функция выводит сообщение, что заметка не найдена.
    Для проверки наличия файла используйте функцию os.path.isfile из модуля os.
    Не забудьте импортировать этот модуль."""
    try:
        if os.path.isfile(note_name + ".txt"):
            with open(f"{note_name}.txt", "r", encoding="utf-8") as file:
                return file.read()
        else:
            logger.error(f"Заметка {note_name} не найдена.")
            return f"Заметка {note_name} не найдена."
    except AttributeError as err:
        logger.error(f'Произошла ошибка: {err}')


# получение имени заметки для чтения и вывод в чат если есть, если нет сообщение нет
def get_name_note_read(update, context) -> int:
    """Запрос имени заметки для чтения."""
    try:
        user = update.message.from_user
        logger.info(f"Пользователь:  {user.first_name}. Имя заметки для чтения : {update.message.text}.")
        context.user_data['note_name'] = update.message.text
        # создаем заметку и выводим сообщение о результате
        update.message.reply_text(read_note(context.user_data['note_name']))
        return ConversationHandler.END
    except AttributeError as err:
        logger.error(f'Произошла ошибка: {err}')


def create_read_handler(update, context) -> None:
    """Обработчик для команды read"""
    try:
        update.message.reply_text('Введите имя заметки для чтения: ')
        return NAME
    except AttributeError as err:
        # Отправить пользователю сообщение об ошибке
        context.bot.send_message(chat_id=update.message.chat_id, text=f"Произошла ошибка: {err}")


def edit_note(note_name, note_text) -> str:
    """Обновляет содержимое файла. Если файла не
      существует, она выводит сообщение, что заметка не найдена."""
    try:
        if note_name != '':
            with open(f"{note_name}.txt", "w", encoding="utf-8") as file:
                file.write(note_text)
            logger.info(f"Заметка {note_name} обновлена.")
            return f"Заметка {note_name} обновлена."
    except FileNotFoundError:
        logger.error(f"Невозможно создать файл с именем {note_name}")
    except AttributeError as err:
        logger.error(f'Произошла ошибка : {err}')


def get_name_note_edit(update, context) -> int:
    """Запрос нового текста заметки."""
    try:
        user = update.message.from_user
        logger.info(f"Пользователь:  {user.first_name}. Имя редактируемой заметки: {update.message.text}.")
        context.user_data['note_name'] = update.message.text
        if os.path.isfile(context.user_data['note_name'] + '.txt'):
            update.message.reply_text('Введите новый текст заметки: ')
            return TEXT
        else:
            logger.error(f"Пользователь:  {user.first_name}. Заметка {context.user_data['note_name']} не найдена.")
            update.message.reply_text(f"Заметка с именем {context.user_data['note_name']} не найдена")
            update.message.reply_text('Введите имя заметки для редактирования еще раз:')
            return NAME
    except AttributeError as err:
        logger.error(f'Произошла ошибка : {err}')


def get_text_note_edit(update, context) -> int:
    """Выход из опроса."""
    try:
        user = update.message.from_user
        logger.info(f"Пользователь:  {user.first_name}. Текст редактируемой заметки: {update.message.text}")
        context.user_data['note_text'] = update.message.text
        # создаем заметку и выводим сообщение о результате
        update.message.reply_text(edit_note(context.user_data['note_name'], context.user_data['note_text']))
        return ConversationHandler.END
    except AttributeError as err:
        logger.error(f'Произошла ошибка : {err}')


def create_edit_handler(update, context) -> None:
    """Обработчик для команды edit"""
    try:
        update.message.reply_text('Введите имя заметки для редактирования: ')
        return NAME
    except AttributeError as err:
        # Отправить пользователю сообщение об ошибке
        context.bot.send_message(chat_id=update.message.chat_id, text=f"Произошла ошибка: {err}")


def delete_note(note_name) -> str:
    """Функция удаляет файл.
    Для удаления используйте функцию os.remove из модуля os. Если файла не существует, она выводит сообщение,
    что заметка не найдена."""
    try:
        if os.path.isfile(note_name + '.txt'):
            os.remove(note_name + '.txt')
            logger.info(f"Заметка {note_name} удалена.")
            return f"Заметка {note_name} удалена."
        else:
            logger.error(f"Заметка  {note_name} не найдена.")
            return f"Заметка  {note_name} не найдена."
    except FileNotFoundError:
        logger.error(f"Файл с именем {note_name}.txt не найден.")
    except AttributeError as err:
        logger.error(f'Произошла ошибка: {err}')


def get_name_note_delete(update, context) -> int:
    """Запрос имени заметки для удаления."""
    try:
        user = update.message.from_user
        logger.info(f"Пользователь:  {user.first_name}. Имя заметки для удаления : {update.message.text}.")
        context.user_data['note_name'] = update.message.text
        # удаляем заметку и выводим сообщение о результате
        update.message.reply_text(delete_note(context.user_data['note_name']))
        return ConversationHandler.END
    except AttributeError as err:
        logger.error(f'Произошла ошибка: {err}')


def create_delete_handler(update, context) -> int:
    """Обработчик для команды delete"""
    try:
        update.message.reply_text('Введите имя заметки для удаления: ')
        return NAME
    except AttributeError as err:
        # Отправить пользователю сообщение об ошибке
        context.bot.send_message(chat_id=update.message.chat_id, text=f"Произошла ошибка: {err}")


def display_sorted_notes(update, context) -> None:
    """Выводит все заметки пользователя в порядке уменьшения длинны"""
    try:
        # формирование списка файлов с заметками
        notes = [note for note in os.listdir() if note.endswith(".txt")]
        # создание словаря с именем файла и длинной заметки
        dic_notes = {}
        for i in notes:
            with open(i, "r", encoding="utf-8") as file:
                dic_notes[i] = len(file.read())
        # сортировка заметок по уменьшению длинны
        sorted_notes = sorted(dic_notes.items(), key=lambda item: item[1], reverse=True)
        # вывод заметок в порядке уменьшения длинны
        for i in sorted_notes:
            with open(i[0], "r", encoding="utf-8") as file:
                update.message.reply_text(f'Заметка "{i[0]}".')
                update.message.reply_text(file.read())
    except AttributeError as err:  # не приходит в голову ситуация вызывающая ошибку =/
        logger.error(f'Произошла ошибка: {err}')


def key_on(update, context) -> None:
    """Добавляет виртуальную клавиатуру с командами"""
    reply_keyboard = [['/start'],
                      ['/create'],
                      ['/cancel'],
                      ['/read'],
                      ['/edit'],
                      ['/delete'],
                      ['/display'],
                      ['/key_off'],
                      ['/help'],
                      ['/create_event'],
                      ['/read_event'],
                      ['/edit_event'],
                      ['/delete_event'],
                      ['/display_event']]

    update.message.reply_text(
        'Виртуальная клавиатура добавлена в бот.',
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, resize_keyboard=True, one_time_keyboard=True,
            input_field_placeholder='Выберите команду или введите ответ на запрос'
        ),
    )


def key_off(update, context) -> None:
    """Убирает виртуальную клавиатуру с командами"""
    update.message.reply_text(
        'Виртуальная клавиатура убрана из бота.',
        reply_markup=ReplyKeyboardRemove(),
    )


def help_view(update, context) -> None:
    """Выводит справку по командам"""
    update.message.reply_text(""" Бот для работы с заметками.
        Команды:
        /start - запуск бота
        /create - создание заметки
        /cancel - выход из диалога
        /read - чтение заметки
        /edit - замена текста заметки
        /delete - удаление заметки
        /display - вывод списка заметок в порядке уменьшения длинны
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


# ******** Задание 8 Календарь START ********
# Создать класс Calendar
class Calendar:
    def __init__(self):
        self.events = {}

    # метод create_event
    def create_event(self, event_name, event_date, event_time, event_details) -> int:
        event_id = len(self.events) + 1
        event = {
            "id": event_id,
            "name": event_name,
            "date": event_date,
            "time": event_time,
            "details": event_details
        }
        self.events[event_id] = event
        return event_id

    # метод read_event
    def read_event(self, id_event) -> str:
        str_out = ''
        for key, val in self.events[id_event].items():
            str_out = str_out + str(key) + ': ' + str(val) + ' | '
        return str_out

    # метод edit_event
    def edit_event(self, id_event, new_event_details) -> None:
        self.events[id_event]['details'] = new_event_details

    # метод delete_event
    def delete_event(self, id_event) -> str:
        del self.events[id_event]
        return f'Событие номер {id_event} удалено.'

    # метод display_event
    def display_event(self) -> str:
        str_out = ''
        for el in self.events.items():
            # print(el[1].items())
            for key, val in el[1].items():
                str_out = str_out + str(key) + ': ' + str(val) + ' | '
            str_out = str_out + '\n'
        return str_out

# ******** Задание 8 Календарь END ********


def main() -> None:
    """Запуск бота."""
    try:
        # создание обработчика с токеном
        updater = Updater(token=secrets.API_TOKEN)

        # получение диспетчера
        dispatcher = updater.dispatcher

        # обработка команды /start
        updater.dispatcher.add_handler(CommandHandler('start', create_start_handler))

        # диалог для создания заметки, шаги NAME, ТEXT
        conv_handler_create = ConversationHandler(
            entry_points=[CommandHandler('create', create_note_handler)],
            states={
                NAME: [MessageHandler(Filters.text & ~Filters.command, get_name_note_create)],
                TEXT: [MessageHandler(Filters.text & ~Filters.command, get_text_note)],
            },
            fallbacks=[CommandHandler('cancel', cancel)],  # принудительный выход из диалога по команде /cancel
        )
        dispatcher.add_handler(conv_handler_create)

        # диалог для чтения заметки, шаг NAME
        conv_handler_read = ConversationHandler(
            entry_points=[CommandHandler('read', create_read_handler)],
            states={
                NAME: [MessageHandler(Filters.text & ~Filters.command, get_name_note_read)],
            },
            fallbacks=[CommandHandler('cancel', cancel)],  # принудительный выход из диалога по команде /cancel
        )
        dispatcher.add_handler(conv_handler_read)

        # диалог для редактирования заметки, шаги NAME, ТEXT
        conv_handler_edit = ConversationHandler(
            entry_points=[CommandHandler('edit', create_edit_handler)],
            states={
                NAME: [MessageHandler(Filters.text & ~Filters.command, get_name_note_edit)],
                TEXT: [MessageHandler(Filters.text & ~Filters.command, get_text_note_edit)],
            },
            fallbacks=[CommandHandler('cancel', cancel)],  # принудительный выход из диалога по команде /cancel
        )
        dispatcher.add_handler(conv_handler_edit)

        # диалог для удаления заметки, шаг NAME
        conv_handler_delete = ConversationHandler(
            entry_points=[CommandHandler('delete', create_delete_handler)],
            states={
                NAME: [MessageHandler(Filters.text & ~Filters.command, get_name_note_delete)],
            },
            fallbacks=[CommandHandler('cancel', cancel)],  # принудительный выход из диалога по команде /cancel
        )
        dispatcher.add_handler(conv_handler_delete)

        # обработка команды /display
        updater.dispatcher.add_handler(CommandHandler('display', display_sorted_notes))

        # обработка команды /key_on
        updater.dispatcher.add_handler(CommandHandler('key_on', key_on))

        # обработка команды /key_off
        updater.dispatcher.add_handler(CommandHandler('key_off', key_off))

        # обработка команды /help
        updater.dispatcher.add_handler(CommandHandler('help', help_view))

        # ***************************
        # глобально доступный объект календаря
        calendar = Calendar()

        # обработчик для создания событий
        def event_create_handler(update, context) -> None:
            try:
                # Взять данные о событии из сообщения пользователя
                event_name = update.message.text[14:]
                event_date = datetime.datetime.now().strftime('%Y-%m-%d')
                event_time = datetime.datetime.now().time().strftime('%H:%M')
                event_details = "Описание события"

                # Создать событие с помощью метода create_event класса Calendar
                event_id = calendar.create_event(event_name, event_date, event_time, event_details)

                # Отправить пользователю подтверждение
                context.bot.send_message(chat_id=update.message.chat_id,
                                         text=f"Событие {event_name} создано и имеет номер {event_id}.")
            except AttributeError as error_info:
                # Отправить пользователю сообщение об ошибке
                context.bot.send_message(chat_id=update.message.chat_id,
                                         text=f'При создании события произошла ошибка {error_info}.')

        # Зарегистрировать обработчик, чтобы он вызывался по команде /create_event
        updater.dispatcher.add_handler(CommandHandler('create_event', event_create_handler))

        # обработчик для чтения событий
        def event_read_handler(update, context) -> None:
            try:
                text = update.message.text.replace('/read_event', '').replace(' ', '')  # оставляем только номер
                if text.isdigit():  # проверяем, что номер события число
                    id_event = int(text)
                else:
                    id_event = 0  # так как нумерация событий начинается с 1
                if id_event in calendar.events.keys():
                    context.bot.send_message(chat_id=update.message.chat_id,
                                             text=calendar.read_event(id_event=id_event))
                else:
                    context.bot.send_message(chat_id=update.message.chat_id,
                                             text=f'Событие с номером {text} не найдено. Формат команды: '
                                                  f'/read_event <номер события> ')
            except AttributeError as error_info:
                # Отправить пользователю сообщение об ошибке
                context.bot.send_message(chat_id=update.message.chat_id,
                                         text=f'При чтении события произошла ошибка {error_info}.')

        # Зарегистрировать обработчик, чтобы он вызывался по команде /read_event
        updater.dispatcher.add_handler(CommandHandler('read_event', event_read_handler))

        # обработчик для редактирования событий
        def event_edit_handler(update, context) -> int:
            try:
                text = update.message.text.replace('/edit_event', '').replace(' ', '')  # оставляем только номер
                if text.isdigit():  # проверяем, что номер события число
                    id_event = int(text)
                else:
                    id_event = 0  # так как нумерация событий начинается с 1
                if id_event in calendar.events.keys():
                    context.user_data['id_event'] = id_event
                    context.bot.send_message(chat_id=update.message.chat_id,
                                             text='Введите новое описание события.')
                    return ID
                else:
                    context.bot.send_message(chat_id=update.message.chat_id,
                                             text=f'Событие с номером {text} не найдено. Формат команды: '
                                                  f'/edit_event <номер события> ')
            except AttributeError as error_info:
                # Отправить пользователю сообщение об ошибке
                context.bot.send_message(chat_id=update.message.chat_id,
                                         text=f'При редактировании события произошла ошибка {error_info}.')

        # редактирование события
        def edit_event(update, context) -> None:
            try:
                calendar.edit_event(context.user_data['id_event'], update.message.text)
                # Отправить пользователю подтверждение
                context.bot.send_message(chat_id=update.message.chat_id,
                                         text=f"Событие {context.user_data['id_event']} отредактировано.")
            except AttributeError as error_info:
                # Отправить пользователю сообщение об ошибке
                context.bot.send_message(chat_id=update.message.chat_id,
                                         text=f'При редактировании события произошла ошибка {error_info}.')

        # диалог для редактирования события, шаги ID, ТEXT
        conv_handler_edit_event = ConversationHandler(
            entry_points=[CommandHandler('edit_event', event_edit_handler)],
            states={
                ID: [MessageHandler(Filters.text & ~Filters.command, edit_event)],
            },
            fallbacks=[CommandHandler('cancel', cancel)],  # принудительный выход из диалога по команде /cancel
        )
        dispatcher.add_handler(conv_handler_edit_event)

        # обработчик для удаления событий
        def event_delete_handler(update, context) -> None:
            try:
                text = update.message.text.replace('/delete_event', '').replace(' ', '')  # оставляем только номер
                if text.isdigit():  # проверяем, что номер события число
                    id_event = int(text)
                else:
                    id_event = 0  # так как нумерация событий начинается с 1
                if id_event in calendar.events.keys():
                    context.bot.send_message(chat_id=update.message.chat_id,
                                             text=calendar.delete_event(id_event=id_event))
                else:
                    context.bot.send_message(chat_id=update.message.chat_id,
                                             text=f'Событие с номером {text} не найдено. Формат команды: '
                                                  f'/delete_event <номер события> ')
            except AttributeError as error_info:
                # Отправить пользователю сообщение об ошибке
                context.bot.send_message(chat_id=update.message.chat_id,
                                         text=f'При удалении события произошла ошибка {error_info}.')

        # Зарегистрировать обработчик, чтобы он вызывался по команде /delete_event
        updater.dispatcher.add_handler(CommandHandler('delete_event', event_delete_handler))

        # обработчик для вывода списка событий
        def event_display_handler(update, context) -> None:
            try:
                if calendar.events:
                    context.bot.send_message(chat_id=update.message.chat_id,
                                             text=calendar.display_event())
                else:
                    context.bot.send_message(chat_id=update.message.chat_id,
                                             text=f'В календаре нет событий.')
            except AttributeError as error_info:
                # Отправить пользователю сообщение об ошибке
                context.bot.send_message(chat_id=update.message.chat_id,
                                         text=f'При удалении события произошла ошибка {error_info}.')

        # Зарегистрировать обработчик, чтобы он вызывался по команде /delete_event
        updater.dispatcher.add_handler(CommandHandler('display_event', event_display_handler))


        # запуск бота
        updater.start_polling()

        # для корректной остановки бота по запросу из ide
        updater.idle()

    except AttributeError as err:
        logger.error(f'Произошла ошибка: {err}')


if __name__ == '__main__':
    main()
