from django.contrib import admin
from .models import Notification, NotificationPreference


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'title', 'notification_type', 'is_read', 'created_at')
    list_filter = ('notification_type', 'is_read', 'created_at')
    search_fields = ('user__username', 'title', 'message')
    readonly_fields = ('created_at',)
    date_hierarchy = 'created_at'

    fieldsets = (
        ('Notification Content', {
            'fields': ('user', 'title', 'message', 'notification_type')
        }),
        ('Status and Metadata', {
            'fields': ('is_read', 'created_at', 'related_object_id', 'related_content_type')
        }),
    )


@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(admin.ModelAdmin):
    list_display = (
    'user', 'email_due_reminders', 'email_overdue_alerts', 'email_reservation_available', 'email_general')
    list_filter = ('email_due_reminders', 'email_overdue_alerts', 'email_reservation_available', 'email_general')
    search_fields = ('user__username', 'user__email')