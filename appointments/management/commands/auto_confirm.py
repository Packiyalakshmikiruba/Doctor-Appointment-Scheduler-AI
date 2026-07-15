"""
Auto-confirms Pending appointments once a reminder has been sent.
Simulates a system that doesn't require explicit patient reply --
sending the reminder itself is treated as confirmation trigger.

Run: python manage.py auto_confirm
"""
from django.core.management.base import BaseCommand
from appointments.models import Appointment


class Command(BaseCommand):
    help = "Auto-confirm Pending appointments that have had a reminder sent"

    def handle(self, *args, **kwargs):
        pending = Appointment.objects.filter(
            status="Pending",
            sms_reminder_sent=True,
        )

        count = pending.update(status="Confirmed")

        self.stdout.write(self.style.SUCCESS(f"Auto-confirmed: {count} appointment(s)"))