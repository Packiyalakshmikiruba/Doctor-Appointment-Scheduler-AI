"""
appointments/management/commands/send_day_before_reminders.py

Run daily (e.g. once every morning via Task Scheduler/cron):
    python manage.py send_day_before_reminders
"""

from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from appointments.models import Appointment
from appointments.booking_flow import send_one_day_reminder


class Command(BaseCommand):
    help = "Send 'appointment tomorrow' reminders and auto-confirm them"

    def handle(self, *args, **kwargs):
        tomorrow = (timezone.now() + timedelta(days=1)).date()

        appts = Appointment.objects.filter(
            appointment_date=tomorrow,
            status__in=["Pending", "Confirmed"],
        )

        count = 0
        for appt in appts:
            send_one_day_reminder(appt)
            count += 1

        self.stdout.write(self.style.SUCCESS(f"Day-before reminders sent: {count}"))
