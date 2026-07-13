from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect

from .forms import RegisterForm, LoginForm


def register_view(request):

    if request.method == "POST":

        form = RegisterForm(request.POST)

        if form.is_valid():

            user = form.save(commit=False)

            # Public registration always creates a patient
            user.role = "PATIENT"

            user.save()

            login(request, user)

            messages.success(
                request,
                "Registration Successful."
            )

            return redirect("patient_dashboard")

    else:

        form = RegisterForm()

    return render(
        request,
        "accounts/register.html",
        {
            "form": form
        }
    )


def login_view(request):

    if request.method == "POST":

        form = LoginForm(
            request,
            data=request.POST
        )

        if form.is_valid():

            user = form.get_user()

            login(
                request,
                user
            )

            messages.success(
                request,
                "Login Successful."
            )

            if user.role == "ADMIN":
                return redirect("admin_dashboard")

            elif user.role == "DOCTOR":
                return redirect("doctor_dashboard")

            elif user.role == "PATIENT":
                return redirect("patient_dashboard")

            else:
                return redirect("login")

        else:

            messages.error(
                request,
                "Invalid username or password."
            )

    else:

        form = LoginForm()

    return render(
        request,
        "accounts/login.html",
        {
            "form": form
        }
    )


@login_required
def logout_view(request):

    logout(request)

    messages.success(
        request,
        "Logged Out Successfully."
    )

    return redirect("login")