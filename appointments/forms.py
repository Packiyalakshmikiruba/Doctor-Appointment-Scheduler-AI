from django import forms
from django.core.exceptions import ValidationError
from datetime import date

from .models import Appointment
from patients.models import Patient
from hospital.models import Doctor, DoctorAvailability


class AppointmentForm(forms.ModelForm):

    class Meta:

        model = Appointment

        fields = [
            "patient",
            "doctor",
            "appointment_date",
            "appointment_time",
            "reason",
            "status",
        ]

        widgets = {

            "patient": forms.Select(attrs={
                "class": "form-select"
            }),

            "doctor": forms.Select(attrs={
                "class": "form-select"
            }),

            "appointment_date": forms.DateInput(attrs={
                "class": "form-control",
                "type": "date"
            }),

            "appointment_time": forms.TimeInput(attrs={
                "class": "form-control",
                "type": "time"
            }),

            "reason": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": "Enter Appointment Reason"
            }),

            "status": forms.Select(attrs={
                "class": "form-select"
            }),

        }

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        self.fields["patient"].queryset = Patient.objects.select_related("user")
        self.fields["doctor"].queryset = Doctor.objects.select_related("user")

    # Past Date Validation
    def clean_appointment_date(self):

        appointment_date = self.cleaned_data.get("appointment_date")

        if appointment_date < date.today():
            raise ValidationError(
                "Past date is not allowed."
            )

        return appointment_date

    # Business Validations
    def clean(self):

        cleaned_data = super().clean()

        doctor = cleaned_data.get("doctor")
        appointment_date = cleaned_data.get("appointment_date")
        appointment_time = cleaned_data.get("appointment_time")

        if not doctor or not appointment_date or not appointment_time:
            return cleaned_data

        # ---------------------------------
        # Doctor Availability Check
        # ---------------------------------

        weekday = appointment_date.strftime("%A")

        availability = DoctorAvailability.objects.filter(
            doctor=doctor,
            day_of_week=weekday,
            is_available=True
        ).first()

        if not availability:

            raise ValidationError(
                f"{doctor} is not available on {weekday}."
            )

        if (
            appointment_time < availability.start_time or
            appointment_time > availability.end_time
        ):

            raise ValidationError(
                "Selected time is outside doctor's working hours."
            )

        # ---------------------------------
        # Double Booking Validation
        # ---------------------------------

        appointment = Appointment.objects.filter(
            doctor=doctor,
            appointment_date=appointment_date,
            appointment_time=appointment_time,
        )

        # Update page-க்கு
        if self.instance.pk:
            appointment = appointment.exclude(pk=self.instance.pk)

        if appointment.exists():

            raise ValidationError(
                "Doctor already has an appointment at this time."
            )

        return cleaned_data