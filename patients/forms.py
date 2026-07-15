from django import forms
from django.contrib.auth import get_user_model
from .models import Patient

User = get_user_model()


class PatientForm(forms.ModelForm):
    # ... existing self-service form, unchanged ...
    class Meta:
        model = Patient
        fields = ["gender", "date_of_birth", "blood_group", "phone_number", "address", "distance_from_clinic", "emergency_contact"]
        widgets = {
            "gender": forms.Select(attrs={"class": "form-select"}),
            "date_of_birth": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "blood_group": forms.Select(attrs={"class": "form-select"}),
            "phone_number": forms.TextInput(attrs={"class": "form-control"}),
            "address": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "distance_from_clinic": forms.NumberInput(attrs={"class": "form-control"}),
            "emergency_contact": forms.TextInput(attrs={"class": "form-control"}),
        }


class AdminPatientForm(forms.ModelForm):
    """Used by admin/staff to register a patient on someone's behalf."""

    user = forms.ModelChoiceField(
        queryset=User.objects.filter(role="PATIENT", patient_profile__isnull=True),
        widget=forms.Select(attrs={"class": "form-select"}),
        help_text="Only shows PATIENT accounts that don't have a profile yet."
    )

    class Meta:
        model = Patient
        fields = ["user", "gender", "date_of_birth", "blood_group", "phone_number", "address", "distance_from_clinic", "emergency_contact"]
        widgets = {
            "gender": forms.Select(attrs={"class": "form-select"}),
            "date_of_birth": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "blood_group": forms.Select(attrs={"class": "form-select"}),
            "phone_number": forms.TextInput(attrs={"class": "form-control"}),
            "address": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "distance_from_clinic": forms.NumberInput(attrs={"class": "form-control"}),
            "emergency_contact": forms.TextInput(attrs={"class": "form-control"}),
        }