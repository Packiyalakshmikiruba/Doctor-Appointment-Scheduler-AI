from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from .forms import RegisterForm, LoginForm
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login, logout
from django.utils import timezone
from chatbot.views import _SESSION_HISTORY
from django.shortcuts import render, redirect
from prescriptions.models import Prescription
from messaging.models import Message
from notifications.models import Notification
from hospital.models import (
    Doctor,
    DoctorAvailability,
    DoctorAttendance,
    DoctorStatus,
    DoctorLeave,
)
import json
from datetime import timedelta
from django.db.models import Count, Sum
from appointments.models import Appointment
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from medical_records.models import MedicalRecord
from billing.models import Bill
from payment.models import Payment


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



@login_required
def patient_dashboard_view(request):

    if request.user.role != "PATIENT":
        messages.error(request, "Access denied.")
        return redirect("dashboard")

    if not hasattr(request.user, "patient_profile"):
        messages.info(request, "Please complete your profile.")
        return redirect("complete_profile")

    patient = request.user.patient_profile
    today = timezone.now().date()

    # ----------------------------------------
    # Appointments
    # ----------------------------------------

    all_appointments = Appointment.objects.filter(
        patient=patient
    ).select_related(
        "doctor__user",
        "doctor__department"
    ).order_by("-appointment_date", "-appointment_time")

    upcoming = all_appointments.filter(
        appointment_date__gte=today,
        status__in=["Pending", "Confirmed"]
    ).order_by(
        "appointment_date",
        "appointment_time"
    )

    latest_appointment = all_appointments.first()
    next_appointment = upcoming.first()

    history = all_appointments.filter(
        status__in=["Completed", "Cancelled", "No Show"]
    )[:15]

    high_risk_count = upcoming.filter(
        risk_level="HIGH"
    ).count()

    # ----------------------------------------
    # Medical Records
    # ----------------------------------------

    recent_records = MedicalRecord.objects.filter(
        appointment__patient=patient
    ).select_related(
        "appointment__doctor__user"
    ).prefetch_related(
        "prescriptions"
    ).order_by("-created_at")

    latest_record = recent_records.first()

    # ----------------------------------------
    # Prescriptions
    # ----------------------------------------

    prescriptions = Prescription.objects.filter(
        medical_record__appointment__patient=patient
    ).select_related(
        "medical_record"
    ).order_by("-created_at")

    # ----------------------------------------
    # Bills
    # ----------------------------------------

    all_bills = Bill.objects.filter(
        appointment__patient=patient
    ).select_related(
        "appointment__doctor__user"
    ).order_by("-created_at")

    pending_bills = all_bills.exclude(
        payment_status="Paid"
    )

    total_due = sum(
        bill.balance_due
        for bill in pending_bills
    )

    # ----------------------------------------
    # Payments
    # ----------------------------------------
    payments = (
        Payment.objects
        .filter(
            bill__appointment__patient=patient
        )
        .order_by("-payment_date")
    )

    total_paid = payments.aggregate(
        total=Sum("amount")
    )["total"] or 0
     

    # ----------------------------------------
    # Messages
    # ----------------------------------------

    unread_messages = Message.objects.filter(
        receiver=request.user,
        is_read=False
    ).count()

    # ----------------------------------------
    # Dashboard Statistics
    # ----------------------------------------

    stats = {
        "appointments": all_appointments.count(),
        "upcoming": upcoming.count(),
        "completed": all_appointments.filter(status="Completed").count(),
        "cancelled": all_appointments.filter(status="Cancelled").count(),
        "medical_records": recent_records.count(),
        "prescriptions": prescriptions.count(),
        "pending_bills": pending_bills.count(),
        "total_paid": total_paid,
        "total_due": total_due,
    }

    # ----------------------------------------
    # Notifications
    # ----------------------------------------

    notifications = []

    if next_appointment:
        notifications.append({
            "title": "Upcoming Appointment",
            "message": f"You have an appointment with Dr. {next_appointment.doctor.user.get_full_name()}",
            "date": next_appointment.appointment_date,
            "time": next_appointment.appointment_time,
        })

    if pending_bills.exists():
        notifications.append({
            "title": "Pending Bill",
            "message": f"₹ {total_due} payment pending.",
        })

    # ----------------------------------------
    # Recent Activities
    # ----------------------------------------

    activities = []

    for appointment in all_appointments[:5]:
        activities.append({
            "type": "Appointment",
            "title": f"Appointment with Dr. {appointment.doctor.user.get_full_name()}",
            "date": appointment.appointment_date,
            "status": appointment.status,
        })

    for record in recent_records[:3]:
        activities.append({
            "type": "Medical Record",
            "title": record.diagnosis,
            "date": record.created_at.date(),
            "status": "Completed",
        })

    for payment in payments[:3]:

        activities.append({

        "type": "Payment",

        "title": f"₹ {payment.amount}",

        "date": payment.payment_date.date(),

        "status": payment.payment_method,

    })

    activities = sorted(
        activities,
        key=lambda x: x["date"],
        reverse=True
    )

    # ----------------------------------------
    # Doctors
    # ----------------------------------------

    all_doctors = Doctor.objects.select_related(
        "user",
        "department"
    ).all()

    # ----------------------------------------
    # Render
    # ----------------------------------------

    return render(
        request,
        "accounts/patient_dashboard.html",
        {
            "patient": patient,

            "stats": stats,

            "latest_appointment": latest_appointment,
            "next_appointment": next_appointment,
            "upcoming": upcoming,
            "history": history,

            "high_risk_count": high_risk_count,

            "recent_records": recent_records,
            "latest_record": latest_record,

            "prescriptions": prescriptions,

            "all_bills": all_bills,
            "bills": all_bills,
            "pending_bills": pending_bills,
             
            "payments": payments,

            "total_due": total_due,
            "total_paid": total_paid,

            "notifications": notifications,
            "activities": activities,

            "all_doctors": all_doctors,

            "unread_messages": unread_messages,
        },
    )
# ---------------- Doctor Dashboard ----------------
def doctor_dashboard_view(request):

    # ==========================================
    # Role Check
    # ==========================================

    if request.user.role != "DOCTOR":
        messages.error(
            request,
            "Access denied."
        )
        return redirect("dashboard")

    # ==========================================
    # Doctor Profile Check
    # ==========================================

    if not hasattr(request.user, "doctor_profile"):

        messages.info(
            request,
            "Doctor profile not configured."
        )

        return render(
            request,
            "accounts/dashboard.html"
        )

    doctor = request.user.doctor_profile

    today = timezone.now().date()

    week_end = today + timezone.timedelta(days=7)

    # ==========================================
    # Attendance
    # ==========================================

    today_attendance = (
        DoctorAttendance.objects.filter(
            doctor=doctor,
            attendance_date=today
        ).first()
    )

    doctor_status = (
        DoctorStatus.objects.filter(
            doctor=doctor
        ).first()
    )

    is_checked_in = (
        today_attendance
        and
        today_attendance.check_in_time
        and
        not today_attendance.check_out_time
    )

    is_checked_out = (
        today_attendance
        and
        today_attendance.check_out_time
    )

    # ==========================================
    # Leave
    # ==========================================

    today_leave = (
        DoctorLeave.objects.filter(
            doctor=doctor,
            leave_date=today
        ).first()
    )

    # ==========================================
    # Today's Appointments
    # ==========================================

    todays_appointments = (

        Appointment.objects

        .filter(
            doctor=doctor,
            appointment_date=today,
        )

        .select_related(
            "patient__user",
            "doctor__user"
        )

        .order_by(
            "appointment_time"
        )

    )

    # ==========================================
    # Waiting Patients
    # ==========================================

    waiting_patients = (

        todays_appointments.filter(
            status="Pending"
        ).count()

    )

    # ==========================================
    # Next Patient
    # ==========================================

    next_patient = (

        todays_appointments.filter(

            appointment_time__gte=
            timezone.now().time()

        ).first()

    )

    # ==========================================
    # Total Patients
    # ==========================================

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

    # ==========================================
    # Completed
    # ==========================================

    total_completed = (

        Appointment.objects.filter(
            doctor=doctor,
            status="Completed"
        ).count()

    )

    # ==========================================
    # No Show
    # ==========================================

    total_noshows = (

        Appointment.objects.filter(
            doctor=doctor,
            status="No Show"
        ).count()

    )

    total_visits = (

        total_completed +
        total_noshows

    )

    if total_visits > 0:

        noshow_rate = round(

            (total_noshows / total_visits) * 100,

            1

        )

    else:

        noshow_rate = 0
        # ==========================================
    # AI High Risk Patients Today
    # ==========================================

    high_risk_today = (

        todays_appointments.filter(
            risk_level="HIGH"
        )

    )

    # ==========================================
    # Upcoming Week Appointments
    # ==========================================

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

    # ==========================================
    # Recent Medical Records
    # ==========================================

    recent_records = (

        MedicalRecord.objects

        .filter(
            appointment__doctor=doctor
        )

        .select_related(
            "appointment__patient__user"
        )

        .prefetch_related(
            "prescriptions"
        )

        .order_by(
            "-created_at"
        )[:5]

    )

    # ==========================================
    # Doctor Availability
    # ==========================================

    availability = (

        DoctorAvailability.objects

        .filter(
            doctor=doctor,
            is_available=True
        )

        .order_by(
            "day_of_week",
            "start_time"
        )

    )

    # ==========================================
    # Monthly Performance
    # ==========================================

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

    monthly_pending = (

        Appointment.objects

        .filter(
            doctor=doctor,
            status="Pending",
            appointment_date__month=today.month,
            appointment_date__year=today.year
        )

        .count()

    )

    monthly_confirmed = (

        Appointment.objects

        .filter(
            doctor=doctor,
            status="Confirmed",
            appointment_date__month=today.month,
            appointment_date__year=today.year
        )

        .count()

    )

    monthly_noshow = (

        Appointment.objects

        .filter(
            doctor=doctor,
            status="No Show",
            appointment_date__month=today.month,
            appointment_date__year=today.year
        )

        .count()

    )

    # ==========================================
    # AI Risk Patients
    # ==========================================

    ai_risk_patients = (

        Appointment.objects

        .filter(
            doctor=doctor,
            risk_level__in=[
                "HIGH",
                "MEDIUM"
            ]
        )

        .select_related(
            "patient__user"
        )

        .order_by(
            "-risk_score"
        )[:10]

    )

    # ==========================================
    # Appointment Chart
    # ==========================================

    appointment_chart = {

        "completed": total_completed,

        "pending": Appointment.objects.filter(
            doctor=doctor,
            status="Pending"
        ).count(),

        "confirmed": Appointment.objects.filter(
            doctor=doctor,
            status="Confirmed"
        ).count(),

        "noshow": total_noshows,

    }
        # ==========================================
    # Doctor Status
    # ==========================================

    doctor_status = (

        DoctorStatus.objects

        .filter(
            doctor=doctor
        )

        .first()

    )

    # ==========================================
    # Today Attendance
    # ==========================================

    today_attendance = (

        DoctorAttendance.objects

        .filter(
            doctor=doctor,
            attendance_date=today
        )

        .first()

    )

    # ==========================================
    # Today's Leave
    # ==========================================

    today_leave = (

        DoctorLeave.objects

        .filter(
            doctor=doctor,
            leave_date=today
        )

        .first()

    )

    # ==========================================
    # Notification Count
    # ==========================================

    unread_notifications = (

        Notification.objects

        .filter(
            user=request.user,
            is_read=False
        )

        .count()

    )

    # ==========================================
    # Today's Revenue
    # ==========================================

    today_revenue = (

        Appointment.objects

        .filter(
            doctor=doctor,
            appointment_date=today,
            status="Completed"
        )

        .select_related("doctor")

    )

    revenue = 0

    for appointment in today_revenue:

        revenue += appointment.doctor.consultation_fee

    # ==========================================
    # Context
    # ==========================================

    context = {

        "doctor": doctor,

        "today": today,

        "todays_appointments": todays_appointments,

        "week_appointments": week_appointments,

        "high_risk_today": high_risk_today,

        "ai_risk_patients": ai_risk_patients,

        "recent_records": recent_records,

        "availability": availability,

        "total_patients": total_patients,

        "total_completed": total_completed,

        "total_noshows": total_noshows,

        "noshow_rate": noshow_rate,

        "waiting_patients": waiting_patients,

        "next_patient": next_patient,

        "monthly_completed": monthly_completed,

        "monthly_pending": monthly_pending,

        "monthly_confirmed": monthly_confirmed,

        "monthly_noshow": monthly_noshow,

        "appointment_chart": json.dumps(appointment_chart),

        "doctor_status": doctor_status,

        "today_attendance": today_attendance,

        "today_leave": today_leave,

        "unread_notifications": unread_notifications,

        "today_revenue": revenue,
        

    }

    return render(

        request,

        "hospital/doctor_dashboard.html",

        context,

    )
# ---------------- Admin Dashboard ----------------

@login_required
def admin_dashboard_view(request):

    if request.user.role != "ADMIN":
        messages.error(request, "Access denied.")
        return redirect("dashboard")

    from hospital.models import Doctor, Department
    from patients.models import Patient

    today = timezone.now().date()

    # ---------------- Core Stats ----------------
    total_appointments = Appointment.objects.count()
    pending_count = Appointment.objects.filter(status="Pending").count()
    confirmed_count = Appointment.objects.filter(status="Confirmed").count()
    completed_count = Appointment.objects.filter(status="Completed").count()
    cancelled_count = Appointment.objects.filter(status="Cancelled").count()
    high_risk_count = Appointment.objects.filter(risk_level="HIGH", status__in=["Pending", "Confirmed"]).count()
    noshow_count = Appointment.objects.filter(status="No Show").count()

    total_doctors = Doctor.objects.filter(is_active=True).count()
    total_patients = Patient.objects.count()
    total_departments = Department.objects.count()

    total_revenue = Payment.objects.filter(

    payment_status="Success"

    ).aggregate(

        total=Sum("amount")

    )["total"] or 0
    pending_revenue = sum(

    b.balance_due

    for b in Bill.objects.filter(

        payment_status="Pending"

    )

)

    todays_appointments = Appointment.objects.filter(
        appointment_date=today
    ).select_related("patient__user", "doctor__user").order_by("appointment_time")[:10]

    # ---------------- Chart 1: Appointment Status Breakdown (Donut) ----------------
    status_labels = ["Pending", "Confirmed", "Completed", "Cancelled", "No Show"]
    status_data = [
        pending_count, confirmed_count, completed_count,
        cancelled_count, noshow_count,
    ]

    # ---------------- Chart 2: Risk Level Distribution (Pie) ----------------
    risk_qs = Appointment.objects.exclude(risk_level="").values("risk_level").annotate(count=Count("id"))
    risk_map = {r["risk_level"]: r["count"] for r in risk_qs}
    risk_labels = ["LOW", "MEDIUM", "HIGH"]
    risk_data = [risk_map.get(lvl, 0) for lvl in risk_labels]

    # ---------------- Chart 3: Appointments by Department (Bar) ----------------
    dept_qs = (
        Appointment.objects
        .values("doctor__department__department_name")
        .annotate(count=Count("id"))
        .order_by("-count")[:8]
    )
    dept_labels = [d["doctor__department__department_name"] or "Unknown" for d in dept_qs]
    dept_data = [d["count"] for d in dept_qs]

    # ---------------- Chart 4: 7-Day Appointment Trend (Line) ----------------
    trend_labels = []
    trend_data = []
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        count = Appointment.objects.filter(appointment_date=day).count()
        trend_labels.append(day.strftime("%d %b"))
        trend_data.append(count)

    # ---------------- Chart 5: Top 5 Doctors by Appointment Volume (Bar) ----------------
    doctor_qs = (
        Appointment.objects
        .values("doctor__user__first_name", "doctor__user__last_name")
        .annotate(count=Count("id"))
        .order_by("-count")[:5]
    )
    doctor_labels = [f"Dr. {d['doctor__user__first_name']} {d['doctor__user__last_name']}".strip() for d in doctor_qs]
    doctor_data = [d["count"] for d in doctor_qs]

    # ---------------- Chart 6: Revenue Trend (Last 7 Days, Line) ----------------
    # NOTE: "total_paid" is a Python @property on the Bill model (computed
    # by summing related Payment rows in Python), not an actual database
    # column -- Sum() can only aggregate real fields, so Sum("total_paid")
    # raises FieldError. Aggregate through the real "payments" relation
    # instead (Payment.amount IS a real column), filtered to payments
    # actually made ON that day.
    revenue_labels = []
    revenue_data = []

    for i in range(6, -1, -1):

        day = today - timedelta(days=i)

        day_revenue = Payment.objects.filter(

            payment_date__date=day,

            payment_status="Success"

        ).aggregate(

            total=Sum("amount")

        )["total"] or 0

        revenue_labels.append(
            day.strftime("%d %b")
        )

        revenue_data.append(
            float(day_revenue)
        )

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
         
        # Chart data -- serialized as JSON for Chart.js
        "status_labels": json.dumps(status_labels),
        "status_data": json.dumps(status_data),
        "risk_labels": json.dumps(risk_labels),
        "risk_data": json.dumps(risk_data),
        "dept_labels": json.dumps(dept_labels),
        "dept_data": json.dumps(dept_data),
        "trend_labels": json.dumps(trend_labels),
        "trend_data": json.dumps(trend_data),
        "doctor_labels": json.dumps(doctor_labels),
        "doctor_data": json.dumps(doctor_data),
        "revenue_labels": json.dumps(revenue_labels),
        "revenue_data": json.dumps(revenue_data),
    })
@login_required
def change_password(request):

    if request.method == "POST":

        form = PasswordChangeForm(request.user, request.POST)

        if form.is_valid():

            user = form.save()

            update_session_auth_hash(request, user)

            messages.success(request, "Password changed successfully.")

            return redirect("dashboard")

    else:

        form = PasswordChangeForm(request.user)

    return render(
        request,
        "accounts/change_password.html",
        {
            "form": form
        }
    )