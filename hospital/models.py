from django.db import models
from accounts.models import User


class Department(models.Model):
    department_name = models.CharField(max_length=100, unique=True)
    room_number = models.CharField(max_length=20)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.department_name


class Doctor(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="doctor_profile"
    )

    department = models.ForeignKey(
        Department,
        on_delete=models.CASCADE,
        related_name="doctors"
    )

    SPECIALIZATION_CHOICES = [
    ("General Physician", "General Physician"),
    ("Cardiologist", "Cardiologist"),
    ("Neurologist", "Neurologist"),
    ("Orthopedic Surgeon", "Orthopedic Surgeon"),
    ("Dermatologist", "Dermatologist"),
    ("Pediatrician", "Pediatrician"),
    ("Gynecologist", "Gynecologist"),
    ("ENT Specialist", "ENT Specialist"),
    ("Ophthalmologist", "Ophthalmologist"),
    ("Psychiatrist", "Psychiatrist"),
]

    specialization = models.CharField(
        max_length=100,
        choices=SPECIALIZATION_CHOICES,
    )
    consultation_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    license_number = models.CharField(
        max_length=50,
        unique=True
    )

    joining_date = models.DateField()

    phone_number = models.CharField(max_length=15)

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
     return self.user.get_full_name() or self.user.username


class DoctorAvailability(models.Model):

    DAYS = [
        ("Monday", "Monday"),
        ("Tuesday", "Tuesday"),
        ("Wednesday", "Wednesday"),
        ("Thursday", "Thursday"),
        ("Friday", "Friday"),
        ("Saturday", "Saturday"),
        ("Sunday", "Sunday"),
    ]

    doctor = models.ForeignKey(
        Doctor,
        on_delete=models.CASCADE,
        related_name="availabilities"
    )

    day_of_week = models.CharField(
        max_length=20,
        choices=DAYS
    )

    start_time = models.TimeField()

    end_time = models.TimeField()

    is_available = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
     return f"{self.doctor} - {self.day_of_week}"
class DoctorLeave(models.Model):

    doctor = models.ForeignKey(
        Doctor,
        on_delete=models.CASCADE,
        related_name="leave_dates"
    )

    leave_date = models.DateField()

    reason = models.CharField(
        max_length=200,
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        unique_together = ("doctor", "leave_date")
        ordering = ["leave_date"]

    def __str__(self):
        return f"Dr. {self.doctor} - Leave on {self.leave_date}"
from django.utils import timezone

class DoctorAttendance(models.Model):

    STATUS_CHOICES = [
        ("AVAILABLE", "Available"),
        ("BUSY", "Busy"),
        ("EMERGENCY", "Emergency"),
        ("LEAVE", "Leave"),
    ]

    doctor = models.ForeignKey(
        Doctor,
        on_delete=models.CASCADE,
        related_name="attendance_records"
    )

    attendance_date = models.DateField(
        default=timezone.now
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="ABSENT"
    )

    check_in_time = models.TimeField(
        null=True,
        blank=True
    )

    check_out_time = models.TimeField(
        null=True,
        blank=True
    )

    class Meta:
        unique_together = ("doctor", "attendance_date")
class DoctorStatus(models.Model):

    STATUS_CHOICES = [
        ("AVAILABLE", "Available"),
        ("BUSY", "Busy"),
        ("EMERGENCY", "Emergency"),
        ("ON_LEAVE", "On Leave"),
        ("NOT_AVAILABLE", "Not Available"),
    ]

    doctor = models.OneToOneField(
        Doctor,
        on_delete=models.CASCADE,
        related_name="current_status"
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="AVAILABLE"
    )

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.doctor} - {self.get_status_display()}"