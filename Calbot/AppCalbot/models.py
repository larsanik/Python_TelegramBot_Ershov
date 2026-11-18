from django.conf import settings
from django.db import models

# Create your models here.
class Event(models.Model):
    name = models.CharField(verbose_name='Имя',max_length=255)
    date = models.DateField(verbose_name='Дата')
    time = models.TimeField(verbose_name='Время')
    duration_minutes = models.PositiveIntegerField(
        default=60,
        verbose_name="Длительность (в минутах)",
        help_text="Укажите продолжительность события в минутах, например 60"
    )

    class Meta:
        verbose_name = "Событие"
        verbose_name_plural = "События"

    def __str__(self):
        return f"Событие {self.name} - {self.date} - {self.time}, длительность {self.duration_minutes} минут"

# статистика бота
class BotStatistics(models.Model):
    date = models.DateField(unique=True, verbose_name="Дата")
    user_count = models.PositiveIntegerField(default=0, verbose_name="Новые пользователи")
    event_count = models.PositiveIntegerField(default=0, verbose_name="Создано событий")
    edited_events = models.PositiveIntegerField(default=0, verbose_name="Отредактировано событий")
    cancelled_events = models.PositiveIntegerField(default=0, verbose_name="Отменено действий/событий")

    class Meta:
        verbose_name = "Статистика бота"
        verbose_name_plural = "Статистика бота"

    def __str__(self):
        return f"Статистика за {self.date.strftime('%d.%m.%Y')}"


class Appointment(models.Model):
    STATUS_CHOICES = [
        ('pending', 'ожидание'),
        ('confirmed', 'подтверждено'),
        ('cancelled', 'отменено'),
    ]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    date = models.DateField()
    time = models.TimeField()
    details = models.TextField(blank=True)
    status = models.CharField(
        choices=STATUS_CHOICES,
        default='pending',
        max_length=40,
    )

    class Meta:
        verbose_name = "Встреча"
        verbose_name_plural = "Встречи"

    def __str__(self):
        return f"Встреча: {self.user.username} - {self.event.name} - {self.date} - {self.time}"


class TelegramUser(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='telegram_profile',
        verbose_name="Пользователь Django"
    )
    tg_user_id = models.BigIntegerField(unique=True, verbose_name="Telegram ID")
    tg_login = models.CharField(max_length=50, verbose_name="Telegram логин")

    class Meta:
        verbose_name = "Пользователь Telegram"
        verbose_name_plural = "Пользователи Telegram"

    def __str__(self):
        return f"{self.tg_login} ({self.tg_user_id})"


class UserDailyEntry(models.Model):
    tg_user_id = models.BigIntegerField(verbose_name="Telegram ID")
    date = models.DateField(auto_now_add=True, verbose_name="Дата входа")
    time = models.TimeField(auto_now_add=True, verbose_name="Время входа")

    class Meta:
        verbose_name = "Суточный визит"
        verbose_name_plural = "Суточные визиты"
        constraints = [
            models.UniqueConstraint(fields=['tg_user_id', 'date'], name='unique_daily_entry')
        ]

    def __str__(self):
        return f"Первый вход за сутки пользователя с Telegram ID: {self.tg_user_id}"
