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

            # Save selected role
            user.role = form.cleaned_data["role"]

            user.save()

            login(request, user)

            messages.success(
                request,
                "Registration Successful."
            )

            if user.role == "ADMIN":
                return redirect("admin_dashboard")

            elif user.role == "DOCTOR":
                return redirect("doctor_dashboard")

            else:
                return redirect("dashboard")

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
                return redirect("dashboard")

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
from django.contrib.auth.decorators import login_required


from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils import timezone
from appointments.models import Appointment


@login_required
def dashboard(request):

    if request.user.role == "PATIENT":

        if not hasattr(request.user, "patient_profile"):
            messages.info(request, "Please complete your profile to continue.")
            return redirect("complete_profile")

        patient = request.user.patient_profile

        upcoming = Appointment.objects.filter(
            patient=patient,
            status__in=["Pending", "Confirmed"],
            appointment_date__gte=timezone.now().date()
        ).select_related("doctor__user", "doctor__department").order_by("appointment_date")

        history = Appointment.objects.filter(
            patient=patient,
            status__in=["Completed", "Cancelled", "No Show"]
        ).select_related("doctor__user").order_by("-appointment_date")[:10]

        high_risk_count = upcoming.filter(risk_level="HIGH").count()

        return render(request, "accounts/patient_dashboard.html", {
            "upcoming": upcoming,
            "history": history,
            "high_risk_count": high_risk_count,
        })

    elif request.user.role == "DOCTOR":

        if not hasattr(request.user, "doctor_profile"):
            messages.info(request, "Doctor profile not set up yet. Contact admin.")
            return render(request, "accounts/dashboard.html")

        doctor = request.user.doctor_profile
        today = timezone.now().date()

        todays_appointments = Appointment.objects.filter(
            doctor=doctor,
            appointment_date=today,
            status__in=["Pending", "Confirmed"]
        ).select_related("patient__user").order_by("appointment_time")

        high_risk_today = todays_appointments.filter(risk_level="HIGH")

        total_noshows = Appointment.objects.filter(doctor=doctor, status="No Show").count()

        return render(request, "accounts/doctor_dashboard.html", {
            "todays_appointments": todays_appointments,
            "high_risk_today": high_risk_today,
            "total_noshows": total_noshows,
        })

    # Admin / staff -> generic dashboard
    return render(request, "accounts/dashboard.html")