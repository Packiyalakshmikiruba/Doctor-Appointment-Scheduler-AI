from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.utils import timezone
from medical_records.models import MedicalRecord
from .forms import RegisterForm, LoginForm
from appointments.models import Appointment
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from chatbot.views import _SESSION_HISTORY
from .forms import RegisterForm, LoginForm
from django.db.models import Count
from hospital.models import DoctorAvailability
# Models
from appointments.models import Appointment

from medical_records.models import MedicalRecord
from billing.models import Bill, Payment


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
            session_key = request.session.session_key

            if session_key in _SESSION_HISTORY:
                del _SESSION_HISTORY[session_key]
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

    session_key = request.session.session_key

    # Clear chat history
    if session_key in _SESSION_HISTORY:
        del _SESSION_HISTORY[session_key]

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
"""
REPLACE patient_dashboard_view in accounts/views.py with this.

Ensure these imports exist at the top of accounts/views.py:
    from medical_records.models import MedicalRecord
    from billing.models import Bill, Payment
"""

"""
REPLACE patient_dashboard_view in accounts/views.py with this.

Ensure these imports exist at the top of accounts/views.py:
    from medical_records.models import MedicalRecord
    from billing.models import Bill, Payment
"""

"""
REPLACE patient_dashboard_view in accounts/views.py with this.

Ensure these imports exist at the top of accounts/views.py:
    from medical_records.models import MedicalRecord
    from billing.models import Bill, Payment
"""

@login_required
def patient_dashboard_view(request):

    if request.user.role != "PATIENT":
        messages.error(request, "Access denied.")
        return redirect("dashboard")

    if not hasattr(request.user, "patient_profile"):
        messages.info(request, "Please complete your profile to continue.")
        return redirect("complete_profile")

    patient = request.user.patient_profile
    today = timezone.now().date()

    all_appointments = Appointment.objects.filter(patient=patient).select_related(
        "doctor__user", "doctor__department"
    )

    # ---- Latest Appointment card: shows immediately after booking ----
    # Most recently CREATED appointment (not necessarily the soonest date),
    # so it always reflects "what did I just book" right after booking.
    latest_appointment = all_appointments.order_by("-created_at").first()

    upcoming = all_appointments.filter(
        appointment_date__gte=today,
        status__in=["Pending", "Confirmed"],
    ).order_by("appointment_date", "appointment_time")

    history = all_appointments.filter(
        status__in=["Completed", "Cancelled", "No Show"]
    ).order_by("-appointment_date")[:15]

    high_risk_count = upcoming.filter(risk_level="HIGH").count()

    recent_records = (
        MedicalRecord.objects.filter(appointment__patient=patient)
        .select_related("appointment__doctor__user", "appointment__doctor__department")
        .prefetch_related("prescriptions")
        .order_by("-created_at")
    )

    all_bills = Bill.objects.filter(appointment__patient=patient).select_related(
        "appointment__doctor__user"
    ).order_by("-created_at")

    pending_bills = all_bills.exclude(payment_status="Paid")
    total_due = sum((b.balance_due for b in pending_bills), 0)

    payments = Payment.objects.filter(
        bill__appointment__patient=patient
    ).select_related("bill").order_by("-paid_at")[:10]

    return render(request, "accounts/patient_dashboard.html", {
        "patient": patient,
        "latest_appointment": latest_appointment,
        "upcoming": upcoming,
        "history": history,
        "high_risk_count": high_risk_count,
        "recent_records": recent_records,
        "all_bills": all_bills,
        "pending_bills": pending_bills,
        "total_due": total_due,
        "payments": payments,
    })
# ---------------- Doctor Dashboard ----------------

@login_required
def doctor_dashboard(request):

    # Role check
    if request.user.role != "DOCTOR":
        messages.error(
            request,
            "Access denied."
        )
        return redirect("dashboard")


    # Doctor profile check
    if not hasattr(request.user, "doctor_profile"):

        messages.info(
            request,
            "Doctor profile not set up yet. Contact admin."
        )

        return render(
            request,
            "accounts/dashboard.html"
        )


    doctor = request.user.doctor_profile


    today = timezone.now().date()


    week_end = today + timezone.timedelta(days=7)



    # ===============================
    # TODAY APPOINTMENTS
    # ===============================


    todays_appointments = (
        Appointment.objects
        .filter(
            doctor=doctor,
            appointment_date=today,
            status__in=[
                "Pending",
                "Confirmed"
            ]
        )
        .select_related(
            "patient__user"
        )
        .order_by(
            "appointment_time"
        )
    )



    # ===============================
    # AI HIGH RISK PATIENTS
    # ===============================


    high_risk_today = (
        todays_appointments
        .filter(
            risk_level="HIGH"
        )
    )



    # ===============================
    # UPCOMING APPOINTMENTS
    # ===============================


    week_appointments = (
        Appointment.objects
        .filter(
            doctor=doctor,
            appointment_date__gt=today,
            appointment_date__lte=week_end,
            status__in=[
                "Pending",
                "Confirmed"
            ]
        )
        .select_related(
            "patient__user"
        )
        .order_by(
            "appointment_date",
            "appointment_time"
        )[:5]
    )



    # ===============================
    # PATIENT STATISTICS
    # ===============================


    total_patients = (
        Appointment.objects
        .filter(
            doctor=doctor
        )
        .values(
            "patient"
        )
        .distinct()
        .count()
    )



    total_completed = (
        Appointment.objects
        .filter(
            doctor=doctor,
            status="Completed"
        )
        .count()
    )



    total_noshows = (
        Appointment.objects
        .filter(
            doctor=doctor,
            status="No Show"
        )
        .count()
    )



    total_seen = (
        total_completed +
        total_noshows
    )



    noshow_rate = (

        round(
            (total_noshows / total_seen) * 100,
            1
        )

        if total_seen > 0

        else 0

    )



    # ===============================
    # WAITING PATIENTS
    # ===============================


    waiting_patients = (
        todays_appointments
        .filter(
            status="Pending"
        )
        .count()
    )



    # ===============================
    # NEXT PATIENT
    # ===============================


    next_patient = (
        todays_appointments
        .filter(
            appointment_time__gte=
            timezone.now().time()
        )
        .first()
    )



    # ===============================
    # MEDICAL RECORDS
    # ===============================


    recent_records = (
        MedicalRecord.objects
        .filter(
            appointment__doctor=doctor
        )
        .select_related(
            "appointment__patient__user"
        )
        .order_by(
            "-created_at"
        )[:5]
    )



    # ===============================
    # AVAILABILITY
    # ===============================


    availability = (
        DoctorAvailability.objects
        .filter(
            doctor=doctor,
            is_available=True
        )
        .order_by(
            "day_of_week"
        )
    )



    # ===============================
    # MONTHLY PERFORMANCE
    # ===============================


    monthly_completed = (
        Appointment.objects
        .filter(
            doctor=doctor,
            status="Completed",
            appointment_date__month=today.month,
            appointment_date__year=today.year
        )
        .count()
    )



    # ===============================
    # CHART DATA
    # ===============================


    appointment_chart = (
        Appointment.objects
        .filter(
            doctor=doctor
        )
        .values(
            "status"
        )
        .annotate(
            count=Count("id")
        )
    )



    context = {


        "doctor":
            doctor,


        "todays_appointments":
            todays_appointments,


        "high_risk_today":
            high_risk_today,


        "week_appointments":
            week_appointments,


        "total_patients":
            total_patients,


        "total_completed":
            total_completed,


        "total_noshows":
            total_noshows,


        "noshow_rate":
            noshow_rate,


        "recent_records":
            recent_records,


        "availability":
            availability,


        "waiting_patients":
            waiting_patients,


        "next_patient":
            next_patient,


        "monthly_completed":
            monthly_completed,


        "appointment_chart":
            appointment_chart,


        "today":
            today,

    }



    return render(
        request,
        "accounts/doctor_dashboard.html",
        context
    )
# ---------------- Admin Dashboard ----------------

@login_required
def admin_dashboard_view(request):

    if request.user.role != "ADMIN":
        messages.error(request, "Access denied.")
        return redirect("dashboard")

    from hospital.models import Doctor, Department
    from patients.models import Patient

    total_appointments = Appointment.objects.count()
    pending_count = Appointment.objects.filter(status="Pending").count()
    confirmed_count = Appointment.objects.filter(status="Confirmed").count()
    completed_count = Appointment.objects.filter(status="Completed").count()
    high_risk_count = Appointment.objects.filter(risk_level="HIGH", status__in=["Pending", "Confirmed"]).count()
    noshow_count = Appointment.objects.filter(status="No Show").count()

    total_doctors = Doctor.objects.filter(is_active=True).count()
    total_patients = Patient.objects.count()
    total_departments = Department.objects.count()

    total_revenue = sum(b.total_paid for b in Bill.objects.all())
    pending_revenue = sum(b.balance_due for b in Bill.objects.filter(payment_status="Pending"))

    todays_appointments = Appointment.objects.filter(
        appointment_date=timezone.now().date()
    ).select_related("patient__user", "doctor__user").order_by("appointment_time")[:10]

    return render(request, "accounts/admin_dashboard.html", {
        "total_appointments": total_appointments,
        "pending_count": pending_count,
        "confirmed_count": confirmed_count,
        "completed_count": completed_count,
        "high_risk_count": high_risk_count,
        "noshow_count": noshow_count,
        "total_doctors": total_doctors,
        "total_patients": total_patients,
        "total_departments": total_departments,
        "total_revenue": total_revenue,
        "pending_revenue": pending_revenue,
        "todays_appointments": todays_appointments,
    })