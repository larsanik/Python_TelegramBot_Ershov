from django.contrib import admin

from .models import Event, BotStatistics, Appointment

# Register your models here.
admin.site.register(Event)

admin.site.register(BotStatistics)

admin.site.register(Appointment)
