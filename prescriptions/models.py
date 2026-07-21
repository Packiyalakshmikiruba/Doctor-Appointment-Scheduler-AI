from django.db import models
from medical_records.models import MedicalRecord


class Prescription(models.Model):

    FOOD_CHOICES = [
        ("Before Food", "Before Food"),
        ("After Food", "After Food"),
    ]

    FREQUENCY_CHOICES = [
        ("Once Daily", "Once Daily"),
        ("Twice Daily", "Twice Daily"),
        ("Three Times Daily", "Three Times Daily"),
        ("Every 6 Hours", "Every 6 Hours"),
        ("Every 8 Hours", "Every 8 Hours"),
        ("SOS", "SOS"),
    ]

    medical_record = models.ForeignKey(
        MedicalRecord,
        on_delete=models.CASCADE,
        related_name="prescriptions"
    )

    medicine_name = models.CharField(max_length=100)

    dosage = models.CharField(
        max_length=50,
        help_text="Example: 500 mg / 1 Tablet"
    )

    frequency = models.CharField(
        max_length=30,
        choices=FREQUENCY_CHOICES
    )

    duration = models.PositiveIntegerField(
        help_text="Duration in Days"
    )

    before_after_food = models.CharField(
        max_length=20,
        choices=FOOD_CHOICES
    )

    instructions = models.TextField(
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        ordering = ["medicine_name"]

    def __str__(self):
        return f"{self.medicine_name} - {self.medical_record.patient.user.get_full_name()}"