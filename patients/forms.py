from django import forms
from .models import Patient
from accounts.models import User


class PatientForm(forms.ModelForm):

    class Meta:

        model = Patient

        fields = [
            "user",
            "gender",
            "date_of_birth",
            "blood_group",
            "phone_number",
            "address",
            "distance_from_clinic",
            "emergency_contact",
        ]

        widgets = {

            "user": forms.Select(attrs={
                "class": "form-select"
            }),

            "gender": forms.Select(attrs={
                "class": "form-select"
            }),

            "date_of_birth": forms.DateInput(attrs={
                "class": "form-control",
                "type": "date"
            }),

            "blood_group": forms.Select(attrs={
                "class": "form-select"
            }),

            "phone_number": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Phone Number"
            }),

            "address": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": "Address"
            }),

            "distance_from_clinic": forms.NumberInput(attrs={
                "class": "form-control",
                "placeholder": "Distance from Clinic (KM)"
            }),

            "emergency_contact": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Emergency Contact"
            }),

        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Patient role users மட்டும்
        self.fields["user"].queryset = User.objects.filter(role="PATIENT")