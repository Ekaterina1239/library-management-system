from django.db import models
from django.utils import timezone
from datetime import timedelta
from accounts.models import User
from books.models import Book


class Loan(models.Model):
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('returned', 'Returned'),
        ('overdue', 'Overdue'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='loans')
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='loans')
    borrowed_date = models.DateTimeField(auto_now_add=True)
    due_date = models.DateTimeField()
    returned_date = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    renewals = models.IntegerField(default=0)
    max_renewals = models.IntegerField(default=2)

    def save(self, *args, **kwargs):
        if not self.due_date and not self.pk:
            self.due_date = timezone.now() + timedelta(days=14)

        if self.returned_date:
            self.status = 'returned'
        elif self.due_date and timezone.now() > self.due_date:
            self.status = 'overdue'
        else:
            self.status = 'active'

        if not self.pk:
            self.book.available_copies -= 1
            self.book.save()
        elif self.returned_date and self.status == 'returned':
            if self.book.available_copies < self.book.total_copies:
                self.book.available_copies += 1
                self.book.save()

        super().save(*args, **kwargs)

    def can_renew(self):
        return (self.renewals < self.max_renewals and
                self.status == 'active' and
                not self.is_overdue())

    def is_overdue(self):
        return timezone.now() > self.due_date and not self.returned_date

    def days_overdue(self):
        if self.is_overdue():
            return (timezone.now() - self.due_date).days
        return 0

    def __str__(self):
        return f"{self.user.username} - {self.book.title}"


class Reservation(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('available', 'Available'),
        ('cancelled', 'Cancelled'),
        ('expired', 'Expired'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reservations')
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='reservations')
    reserved_date = models.DateTimeField(auto_now_add=True)
    expiry_date = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    notified = models.BooleanField(default=False)
    priority = models.IntegerField(default=0)

    def save(self, *args, **kwargs):
        if not self.expiry_date:
            self.expiry_date = timezone.now() + timedelta(days=3)

        if not self.pk:
            existing_reservations = Reservation.objects.filter(
                book=self.book,
                status__in=['pending', 'available']
            ).count()
            self.priority = existing_reservations + 1

        super().save(*args, **kwargs)

    def is_expired(self):
        return timezone.now() > self.expiry_date

    def __str__(self):
        return f"{self.user.username} - {self.book.title}"