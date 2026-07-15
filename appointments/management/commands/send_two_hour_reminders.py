"""
appointments/management/commands/send_two_hour_reminders.py

Run frequently (e.g. every 15-30 minutes via Task Scheduler/cron):
    python manage.py send_two_hour_reminders
"""

from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from appointments.models import Appointment
from appointments.booking_flow import send_two_hour_reminder


class Command(BaseCommand):
    help = "Send 'appointment in 2 hours' reminders"

    def handle(self, *args, **kwargs):
        now = timezone.now()
        target_start = now + timedelta(hours=2)
        target_end = target_start + timedelta(minutes=30)  # command run window

        appts = Appointment.objects.filter(status="Confirmed")

        count = 0
        for appt in appts:
            naive_dt = timezone.datetime.combine(appt.appointment_date, appt.appointment_time)
            appt_datetime = timezone.make_aware(naive_dt) if timezone.is_naive(naive_dt) else naive_dt

            if target_start <= appt_datetime <= target_end:
                send_two_hour_reminder(appt)
                count += 1

        self.stdout.write(self.style.SUCCESS(f"Two-hour reminders sent: {count}"))
