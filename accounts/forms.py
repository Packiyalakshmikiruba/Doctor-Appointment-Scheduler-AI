from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import User


class RegisterForm(UserCreationForm):

    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            "class": "form-control",
            "placeholder": "Enter Email"
        })
    )

    class Meta:
        model = User

        fields = (
            "first_name",
            "last_name",
            "username",
            "email",
            "role",
            "password1",
            "password2",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["first_name"].widget.attrs.update({
            "class": "form-control",
            "placeholder": "Enter First Name"
        })

        self.fields["last_name"].widget.attrs.update({
            "class": "form-control",
            "placeholder": "Enter Last Name"
        })

        self.fields["username"].widget.attrs.update({
            "class": "form-control",
            "placeholder": "Enter Username"
        })

        self.fields["role"].widget.attrs.update({
            "class": "form-select"
        })

        self.fields["password1"].widget.attrs.update({
            "class": "form-control",
            "placeholder": "Enter Password"
        })

        self.fields["password2"].widget.attrs.update({
            "class": "form-control",
            "placeholder": "Confirm Password"
        })


class LoginForm(AuthenticationForm):

    username = forms.CharField(
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "Enter Username"
        })
    )

    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            "class": "form-control",
            "placeholder": "Enter Password"
        })
    )