# **Задание 3.** Напишите приложение, которое работает с заметками
# Приложение должно создавать, читать, редактировать и удалять заметки.
# Для этого создайте функции для каждой операции с
# заметками и основную функцию, которая управляет работой приложения.

# +
# Задание 4. Добавьте вывод всех заметок пользователя

import os
import time
import telegram
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import logging
import secrets
# логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def build_note(note_text, note_name):
    """получает название и текст заметки, а затем создает текстовый файл с этим названием и текстом"""
    try:
        if not note_text.strip():
            logger.error("Текст заметки не может быть пустым.")
            return
        with open(f"{note_name}.txt", "w", encoding="utf-8") as file:
            file.write(note_text)
        logger.info(f"Заметка {note_name} создана.")
    except Exception as err:
        logger.error(f'Произошла ошибка: {err}')


def create_note(note_name, note_text):
    """запрашивает у пользователя название и текст заметки, а затем вызывает функцию build_note(note_text, note_name)"""
    try:
        # note_name = input("Введите название заметки для создания: ")
        # note_text = input("Введите текст заметки: ")
        build_note(note_text, note_name)
    except Exception as err:
        logger.error(f'Произошла ошибка: {err}')


# обработчик для создания заметок create_handler
def create_note_handler(update, context):
    try:
        # Получить название заметки из сообщения пользователя
        note_name = context.bot.send_message(chat_id=update.message.chat_id,text="Введите имя заметки:")
        context.bot.register_next_step_handler(note_name, )
        #note_name = update.message.chat_id
        logger.info(note_name)
        # Получить текст заметки из сообщения пользователя
        # note_text = update.send_message(text="Введите текст заметки:")
        # update.register_next_step_handler(note_text)
        note_text = update.message.text
        logger.error(note_text)
        # Создать заметку с помощью функции create_note(note_text, note_name)
        create_note(note_name, note_text)
        # Отправить пользователю подтверждение, что заметка создана
        context.bot.send_message(chat_id=update.message.chat_id, text=f"Заметка {note_name} создана.")
    except Exception as err:
        # Отправить пользователю сообщение об ошибке
        context.bot.send_message(chat_id=update.message.chat_id, text=f"Произошла ошибка: {err}")


# эхо
def text(update, context):
    message = update.message
    message.reply_text('Echo: ' + message.text)


def read_note():
    """запрашивает у пользователя название заметки. Если файл с таким названием существует, функция считывает содержимое
    файла и выводит его на экран. Если файла не существует, функция выводит сообщение, что заметка не найдена.
    Для проверки наличия файла используйте функцию os.path.isfile из модуля os.
    Не забудьте импортировать этот модуль."""
    try:
        note_name = input("Введите название заметки: ")
        if os.path.isfile(note_name + ".txt"):
            with open(f"{note_name}.txt", "r", encoding="utf-8") as file:
                print(file.read())
            return note_name
        else:
            logger.error("Заметка не найдена.")
            return ''
    except Exception as err:
        logger.error(f'Произошла ошибка: {err}')


def edit_note():
    """запрашивает у пользователя название заметки. Если файл с введенным именем существует, функция считывает и выводит
     содержимое файла, запрашивает у пользователя новый текст заметки и обновляет содержимое файла. Если файла не
      существует, она выводит сообщение, что заметка не найдена."""
    try:
        note_name = read_note()
        if note_name != '':
            note_text = input("Введите новый текст заметки: ")
            with open(f"{note_name}.txt", "w", encoding="utf-8") as file:
                file.write(note_text)
            logger.info(f"Заметка {note_name} обновлена.")
    except Exception as err:
        logger.error(f'Произошла ошибка: {err}')


def delete_note():
    """запрашивает у пользователя название заметки. Если файл с введенным именем существует, функция удаляет файл.
    Для удаления используйте функцию os.remove из модуля os. Если файла не существует, она выводит сообщение,
    что заметка не найдена."""
    try:
        note_name = input("Введите название заметки для удаления: ")
        if os.path.isfile(note_name + '.txt'):
            os.remove(note_name + '.txt')
            logger.info(f"Заметка {note_name} удалена.")
        else:
            logger.error("Заметка не найдена.")
    except Exception as err:
        logger.error(f'Произошла ошибка: {err}')


def display_notes():
    """выводит все заметки пользователя"""
    try:
        # формирование списка файлов с замктками
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
                print(f'Заметка "{i[0]}".')
                print(file.read(), '\n')
    except Exception as err:
        logger.error(f'Произошла ошибка: {err}')


def display_sorted_notes():
    """выводит все заметки пользователя в порядке уменьшения длинны"""
    try:
        # формирование списка файлов с замктками
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
                print(f'Заметка "{i[0]}".')
                print(file.read(), '\n')
    except Exception as err:
        logger.error(f'Произошла ошибка: {err}')


# проверка связи
def hi(update, context):
    context.bot.send_message(chat_id=update.message.chat_id, text="Я на связи =о).")


# инициализация объекта Updater с помощью токена API:
updater = Updater(token=secrets.API_TOKEN, use_context=True)
# Добавить функцию create_note_handler как CommandHandler для команды /create
updater.dispatcher.add_handler(CommandHandler('create', create_note_handler))
updater.dispatcher.add_handler(CommandHandler("hi", hi))
updater.dispatcher.add_handler(MessageHandler(Filters.text, text))
updater.start_polling()

# def main():
#     """содержит основной цикл программы. Функция отображает меню с вариантами действий с заметками, которые пользователь
#      может выбрать. Затем функция выполняет действие, которое выбрал пользователь."""
#     try:
#         while True:
#             # запрашиваем дейстие с заметкой у пользователя
#             sel = input("Что вы хотите сделать с заметкой?\n"
#                         "Создать       - 1\n"
#                         "Читать        - 2\n"
#                         "Редактировать - 3\n"
#                         "Удалить       - 4\n"
#                         "Вывести все заметки в порядке уменьшения длинны - 5\n"
#                         ":> ")
#             # выполнение действий с заметками
#             if sel == "1":
#                 create_note()
#             elif sel == "2":
#                 read_note()
#             elif sel == "3":
#                 edit_note()
#             elif sel == "4":
#                 delete_note()
#             elif sel == "5":
#                 display_sorted_notes()
#             else:
#                 logger.info('Не верно введен вариант действия с заметкой.')
#
#             # выход из программы
#             time.sleep(0.1)
#             if input('Продолжить работу с заметками (y/n)?\n:> ').lower() == 'n':
#                 break
#     except Exception as err:
#         logger.error(f'Произошла ошибка: {err}')
#
#
# if __name__ == "__main__":
#     main()
