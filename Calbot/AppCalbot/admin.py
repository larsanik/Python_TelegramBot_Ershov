from django.contrib import admin

from .models import Event, BotStatistics, Appointment, TelegramUser, UserDailyEntry

# Register your models here.
admin.site.register(Event)

admin.site.register(BotStatistics)

admin.site.register(Appointment)

admin.site.register(TelegramUser)

admin.site.register(UserDailyEntry)
