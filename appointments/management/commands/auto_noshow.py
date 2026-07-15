"""
Marks appointments as "No Show" automatically once their scheduled
time has passed and no one manually marked them Completed/Cancelled.

Run: python manage.py auto_noshow
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime
from appointments.models import Appointment


class Command(BaseCommand):
    help = "Auto-mark past Pending/Confirmed appointments as No Show"

    def handle(self, *args, **kwargs):
        now = timezone.now()

        candidates = Appointment.objects.filter(status__in=["Pending", "Confirmed"])
        marked = 0

        for appt in candidates:
            appt_datetime = datetime.combine(appt.appointment_date, appt.appointment_time)
            appt_datetime = timezone.make_aware(appt_datetime)

            # Give a 30-minute grace period after the scheduled time
            if now > appt_datetime + timezone.timedelta(minutes=30):
                appt.status = "No Show"
                appt.save()
                marked += 1
                self.stdout.write(
                    f"[NO-SHOW] {appt.patient} missed appointment on "
                    f"{appt.appointment_date} at {appt.appointment_time}"
                )

        self.stdout.write(self.style.SUCCESS(f"Marked as No Show: {marked} appointment(s)"))