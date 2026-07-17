from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.utils import timezone

from .forms import RegisterForm, LoginForm
from appointments.models import Appointment
from support.models import SupportMessage



def register_view(request):

    if request.method == "POST":
        form = RegisterForm(request.POST)

        if form.is_valid():
            user = form.save(commit=False)
            user.role = form.cleaned_data["role"]
            user.save()
            login(request, user)
            messages.success(request, "Registration Successful.")

            if user.role == "ADMIN":
                return redirect("admin_dashboard")
            elif user.role == "DOCTOR":
                return redirect("doctor_dashboard")
            else:
                return redirect("patient_dashboard")

    else:
        form = RegisterForm()

    return render(request, "accounts/register.html", {"form": form})


def login_view(request):

    if request.method == "POST":
        form = LoginForm(request, data=request.POST)

        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, "Login Successful.")

            if user.role == "ADMIN":
                return redirect("admin_dashboard")
            elif user.role == "DOCTOR":
                return redirect("doctor_dashboard")
            elif user.role == "PATIENT":
                return redirect("patient_dashboard")
            else:
                return redirect("login")

        else:
            messages.error(request, "Invalid username or password.")

    else:
        form = LoginForm()

    return render(request, "accounts/login.html", {"form": form})


@login_required
def logout_view(request):
    logout(request)
    messages.success(request, "Logged Out Successfully.")
    return redirect("login")


# ---------------- Generic entry point (used by navbar links, redirects role-wise) ----------------

@login_required
def dashboard_redirect(request):
    if request.user.role == "ADMIN":
        return redirect("admin_dashboard")
    elif request.user.role == "DOCTOR":
        return redirect("doctor_dashboard")
    elif request.user.role == "PATIENT":
        return redirect("patient_dashboard")
    return redirect("login")


# ---------------- Patient Dashboard ----------------
@login_required
def patient_dashboard_view(request):

    if request.user.role != "PATIENT":
        messages.error(request, "Access denied.")
        return redirect("dashboard")

    if not hasattr(request.user, "patient_profile"):
        messages.info(request, "Please complete your profile to continue.")
        return redirect("complete_profile")

    patient = request.user.patient_profile

    upcoming = Appointment.objects.filter(
        patient=patient,
        status__in=["Pending", "Confirmed"],
        appointment_date__gte=timezone.now().date()
    ).select_related("doctor__user", "doctor__department").order_by("appointment_date", "appointment_time")

    history = Appointment.objects.filter(
        patient=patient,
        status__in=["Completed", "Cancelled", "No Show"]
    ).select_related("doctor__user").order_by("-appointment_date")[:10]

    high_risk_count = upcoming.filter(risk_level="HIGH").count()

    from billing.models import Bill, Payment
    pending_bills = Bill.objects.filter(
        appointment__patient=patient,
        payment_status="Pending"
    ).select_related("appointment__doctor__user")

    total_due = sum(b.balance_due for b in pending_bills)

    payments = Payment.objects.filter(
        bill__appointment__patient=patient
    ).select_related("bill").order_by("-paid_at")[:5]

    from medical_records.models import MedicalRecord
    recent_records = MedicalRecord.objects.filter(
        appointment__patient=patient
    ).select_related(
        "appointment__doctor__user"
    ).prefetch_related(
        "prescriptions"
    ).order_by("-created_at")[:5]

    return render(request, "accounts/patient_dashboard.html", {
        "patient": patient,
        "upcoming": upcoming,
        "history": history,
        "high_risk_count": high_risk_count,
        "pending_bills": pending_bills,
        "total_due": total_due,
        "payments": payments,
        "recent_records": recent_records,
    })
# ---------------- Doctor Dashboard ----------------

@login_required
def doctor_dashboard_view(request):

    if request.user.role != "DOCTOR":
        messages.error(request, "Access denied.")
        return redirect("dashboard")

    if not hasattr(request.user, "doctor_profile"):
        messages.info(request, "Doctor profile not set up yet. Contact admin.")
        return render(request, "accounts/dashboard.html")

    doctor = request.user.doctor_profile
    today = timezone.now().date()
    week_end = today + timezone.timedelta(days=7)

    # Today's schedule
    todays_appointments = Appointment.objects.filter(
        doctor=doctor, appointment_date=today, status__in=["Pending", "Confirmed"]
    ).select_related("patient__user").order_by("appointment_time")

    high_risk_today = todays_appointments.filter(risk_level="HIGH")

    # This week's upcoming (excluding today)
    week_appointments = Appointment.objects.filter(
        doctor=doctor,
        appointment_date__gt=today,
        appointment_date__lte=week_end,
        status__in=["Pending", "Confirmed"]
    ).select_related("patient__user").order_by("appointment_date", "appointment_time")[:5]

    # Stats
    total_patients = Appointment.objects.filter(doctor=doctor).values("patient").distinct().count()
    total_completed = Appointment.objects.filter(doctor=doctor, status="Completed").count()
    total_noshows = Appointment.objects.filter(doctor=doctor, status="No Show").count()
    total_seen = total_completed + total_noshows
    noshow_rate = round((total_noshows / total_seen * 100), 1) if total_seen > 0 else 0

    # Recent medical records (created by this doctor)
    from medical_records.models import MedicalRecord
    recent_records = MedicalRecord.objects.filter(
        appointment__doctor=doctor
    ).select_related("appointment__patient__user").order_by("-created_at")[:5]

    # This doctor's availability (for quick view)
    from hospital.models import DoctorAvailability
    availability = DoctorAvailability.objects.filter(doctor=doctor, is_available=True).order_by("day_of_week")

    return render(request, "accounts/doctor_dashboard.html", {
        "doctor": doctor,
        "todays_appointments": todays_appointments,
        "high_risk_today": high_risk_today,
        "week_appointments": week_appointments,
        "total_patients": total_patients,
        "total_completed": total_completed,
        "total_noshows": total_noshows,
        "noshow_rate": noshow_rate,
        "recent_records": recent_records,
        "availability": availability,
    })
# ---------------- Admin Dashboard ----------------

@login_required
def admin_dashboard_view(request):
    if request.user.role != "ADMIN":
        messages.error(request, "Access denied.")
        return redirect("dashboard")

    total_appointments = Appointment.objects.count()
    pending_count = Appointment.objects.filter(status="Pending").count()
    high_risk_count = Appointment.objects.filter(risk_level="HIGH").count()
    noshow_count = Appointment.objects.filter(status="No Show").count()
    
    # இதோ நீங்கள் மறந்த அந்த மெசேஜ் பகுதி:
    # இங்கிருந்துதான் மெசேஜ்கள் டேஷ்போர்டுக்கு செல்லும்
    admin_messages = SupportMessage.objects.filter(is_read=False).order_by('-created_at')

    return render(request, "accounts/admin_dashboard.html", {
        "total_appointments": total_appointments,
        "pending_count": pending_count,
        "high_risk_count": high_risk_count,
        "noshow_count": noshow_count,
        "admin_messages": admin_messages, # இதைச் சேர்த்துள்ளேன்
    })