from django.db import models
from accounts.models import User


class Patient(models.Model):

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="patient_profile"
    )

    gender = models.CharField(max_length=10)

    date_of_birth = models.DateField()

    blood_group = models.CharField(max_length=5)

    phone_number = models.CharField(max_length=15)

    address = models.TextField()

    distance_from_clinic = models.DecimalField(
        max_digits=5,
        decimal_places=2
    )

    emergency_contact = models.CharField(max_length=15)

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.user.get_full_name()