from django import forms
from .models import MedicalRecord
from appointments.models import Appointment


class MedicalRecordForm(forms.ModelForm):

    appointment = forms.ModelChoiceField(
        queryset=Appointment.objects.filter(
            status="Confirmed",
            medical_record__isnull=True
        ).select_related("doctor__user", "patient"),
        widget=forms.Select(attrs={"class": "form-select", "id": "id_appointment"})
    )

    class Meta:
        model = MedicalRecord
        fields = ["appointment", "symptoms", "diagnosis", "notes", "follow_up_date"]
        widgets = {
            "symptoms": forms.Textarea(attrs={"class": "form-control", "rows": 3, "placeholder": "Enter Symptoms"}),
            "diagnosis": forms.Textarea(attrs={"class": "form-control", "rows": 3, "placeholder": "Enter Diagnosis"}),
            "notes": forms.Textarea(attrs={"class": "form-control", "rows": 2, "placeholder": "Additional Notes"}),
            "follow_up_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
        }