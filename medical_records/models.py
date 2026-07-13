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

    prescription = models.TextField()

    notes = models.TextField(
        blank=True,
        null=True
    )

    follow_up_date = models.DateField(
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Medical Record - {self.appointment.patient}"