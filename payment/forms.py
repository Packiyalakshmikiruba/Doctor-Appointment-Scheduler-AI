from django import forms

from .models import Payment


class PaymentForm(forms.ModelForm):

    class Meta:

        model=Payment

        fields=[
            "payment_method",
            "payment_status",
            "remarks",
        ]

        widgets={

            "payment_method":forms.Select(attrs={
                "class":"form-select"
            }),

            "payment_status":forms.Select(attrs={
                "class":"form-select"
            }),

            "remarks":forms.Textarea(attrs={
                "class":"form-control",
                "rows":3,
                "placeholder":"Enter Remarks (Optional)"
            }),

        }

    def clean(self):

        cleaned_data=super().clean()

        payment_method=cleaned_data.get("payment_method")
        payment_status=cleaned_data.get("payment_status")

        if payment_method=="Cash" and payment_status=="Failed":

            raise forms.ValidationError(
                "Cash payment cannot be marked as Failed."
            )

        return cleaned_data

    def clean_remarks(self):

        remarks=self.cleaned_data.get("remarks")

        if remarks:

            remarks=remarks.strip()

        return remarks