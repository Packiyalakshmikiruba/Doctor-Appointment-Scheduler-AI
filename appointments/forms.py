from django import forms
from .models import Appointment
from hospital.models import DoctorAvailability


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

            "patient": forms.Select(attrs={
                "class": "form-select"
            }),

            "doctor": forms.Select(attrs={
                "class": "form-select"
            }),

            "appointment_date": forms.DateInput(
                attrs={
                    "class": "form-control",
                    "type": "date",
                }
            ),

            "appointment_time": forms.TimeInput(
                attrs={
                    "class": "form-control",
                    "type": "time",
                }
            ),

            "reason": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Reason for appointment"
                }
            ),

            "status": forms.Select(
                attrs={
                    "class": "form-select"
                }
            ),
        }

    def clean(self):

        cleaned_data = super().clean()

        doctor = cleaned_data.get("doctor")
        appointment_date = cleaned_data.get("appointment_date")
        appointment_time = cleaned_data.get("appointment_time")

        if not doctor or not appointment_date or not appointment_time:
            return cleaned_data

        # ---------------------------------------------------
        # Doctor Availability Check
        # ---------------------------------------------------

        day_name = appointment_date.strftime("%A")

        available = DoctorAvailability.objects.filter(
            doctor=doctor,
            day_of_week=day_name,
            is_available=True,
        ).first()

        if not available:
            raise forms.ValidationError(
                f"{doctor} is not available on {day_name}."
            )

        if (
            appointment_time < available.start_time
            or
            appointment_time > available.end_time
        ):
            raise forms.ValidationError(
                f"Doctor is available only between "
                f"{available.start_time} and {available.end_time}."
            )

        # ---------------------------------------------------
        # Double Booking Check
        # ---------------------------------------------------

        duplicate = Appointment.objects.filter(
            doctor=doctor,
            appointment_date=appointment_date,
            appointment_time=appointment_time,
        )

        # Update செய்யும்போது தன்னையே ignore பண்ணும்
        if self.instance.pk:
            duplicate = duplicate.exclude(pk=self.instance.pk)

        if duplicate.exists():

            raise forms.ValidationError(
                "This doctor already has an appointment at this time."
            )

        return cleaned_data