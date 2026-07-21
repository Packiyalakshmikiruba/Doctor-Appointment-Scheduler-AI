from django import forms

from accounts.models import User
from .models import Department, Doctor, DoctorStatus, DoctorLeave, DoctorAvailability


class DepartmentForm(forms.ModelForm):

    class Meta:

        model = Department

        fields = [
            "department_name",
            "room_number",
            "description",
        ]

        widgets = {

            "department_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter Department Name",
                }
            ),

            "room_number": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter Room Number",
                }
            ),

            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Enter Description",
                }
            ),

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

            "user": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),

            "department": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),

           "specialization": forms.Select(
    attrs={
        "class": "form-select"
    }
),

            "consultation_fee": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Consultation Fee",
                }
            ),

            "license_number": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "License Number",
                }
            ),

            "joining_date": forms.DateInput(
                attrs={
                    "class": "form-control",
                    "type": "date",
                }
            ),

            "phone_number": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Phone Number",
                }
            ),

            "is_active": forms.CheckboxInput(
                attrs={
                    "class": "form-check-input",
                }
            ),

        }

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        # Doctor role users மட்டும்
        self.fields["user"].queryset = User.objects.filter(role="DOCTOR")

        # Department list
        self.fields["department"].queryset = Department.objects.all()

        self.fields["user"].label_from_instance = (
            lambda obj: obj.get_full_name() or obj.username
        )

        self.fields["department"].label_from_instance = (
            lambda obj: obj.department_name
        )


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
            "doctor": forms.Select(
                attrs={"class": "form-select"}
            ),

            "day_of_week": forms.Select(
                attrs={"class": "form-select"}
            ),

            "start_time": forms.TimeInput(
                attrs={
                    "class": "form-control",
                    "type": "time",
                }
            ),

            "end_time": forms.TimeInput(
                attrs={
                    "class": "form-control",
                    "type": "time",
                }
            ),

            "is_available": forms.CheckboxInput(
                attrs={"class": "form-check-input"}
            ),
        }

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        self.fields["doctor"].queryset = Doctor.objects.filter(is_active=True)

        self.fields["doctor"].label_from_instance = (
            lambda obj: obj.user.get_full_name() or obj.user.username
        )

    # -------------------------
    # Validation
    # -------------------------

    def clean(self):

        cleaned_data = super().clean()

        start_time = cleaned_data.get("start_time")
        end_time = cleaned_data.get("end_time")

        if start_time and end_time:

            if end_time <= start_time:

                raise forms.ValidationError(
                    "End time must be greater than Start time."
                )

        return cleaned_data
class DoctorLeaveForm(forms.ModelForm):

    class Meta:

        model = DoctorLeave

        fields = [
            "doctor",
            "leave_date",
            "reason",
        ]

        widgets = {

            "leave_date": forms.DateInput(
                attrs={
                    "type": "date"
                }
            ),

            "reason": forms.TextInput(
                attrs={
                    "class": "form-control"
                }
            ),
        }
class DoctorStatusForm(forms.ModelForm):
    class Meta:
        model = DoctorStatus
        fields = ["status"]