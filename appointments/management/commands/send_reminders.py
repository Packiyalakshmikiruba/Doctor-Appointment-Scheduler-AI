"""
Sends reminders for appointments happening within the next 24 hours.
In production this would call an SMS/Email API (Twilio, etc.) --
here it logs the reminder and marks sms_reminder_sent=True.

Run: python manage.py send_reminders
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta, datetime
from appointments.models import Appointment


class Command(BaseCommand):
    help = "Send reminders for appointments happening in the next 24 hours"

    def handle(self, *args, **kwargs):
        now = timezone.now()
        window_end = now + timedelta(hours=24)

        upcoming = Appointment.objects.filter(
            status__in=["Pending", "Confirmed"],
            sms_reminder_sent=False,
        )

        sent_count = 0

        for appt in upcoming:
            appt_datetime = datetime.combine(appt.appointment_date, appt.appointment_time)
            appt_datetime = timezone.make_aware(appt_datetime)

            if now <= appt_datetime <= window_end:
                # Simulated SMS/Email send -- replace with real gateway later
                self.stdout.write(
                    f"[REMINDER] To {appt.patient}: Your appointment with "
                    f"Dr. {appt.doctor.user.get_full_name() or appt.doctor.user.username} "
                    f"is on {appt.appointment_date} at {appt.appointment_time}."
                )

                appt.sms_reminder_sent = True
                appt.save()
                sent_count += 1

        self.stdout.write(self.style.SUCCESS(f"Reminders sent: {sent_count}"))