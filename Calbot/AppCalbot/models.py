from django.conf import settings
from django.db import models

# Create your models here.
class Event(models.Model):
    name = models.CharField(verbose_name='Имя',max_length=255)
    date = models.DateField(verbose_name='Дата')
    time = models.TimeField(verbose_name='Время')

    class Meta:
        verbose_name = "Событие"
        verbose_name_plural = "События"

    def __type__(self):
        return f"Событие {self.name}"

    def __str__(self):
        return f"Событие {self.name} - {self.date} - {self.time}"

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
        return f"Встреча: {self.user.name} - {self.event.name} - {self.date} - {self.time}"
