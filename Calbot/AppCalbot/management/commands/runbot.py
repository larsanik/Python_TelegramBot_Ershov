import os
import sys
from django.core.management.base import BaseCommand

# Добавляем путь к папке src, если файл telegram_calendar_bot.py остается там
SRC_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', 'src'))
if SRC_PATH not in sys.path:
    sys.path.append(SRC_PATH)

from src.telegram_calendar_bot import main


class Command(BaseCommand):
    help = 'Запускает Telegram-бота'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Telegram-бот запускается...'))
        main()
