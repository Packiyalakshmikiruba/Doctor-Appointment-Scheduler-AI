from django.db import models
from django.utils import timezone
from patients.models import Patient
from hospital.models import Doctor


class Appointment(models.Model):

    STATUS_CHOICES = [
        ("Pending", "Pending"),
        ("Confirmed", "Confirmed"),
        ("Completed", "Completed"),
        ("Cancelled", "Cancelled"),
        ("No Show", "No Show"),
    ]

    RISK_LEVEL_CHOICES = [
        ("LOW", "Low"),
        ("MEDIUM", "Medium"),
        ("HIGH", "High"),
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

    appointment_date = models.DateField()

    appointment_time = models.TimeField()

    reason = models.TextField()

    # AI Feature
    sms_reminder_sent = models.BooleanField(default=False)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="Pending"
    )

    # AI Prediction Output
    risk_score = models.FloatField(
        null=True,
        blank=True,
        editable=False
    )

    risk_level = models.CharField(
        max_length=10,
        choices=RISK_LEVEL_CHOICES,
        blank=True,
        editable=False
    )

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-appointment_date", "-appointment_time"]

    def __str__(self):
        return (
            f"{self.patient.user.get_full_name()} "
            f"- Dr. {self.doctor.user.get_full_name()}"
        )

    @property
    def lead_time_days(self):
        booking_date = (
            self.created_at.date()
            if self.created_at
            else timezone.now().date()
        )

        return max(
            (self.appointment_date - booking_date).days,
            0
        )

    @property
    def appointment_weekday(self):
        return self.appointment_date.strftime("%A")