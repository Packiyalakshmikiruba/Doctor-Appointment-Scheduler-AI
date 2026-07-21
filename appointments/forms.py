from django import forms
from django.utils import timezone

from .models import Appointment
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
        ]

        widgets = {
            "patient": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),

            "doctor": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),

            "appointment_date": forms.DateInput(
                format="%Y-%m-%d",
                attrs={
                    "type": "date",
                    "class": "form-control",
                },
            ),

            "appointment_time": forms.TimeInput(
                format="%H:%M",
                attrs={
                    "type": "time",
                    "class": "form-control",
                },
            ),

            "reason": forms.Textarea(
                attrs={
                    "rows": 4,
                    "class": "form-control",
                    "placeholder": "Reason for visit",
                }
            ),
        }

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        self.fields["appointment_date"].input_formats = [
            "%Y-%m-%d",
        ]

        self.fields["appointment_time"].input_formats = [
            "%H:%M",
        ]

        self.fields["doctor"].queryset = (
            Doctor.objects.filter(is_active=True)
            .select_related("user", "department")
            .order_by("user__first_name")
        )

        self.fields["doctor"].label_from_instance = (
            lambda obj: f"Dr. {obj.user.get_full_name() or obj.user.username}"
            f" - {obj.department.department_name}"
        )

    def clean(self):

        cleaned_data = super().clean()

        patient = cleaned_data.get("patient")
        doctor = cleaned_data.get("doctor")
        appointment_date = cleaned_data.get("appointment_date")
        appointment_time = cleaned_data.get("appointment_time")

        if not patient or not doctor or not appointment_date or not appointment_time:
            return cleaned_data

        # ----------------------------------------
        # Future Date Validation
        # ----------------------------------------

        if appointment_date < timezone.localdate():
            raise forms.ValidationError(
                "Past dates cannot be booked."
            )

        # ----------------------------------------
        # Doctor Availability
        # ----------------------------------------

        day_name = appointment_date.strftime("%A")

        availability = DoctorAvailability.objects.filter(
            doctor=doctor,
            day_of_week=day_name,
            is_available=True,
        ).first()

        if availability is None:
            raise forms.ValidationError(
                f"Dr. {doctor.user.get_full_name()} is not available on {day_name}."
            )

        if not (
            availability.start_time <= appointment_time <= availability.end_time
        ):
            raise forms.ValidationError(
                f"Doctor is available only between "
                f"{availability.start_time.strftime('%I:%M %p')} "
                f"and "
                f"{availability.end_time.strftime('%I:%M %p')}."
            )

        # ----------------------------------------
        # Doctor Double Booking
        # ----------------------------------------

        doctor_duplicate = Appointment.objects.filter(
            doctor=doctor,
            appointment_date=appointment_date,
            appointment_time=appointment_time,
        )

        if self.instance.pk:
            doctor_duplicate = doctor_duplicate.exclude(pk=self.instance.pk)

        if doctor_duplicate.exists():
            raise forms.ValidationError(
                "Doctor already has another appointment at this time."
            )

        # ----------------------------------------
        # Patient Double Booking
        # ----------------------------------------

        patient_duplicate = Appointment.objects.filter(
            patient=patient,
            appointment_date=appointment_date,
            appointment_time=appointment_time,
        )

        if self.instance.pk:
            patient_duplicate = patient_duplicate.exclude(pk=self.instance.pk)

        if patient_duplicate.exists():
            raise forms.ValidationError(
                "Patient already has another appointment at this time."
            )

        return cleaned_data