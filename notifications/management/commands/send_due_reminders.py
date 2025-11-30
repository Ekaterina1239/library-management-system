from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from loans.models import Loan
from notifications.models import Notification
from django.core.mail import send_mail
from django.conf import settings


class Command(BaseCommand):
    help = 'Send due date reminders for loans due tomorrow'

    def handle(self, *args, **options):
        tomorrow = timezone.now() + timedelta(days=1)
        due_tomorrow = Loan.objects.filter(
            due_date__date=tomorrow.date(),
            returned_date__isnull=True
        )

        count = 0
        for loan in due_tomorrow:
            # Create notification
            Notification.objects.create(
                user=loan.user,
                title='Due Date Reminder',
                message=f'Your book "{loan.book.title}" is due tomorrow. Please return it on time.',
                notification_type='due_reminder',
                related_object_id=loan.id,
                related_content_type='loan'
            )

            # Send email notification
            if hasattr(loan.user, 'notification_preferences'):
                if loan.user.notification_preferences.email_due_reminders:
                    try:
                        send_mail(
                            'Library Book Due Tomorrow',
                            f'Dear {loan.user.first_name},\n\n'
                            f'This is a reminder that your book "{loan.book.title}" '
                            f'is due tomorrow ({loan.due_date.strftime("%B %d, %Y")}).\n\n'
                            f'Please return it to the library to avoid late fees.\n\n'
                            f'Best regards,\nLibrary Management System',
                            settings.DEFAULT_FROM_EMAIL,
                            [loan.user.email],
                            fail_silently=True,
                        )
                        count += 1
                    except Exception as e:
                        self.stdout.write(
                            self.style.ERROR(f'Failed to send email to {loan.user.email}: {str(e)}')
                        )

        self.stdout.write(
            self.style.SUCCESS(f'Successfully sent {count} due date reminders')
        )