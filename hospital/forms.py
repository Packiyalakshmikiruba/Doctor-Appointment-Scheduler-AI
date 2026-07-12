from django import forms
from .models import Department


class DepartmentForm(forms.ModelForm):

    class Meta:
        model = Department

        fields = [
            "department_name",
            "room_number",
            "description",
        ]

        widgets = {
            "department_name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter Department Name"
            }),

            "room_number": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter Room Number"
            }),

            "description": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": "Enter Description"
            }),
        }