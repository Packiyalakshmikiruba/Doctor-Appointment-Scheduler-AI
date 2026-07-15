from django.db import models
from appointments.models import Appointment


class Prediction(models.Model):

    PREDICTION_CHOICES = [
        ("LOW", "Low Risk"),
        ("MEDIUM", "Medium Risk"),
        ("HIGH", "High Risk"),
    ]

    appointment = models.OneToOneField(
        Appointment,
        on_delete=models.CASCADE,
        related_name="prediction"
    )

    risk_score = models.DecimalField(
        max_digits=5,
        decimal_places=2
    )

    prediction = models.CharField(
        max_length=10,
        choices=PREDICTION_CHOICES
    )

    confidence_score = models.DecimalField(
        max_digits=5,
        decimal_places=2
    )

    model_version = models.CharField(
        max_length=20
    )

    predicted_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"{self.appointment.id} - {self.prediction}"