from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from loans.models import Loan
from notifications.models import Notification
from django.core.mail import send_mail
from django.conf import settings


class Command(BaseCommand):
    help = 'Send overdue notifications and due date reminders'

    def handle(self, *args, **options):
        # Send due date reminders (1 day before due date)
        tomorrow = timezone.now() + timedelta(days=1)
        due_loans = Loan.objects.filter(
            due_date__date=tomorrow.date(),
            returned_date__isnull=True
        )

        for loan in due_loans:
            Notification.objects.create(
                user=loan.user,
                title='Due Date Reminder',
                message=f'Your book "{loan.book.title}" is due tomorrow.',
                notification_type='due_reminder',
                related_object_id=loan.id,
                related_content_type='loan'
            )

            # Send email if user has preferences
            if hasattr(loan.user, 'notification_preferences'):
                if loan.user.notification_preferences.email_due_reminders:
                    send_mail(
                        'Library Book Due Tomorrow',
                        f'Dear {loan.user.first_name},\n\nYour book "{loan.book.title}" is due tomorrow.\n\nPlease return it on time to avoid late fees.\n\nBest regards,\nLibrary Management System',
                        settings.DEFAULT_FROM_EMAIL,
                        [loan.user.email],
                        fail_silently=True,
                    )

        # Send overdue alerts
        overdue_loans = Loan.objects.filter(
            due_date__lt=timezone.now(),
            returned_date__isnull=True
        )

        for loan in overdue_loans:
            days_overdue = (timezone.now() - loan.due_date).days

            Notification.objects.create(
                user=loan.user,
                title='Overdue Book Alert',
                message=f'Your book "{loan.book.title}" is {days_overdue} days overdue.',
                notification_type='overdue_alert',
                related_object_id=loan.id,
                related_content_type='loan'
            )

            # Send email if user has preferences
            if hasattr(loan.user, 'notification_preferences'):
                if loan.user.notification_preferences.email_overdue_alerts:
                    send_mail(
                        'Overdue Book Alert',
                        f'Dear {loan.user.first_name},\n\nYour book "{loan.book.title}" is {days_overdue} days overdue.\n\nPlease return it as soon as possible to avoid additional fees.\n\nBest regards,\nLibrary Management System',
                        settings.DEFAULT_FROM_EMAIL,
                        [loan.user.email],
                        fail_silently=True,
                    )

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully processed {due_loans.count()} due reminders and {overdue_loans.count()} overdue alerts'
            )
        )