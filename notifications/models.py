from django.db import models
from accounts.models import User


class Notification(models.Model):
    NOTIFICATION_TYPES = (
        ('due_reminder', 'Due Date Reminder'),
        ('overdue_alert', 'Overdue Alert'),
        ('reservation_available', 'Reservation Available'),
        ('general', 'General'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=200)
    message = models.TextField()
    notification_type = models.CharField(max_length=50, choices=NOTIFICATION_TYPES)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    related_object_id = models.PositiveIntegerField(null=True, blank=True)
    related_content_type = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f"{self.user.username} - {self.title}"

    class Meta:
        ordering = ['-created_at']


class NotificationPreference(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='notification_preferences')
    email_due_reminders = models.BooleanField(default=True)
    email_overdue_alerts = models.BooleanField(default=True)
    email_reservation_available = models.BooleanField(default=True)
    email_general = models.BooleanField(default=True)

    def __str__(self):
        return f"Notification preferences for {self.user.username}"