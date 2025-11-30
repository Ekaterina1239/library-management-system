from django.core.management.base import BaseCommand
from django.contrib.sessions.models import Session
from django.utils import timezone


class Command(BaseCommand):
    help = 'Clear all user sessions'

    def handle(self, *args, **options):
        sessions = Session.objects.all()
        count = sessions.count()
        sessions.delete()

        self.stdout.write(
            self.style.SUCCESS(f'Successfully cleared {count} user sessions')
        )