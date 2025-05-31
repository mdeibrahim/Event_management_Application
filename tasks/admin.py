from django.contrib import admin
from .models import User, Event, EventRegistration, Notification,Profile,EventCategory

# Register your models here.
admin.site.register(User)
admin.site.register(Profile)
admin.site.register(EventCategory)
admin.site.register(Event)
admin.site.register(EventRegistration)
admin.site.register(Notification)

