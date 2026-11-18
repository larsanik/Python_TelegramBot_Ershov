import os
import subprocess
import sys
import time

# Путь к интерпретатору текущего виртуального окружения (.venv)
PYTHON_EXE = sys.executable
MANAGE_PY = os.path.join('Calbot', 'manage.py')


def main():
    print("Запуск веб-сервера Django и Telegram-бота...")

    # 1. Запускаем Django-сервер (--noreload важен, чтобы не плодить лишние процессы)
    django_proc = subprocess.Popen([PYTHON_EXE, MANAGE_PY, 'runserver', '--noreload'])

    # 2. Запускаем Telegram-бота
    bot_proc = subprocess.Popen([PYTHON_EXE, MANAGE_PY, 'runbot'])

    try:
        # Следим за работой обоих процессов
        while True:
            if django_proc.poll() is not None:
                print("Сервер Django остановился. Завершаем работу...")
                break
            if bot_proc.poll() is not None:
                print("Telegram-бот остановился. Завершаем работу...")
                break
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nОстановка проектов...")
    finally:
        # Гарантированно закрываем оба процесса при выходе
        django_proc.terminate()
        bot_proc.terminate()
        django_proc.wait()
        bot_proc.wait()
        print("Оба сервиса успешно остановлены.")


if __name__ == '__main__':
    main()
