from django import forms
from .models import Department, Doctor, DoctorAvailability
from .models import Doctor

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
class DoctorForm(forms.ModelForm):

    class Meta:
        model = Doctor

        fields = [
            "user",
            "department",
            "specialization",
            "consultation_fee",
            "license_number",
            "joining_date",
            "phone_number",
            "is_active",
        ]

        widgets = {

            "user": forms.Select(attrs={
                "class": "form-select"
            }),

            "department": forms.Select(attrs={
                "class": "form-select"
            }),

            "specialization": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter Specialization"
            }),

            "consultation_fee": forms.NumberInput(attrs={
                "class": "form-control",
                "placeholder": "Consultation Fee"
            }),

            "license_number": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "License Number"
            }),

            "joining_date": forms.DateInput(attrs={
                "class": "form-control",
                "type": "date"
            }),

            "phone_number": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Phone Number"
            }),

            "is_active": forms.CheckboxInput(attrs={
                "class": "form-check-input"
            }),

        }
class DoctorAvailabilityForm(forms.ModelForm):

    class Meta:
        model = DoctorAvailability

        fields = [
            "doctor",
            "day_of_week",
            "start_time",
            "end_time",
            "is_available",
        ]

        widgets = {

            "doctor": forms.Select(attrs={
                "class": "form-select"
            }),

            "day_of_week": forms.Select(attrs={
                "class": "form-select"
            }),

            "start_time": forms.TimeInput(attrs={
                "class": "form-control",
                "type": "time"
            }),

            "end_time": forms.TimeInput(attrs={
                "class": "form-control",
                "type": "time"
            }),

            "is_available": forms.CheckboxInput(attrs={
                "class": "form-check-input"
            }),

        }