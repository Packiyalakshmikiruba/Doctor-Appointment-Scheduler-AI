from django import forms
from .models import Payment


class PaymentForm(forms.ModelForm):

    class Meta:

        model = Payment

        fields = [
            "payment_method",
            "payment_status",
            "remarks",
        ]

        widgets = {

            "payment_method": forms.Select(
                attrs={
                    "class": "form-select"
                }
            ),

            "payment_status": forms.Select(
                attrs={
                    "class": "form-select"
                }
            ),

            "remarks": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Remarks (Optional)"
                }
            ),
        }