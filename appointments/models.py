from django.db import models
from patients.models import Patient
from hospital.models import Doctor

class Appointment(models.Model):

    STATUS_CHOICES = [
        ("BOOKED", "Booked"),
        ("CONFIRMED", "Confirmed"),
        ("COMPLETED", "Completed"),
        ("CANCELLED", "Cancelled"),
        ("NO_SHOW", "No Show"),
    ]

    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name="appointments"
    )

    doctor = models.ForeignKey(
        Doctor,
        on_delete=models.CASCADE,
        related_name="appointments"
    )

    booking_date = models.DateField()

    appointment_date = models.DateField()

    appointment_time = models.TimeField()

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="BOOKED"
    )

    appointment_type = models.CharField(
        max_length=20,
        choices=[
            ("NEW", "New"),
            ("FOLLOW_UP", "Follow Up"),
        ],
        default="NEW"
    )

    consultation_mode = models.CharField(
        max_length=20,
        choices=[
            ("ONLINE", "Online"),
            ("OFFLINE", "Offline"),
        ],
        default="OFFLINE"
    )

    sms_reminder_sent = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.patient.user.get_full_name()} - {self.appointment_date}"