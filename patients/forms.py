from django import forms
from .models import Patient


class PatientForm(forms.ModelForm):

    class Meta:
        model = Patient
        fields = [
            "gender",
            "date_of_birth",
            "blood_group",
            "phone_number",
            "address",
            "distance_from_clinic",
            "emergency_contact",
        ]

        widgets = {
            "gender": forms.Select(attrs={"class": "form-select"}),
            "date_of_birth": forms.DateInput(attrs={
                "class": "form-control", "type": "date"
            }),
            "blood_group": forms.Select(attrs={"class": "form-select"}),
            "phone_number": forms.TextInput(attrs={
                "class": "form-control", "placeholder": "e.g. 9876543210"
            }),
            "address": forms.Textarea(attrs={
                "class": "form-control", "rows": 3, "placeholder": "Full address"
            }),
            "distance_from_clinic": forms.NumberInput(attrs={
                "class": "form-control", "placeholder": "Distance in km", "step": "0.1"
            }),
            "emergency_contact": forms.TextInput(attrs={
                "class": "form-control", "placeholder": "Emergency contact number"
            }),
        }