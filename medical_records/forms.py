from django import forms
from .models import MedicalRecord


class MedicalRecordForm(forms.ModelForm):

    class Meta:

        model = MedicalRecord

        fields = [
            "appointment",
            "symptoms",
            "diagnosis",
            "prescription",
            "notes",
            "follow_up_date",
        ]

        widgets = {

            "appointment": forms.Select(attrs={
                "class": "form-select"
            }),

            "symptoms": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 3
            }),

            "diagnosis": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 3
            }),

            "prescription": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 4
            }),

            "notes": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 3
            }),

            "follow_up_date": forms.DateInput(attrs={
                "class": "form-control",
                "type": "date"
            }),

        }