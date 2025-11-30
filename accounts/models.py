from django.contrib.auth.models import AbstractUser
from django.db import models
import uuid


class User(AbstractUser):
    USER_TYPES = (
        ('reader', 'Reader'),
        ('librarian', 'Librarian'),
        ('it_staff', 'IT Staff'),
        ('management', 'Management'),
    )

    user_type = models.CharField(max_length=20, choices=USER_TYPES, default='reader')
    phone_number = models.CharField(max_length=15, blank=True)
    address = models.TextField(blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    membership_id = models.CharField(max_length=20, unique=True, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.membership_id:
            self.membership_id = f"MEM{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.username} ({self.get_user_type_display()})"

    class Meta:
        db_table = 'auth_user'


class StaffInvite(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('used', 'Used'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled'),
    )

    email = models.EmailField(unique=True)
    token = models.CharField(max_length=100, unique=True)
    user_type = models.CharField(max_length=20, choices=[
        ('librarian', 'Librarian'),
        ('it_staff', 'IT Staff'),
        ('management', 'Management'),
    ])
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_staff_invites')
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    used_at = models.DateTimeField(null=True, blank=True)

    def is_expired(self):
        from django.utils import timezone
        return timezone.now() > self.expires_at

    def __str__(self):
        return f"Staff invite for {self.email} ({self.get_status_display()})"