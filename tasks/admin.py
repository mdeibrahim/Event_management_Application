from django.contrib import admin
from .models import Event, EventRegistration, Notification, Profile, EventCategory

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone_number', 'gender', 'age')
    search_fields = ('user__username', 'user__email', 'phone_number')
    list_filter = ('gender',)

@admin.register(EventCategory)
class EventCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name', 'description')

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'date', 'time', 'location', 'visibility')
    list_filter = ('category', 'visibility', 'date')
    search_fields = ('title', 'description', 'location')
    date_hierarchy = 'date'

@admin.register(EventRegistration)
class EventRegistrationAdmin(admin.ModelAdmin):
    list_display = ('event', 'user', 'role', 'requested_at')
    list_filter = ('role', 'event')
    search_fields = ('user__username', 'event__title', 'role')
    ordering = ('-requested_at',)
    date_hierarchy = 'requested_at'

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('recipient', 'notification_type', 'is_read', 'timestamp')
    list_filter = ('is_read', 'notification_type', 'timestamp')
    search_fields = ('recipient__username', 'message', 'notification_type')

