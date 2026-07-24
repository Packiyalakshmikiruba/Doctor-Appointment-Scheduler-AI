from django import forms
from django.forms import inlineformset_factory

from .models import Prescription
from medical_records.models import MedicalRecord


class PrescriptionForm(forms.ModelForm):

    class Meta:
        model = Prescription

        fields = [
            "medicine_name",
            "dosage",
            "frequency",
            "duration",
            "before_after_food",
            "instructions",
        ]

        widgets = {

            "medicine_name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Medicine Name"
            }),

            "dosage": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Example : 500 mg / 1 Tablet"
            }),

            "frequency": forms.Select(attrs={
                "class": "form-select"
            }),

            "duration": forms.NumberInput(attrs={
                "class": "form-control",
                "min": 1,
                "placeholder": "Number of Days"
            }),

            "before_after_food": forms.Select(attrs={
                "class": "form-select"
            }),

            "instructions": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 2,
                "placeholder": "Additional Instructions (Optional)"
            }),
        }

    # Optional fields
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["before_after_food"].required = False
        self.fields["instructions"].required = False

    def clean_medicine_name(self):

        medicine = self.cleaned_data.get("medicine_name")

        if not medicine or not medicine.strip():
            raise forms.ValidationError(
                "Medicine name is required."
            )

        return medicine.title()

    def clean_duration(self):

        duration = self.cleaned_data.get("duration")

        if duration <= 0:
            raise forms.ValidationError(
                "Duration must be greater than zero."
            )

        return duration

    def clean_dosage(self):

        dosage = self.cleaned_data.get("dosage")

        if not dosage or not dosage.strip():
            raise forms.ValidationError(
                "Dosage is required."
            )

        return dosage

    def clean(self):

        cleaned_data = super().clean()

        medicine = cleaned_data.get("medicine_name")
        dosage = cleaned_data.get("dosage")

        if medicine and dosage:
            cleaned_data["medicine_name"] = medicine.title()

        return cleaned_data


PrescriptionFormSet = inlineformset_factory(

    MedicalRecord,

    Prescription,

    form=PrescriptionForm,

    extra=1,

    can_delete=True,

    min_num=1,

    validate_min=True,

)