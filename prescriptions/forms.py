from django import forms
from django.forms import inlineformset_factory
from .models import Prescription
from medical_records.models import MedicalRecord


class PrescriptionForm(forms.ModelForm):
    class Meta:
        model = Prescription
        fields = ["medicine_name", "dosage", "frequency", "duration", "instructions"]
        widgets = {
            "medicine_name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Medicine name"}),
            "dosage": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. 500mg"}),
            "frequency": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. Twice a day"}),
            "duration": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. 5 days"}),
            "instructions": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. After food"}),
        }


PrescriptionFormSet = inlineformset_factory(
    MedicalRecord,
    Prescription,
    form=PrescriptionForm,
    extra=3,          # 3 empty rows initially, JS-ல "add more" button add பண்ணலாம்
    can_delete=True
)