from django import forms
from django.forms import inlineformset_factory
from .models import Prescription
from medical_records.models import MedicalRecord


class PrescriptionForm(forms.ModelForm):
    class Meta:
        model = Prescription
        fields = ["medicine_name", "dosage", "frequency", "duration", "before_after_food", "instructions"]
        widgets = {
            "medicine_name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Medicine name"}),
            "dosage": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. 500mg"}),
            "frequency": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. Twice a day"}),
            "duration": forms.NumberInput(attrs={"class": "form-control", "placeholder": "Days"}),
            "before_after_food": forms.Select(attrs={"class": "form-select"}),
            "instructions": forms.TextInput(attrs={"class": "form-control", "placeholder": "Optional instructions"}),
        }


PrescriptionFormSet = inlineformset_factory(
    MedicalRecord,
    Prescription,
    form=PrescriptionForm,
    extra=3,
    can_delete=True
)