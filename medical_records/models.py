from django.db import models
from appointments.models import Appointment


class MedicalRecord(models.Model):

    appointment = models.OneToOneField(
        Appointment,
        on_delete=models.CASCADE,
        related_name="medical_record"
    )

    symptoms = models.TextField()

    diagnosis = models.TextField()

    treatment = models.TextField(
        blank=True,
        null=True
    )

    notes = models.TextField(
        blank=True,
        null=True
    )

    follow_up_date = models.DateField(
        blank=True,
        null=True
    )

    # NEW
    consultation_duration = models.PositiveIntegerField(
        blank=True,
        null=True,
        help_text="Duration in minutes"
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return (
            f"{self.appointment.patient.user.get_full_name()} "
            f"- {self.appointment.appointment_date}"
        )

    @property
    def doctor(self):
        return self.appointment.doctor

    @property
    def patient(self):
        return self.appointment.patient

    @property
    def appointment_status(self):
        return self.appointment.status

    @property
    def risk_level(self):
        return self.appointment.risk_level

    @property
    def consultation_completed(self):
        return self.appointment.status == "Completed"