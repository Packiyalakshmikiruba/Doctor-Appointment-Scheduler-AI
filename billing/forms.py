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
from .models import Bill, Payment


class PaymentForm(forms.ModelForm):

    class Meta:
        model = Payment
        fields = ["amount_paid", "payment_mode", "transaction_reference"]
        widgets = {
            "amount_paid": forms.NumberInput(attrs={"class": "form-control", "placeholder": "Amount"}),
            "payment_mode": forms.Select(attrs={"class": "form-select"}),
            "transaction_reference": forms.TextInput(attrs={"class": "form-control", "placeholder": "Optional reference"}),
        }