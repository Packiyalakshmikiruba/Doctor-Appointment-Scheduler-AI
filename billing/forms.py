from django import forms
from .models import Bill


class BillForm(forms.ModelForm):

    class Meta:

        model = Bill

        fields = [
            "appointment",
            "consultation_fee",
            "medicine_cost",
            "lab_test_cost",
            "discount",
            "gst",
            "payment_status",
        ]

        widgets = {

            "appointment": forms.Select(attrs={
                "class": "form-select"
            }),

            "consultation_fee": forms.NumberInput(attrs={
                "class": "form-control"
            }),

            "medicine_cost": forms.NumberInput(attrs={
                "class": "form-control"
            }),

            "lab_test_cost": forms.NumberInput(attrs={
                "class": "form-control"
            }),

            "discount": forms.NumberInput(attrs={
                "class": "form-control"
            }),

            "gst": forms.NumberInput(attrs={
                "class": "form-control"
            }),

            "payment_status": forms.Select(attrs={
                "class": "form-select"
            }),

        }