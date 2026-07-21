from django import forms
from django.utils import timezone

from .models import MedicalRecord
from appointments.models import Appointment


class MedicalRecordForm(forms.ModelForm):

    class Meta:

        model = MedicalRecord

        fields = [
            "appointment",
            "symptoms",
            "diagnosis",
            "treatment",
            "notes",
            "follow_up_date",
        ]

        widgets = {

            "appointment": forms.Select(
                attrs={
                    "class": "form-select"
                }
            ),

            "symptoms": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Enter symptoms"
                }
            ),

            "diagnosis": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Diagnosis"
                }
            ),

            "treatment": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Treatment Plan"
                }
            ),

            "notes": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Additional Notes"
                }
            ),

            "follow_up_date": forms.DateInput(
                attrs={
                    "class": "form-control",
                    "type": "date"
                }
            ),
        }

    def __init__(self, *args, **kwargs):

        doctor = kwargs.pop("doctor", None)

        super().__init__(*args, **kwargs)

        queryset = Appointment.objects.filter(
            status="Confirmed",
            medical_record__isnull=True
        )

        # Update page-ல் current appointment-யும் காட்ட வேண்டும்
        if self.instance.pk:
            queryset = queryset | Appointment.objects.filter(
                pk=self.instance.appointment_id
            )

        if doctor:
            queryset = queryset.filter(
                doctor=doctor
            )

        self.fields["appointment"].queryset = queryset.select_related(
            "doctor__user",
            "patient__user",
        ).distinct()

        self.fields["appointment"].label_from_instance = self.appointment_label

    def appointment_label(self, obj):

        return (
            f"{obj.appointment_date} | "
            f"{obj.appointment_time} | "
            f"{obj.patient.user.get_full_name()} | "
            f"{obj.reason}"
        )

    # Diagnosis Required
    def clean_diagnosis(self):

        diagnosis = self.cleaned_data.get("diagnosis")

        if not diagnosis or not diagnosis.strip():

            raise forms.ValidationError(
                "Diagnosis is required."
            )

        return diagnosis

    # Symptoms Required
    def clean_symptoms(self):

        symptoms = self.cleaned_data.get("symptoms")

        if not symptoms or not symptoms.strip():

            raise forms.ValidationError(
                "Symptoms are required."
            )

        return symptoms

    # Follow-up Date Validation
    def clean_follow_up_date(self):

        follow = self.cleaned_data.get("follow_up_date")

        if follow and follow < timezone.now().date():

            raise forms.ValidationError(
                "Follow-up date cannot be in the past."
            )

        return follow

    # Prevent Duplicate Medical Record
    def clean_appointment(self):

        appointment = self.cleaned_data.get("appointment")

        if (
            appointment
            and MedicalRecord.objects.filter(
                appointment=appointment
            )
            .exclude(pk=self.instance.pk)
            .exists()
        ):

            raise forms.ValidationError(
                "Medical Record already exists for this appointment."
            )

        return appointment