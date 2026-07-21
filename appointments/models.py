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
        Patient, on_delete=models.CASCADE, related_name="appointments"
    )

    doctor = models.ForeignKey(
        Doctor, on_delete=models.CASCADE, related_name="appointments"
    )

    appointment_date = models.DateField()

    appointment_time = models.TimeField(default="09:00")   # ← புதுசா சேர்த்தது, இதுவே missing field

    reason = models.TextField()

    sms_reminder_sent = models.BooleanField(default=False)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="Pending")

    # AI Prediction Output
    risk_score = models.FloatField(null=True, blank=True, editable=False)
    risk_level = models.CharField(max_length=10, choices=RISK_LEVEL_CHOICES, blank=True, editable=False)

    # AI Prediction Inputs (auto-filled by signal, not user input)
    prior_visits = models.PositiveIntegerField(default=0, editable=False)
    prior_noshows = models.PositiveIntegerField(default=0, editable=False)
    history_noshow_ratio = models.FloatField(default=0, editable=False)
    distance_from_clinic = models.FloatField(default=0, editable=False)
    patient_checked_in = models.BooleanField(
    default=False
)

# Consultation Completed Time
    consultation_completed_at = models.DateTimeField(
        null=True,
        blank=True
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
        booking_date = self.created_at.date() if self.created_at else timezone.now().date()
        return max((self.appointment_date - booking_date).days, 0)

    @property
    def appointment_weekday(self):
        return self.appointment_date.strftime("%A")

    @property
    def time_bucket(self):
        hour = self.appointment_time.hour
        if hour < 12:
            return "Morning"
        elif hour < 17:
            return "Afternoon"
        else:
            return "Evening"
class Waitlist(models.Model):
    """
    A patient who wants an appointment with a specific doctor but couldn't
    get their preferred slot. When another patient cancels, the earliest
    waitlist entry for that doctor gets offered the freed slot.
    """

    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="waitlist_entries")
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name="waitlist_entries")
    preferred_date = models.DateField(null=True, blank=True)
    notified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.patient} waiting for Dr. {self.doctor}"

