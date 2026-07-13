from django.db import models
from medical_records.models import MedicalRecord


class Prescription(models.Model):

    FOOD_CHOICES = [

        ("Before Food", "Before Food"),

        ("After Food", "After Food"),

    ]

    medical_record = models.ForeignKey(

        MedicalRecord,

        on_delete=models.CASCADE,

        related_name="prescriptions"

    )

    medicine_name = models.CharField(max_length=100)

    dosage = models.CharField(max_length=50)

    frequency = models.CharField(max_length=20)

    duration = models.PositiveIntegerField()

    before_after_food = models.CharField(

        max_length=20,

        choices=FOOD_CHOICES

    )

    instructions = models.TextField(

        blank=True,

        null=True

    )

    def __str__(self):

        return self.medicine_name