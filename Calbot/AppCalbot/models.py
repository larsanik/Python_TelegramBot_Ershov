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
