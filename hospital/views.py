from django.shortcuts import render, redirect, get_object_or_404
from .forms import DepartmentForm
from .models import Department
from .forms import DoctorForm
from .forms import DoctorAvailabilityForm, DoctorStatusForm, DoctorLeaveForm
from .models import DoctorAvailability
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from datetime import datetime
from .models import Doctor
from django.db.models import Prefetch
from django.utils import timezone
from .models import Doctor, DoctorLeave
from .models import (
    Doctor,
    DoctorAttendance,
    DoctorStatus,
)
def department_create(request):

    if request.method == "POST":
        form = DepartmentForm(request.POST)

        if form.is_valid():
            form.save()
            return redirect("department_list")

    else:
        form = DepartmentForm()

    return render(
        request,
        "hospital/department_form.html",
        {"form": form}
    )
def department_list(request):

    departments = Department.objects.all()

    context = {
        "departments": departments
    }

    return render(
        request,
        "hospital/department_list.html",
        context
    )
def department_update(request, pk):

    department = get_object_or_404(Department, pk=pk)

    if request.method == "POST":
        form = DepartmentForm(request.POST, instance=department)

        if form.is_valid():
            form.save()
            return redirect("department_list")

    else:
        form = DepartmentForm(instance=department)

    return render(
        request,
        "hospital/department_form.html",
        {"form": form}
    )
def department_delete(request, pk):

    department = get_object_or_404(Department, pk=pk)

    if request.method == "POST":
        department.delete()
        return redirect("department_list")

    return render(
        request,
        "hospital/department_confirm_delete.html",
        {"department": department}
    )
def doctor_create(request):

    if request.method == "POST":

        form = DoctorForm(request.POST)

        if form.is_valid():
            form.save()
            return redirect("doctor_list")

    else:

        form = DoctorForm()

    return render(
        request,
        "hospital/doctor_form.html",
        {"form": form}
    )
def doctor_list(request):

    doctors = (
        Doctor.objects
        .select_related(
            "user",
            "department"
        )
        .prefetch_related(
            "availabilities"
        )
    )

    return render(
        request,
        "hospital/doctor_list.html",
        {
            "doctors": doctors
        }
    )
def doctor_update(request, pk):

    doctor = get_object_or_404(Doctor, pk=pk)

    if request.method == "POST":

        form = DoctorForm(request.POST, instance=doctor)

        if form.is_valid():
            form.save()
            return redirect("doctor_list")

    else:

        form = DoctorForm(instance=doctor)

    return render(
        request,
        "hospital/doctor_form.html",
        {"form": form}
    )
def doctor_delete(request, pk):

    doctor = get_object_or_404(Doctor, pk=pk)

    if request.method == "POST":
        doctor.delete()
        return redirect("doctor_list")

    return render(
        request,
        "hospital/doctor_confirm_delete.html",
        {"doctor": doctor}
    )
def availability_create(request):

    if request.method == "POST":

        form = DoctorAvailabilityForm(request.POST)

        if form.is_valid():
            form.save()
            return redirect("availability_list")

    else:
        form = DoctorAvailabilityForm()

    return render(
        request,
        "hospital/availability_form.html",
        {"form": form}
    )


def availability_list(request):

    DAY_ORDER = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

    availabilities = DoctorAvailability.objects.select_related(
        "doctor",
        "doctor__user"
    ).all()

    # Build one row per doctor, with a slot (or None) for each day column
    grid = {}
    for a in availabilities:
        if a.doctor_id not in grid:
            grid[a.doctor_id] = {"doctor": a.doctor, "days": {d: None for d in DAY_ORDER}}
        grid[a.doctor_id]["days"][a.day_of_week] = a

    doctor_rows = list(grid.values())

    return render(
        request,
        "hospital/availability_list.html",
        {
            "doctor_rows": doctor_rows,
            "day_order": DAY_ORDER,
        }
    )

from hospital.models import (
    Doctor,
    DoctorAttendance,
    DoctorLeave,
    DoctorAvailability,
)

from appointments.models import Appointment


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

    doctor = Doctor.objects.select_related(
        "department",
        "user",
        "current_status"
    ).get(user=request.user)

    today = timezone.now().date()

    todays_appointments = Appointment.objects.filter(
        doctor=doctor,
        appointment_date=today
    ).select_related(
        "patient",
        "doctor"
    ).order_by("appointment_time")

    total_patients = Appointment.objects.filter(
        doctor=doctor
    ).values("patient").distinct().count()

    total_completed = Appointment.objects.filter(
        doctor=doctor,
        status="Completed"
    ).count()

    total_noshow = Appointment.objects.filter(
        doctor=doctor,
        status="No Show"
    ).count()

    total_visits = Appointment.objects.filter(
        doctor=doctor
    ).count()

    if total_visits:
        noshow_rate = round(
            (total_noshow / total_visits) * 100,
            1
        )
    else:
        noshow_rate = 0

    high_risk_today = Appointment.objects.filter(
        doctor=doctor,
        appointment_date=today,
        risk_level="HIGH"
    )

    today_leave = DoctorLeave.objects.filter(
        doctor=doctor,
        leave_date=today
    ).first()

    today_attendance = DoctorAttendance.objects.filter(
        doctor=doctor,
        attendance_date=today
    ).first()
    doctor_status = (
    DoctorStatus.objects
    .filter(doctor=doctor)
    .order_by("-updated_at")
    .first()
)

    availability = DoctorAvailability.objects.filter(
        doctor=doctor,
        is_available=True
    ).order_by("day_of_week", "start_time")

    # ---------------- Upcoming patients (next 7 days, excluding today) ----------------
    from datetime import timedelta
    week_end = today + timedelta(days=7)
    upcoming_patients = Appointment.objects.filter(
        doctor=doctor,
        appointment_date__gt=today,
        appointment_date__lte=week_end,
        status__in=["Pending", "Confirmed"],
    ).select_related("patient__user").order_by("appointment_date", "appointment_time")[:10]

    # ---------------- Emergency / high-risk patients (all upcoming, not just today) ----------------
    emergency_patients = Appointment.objects.filter(
        doctor=doctor,
        appointment_date__gte=today,
        risk_level="HIGH",
        status__in=["Pending", "Confirmed"],
    ).select_related("patient__user").order_by("appointment_date", "appointment_time")

    # ---------------- Recent medical records & prescriptions ----------------
    from medical_records.models import MedicalRecord
    from prescriptions.models import Prescription
    recent_records = MedicalRecord.objects.filter(
        appointment__doctor=doctor
    ).select_related("appointment__patient__user").order_by("-created_at")[:5]

    recent_prescriptions = Prescription.objects.filter(
        medical_record__appointment__doctor=doctor
    ).select_related("medical_record__appointment__patient__user").order_by("-id")[:5]

    # ---------------- Analytics (last 7 days appointment outcome breakdown) ----------------
    # ========================= ANALYTICS =========================

    import json
    from datetime import timedelta
    from django.db.models import Count

    week_start = today - timedelta(days=6)

    appointments_week = Appointment.objects.filter(
        doctor=doctor,
        appointment_date__gte=week_start,
        appointment_date__lte=today
    )

    # ---------------- Appointment Status Chart ----------------

    appointment_chart = {
        "completed": appointments_week.filter(status="Completed").count(),
        "confirmed": appointments_week.filter(status="Confirmed").count(),
        "pending": appointments_week.filter(status="Pending").count(),
        "noshow": appointments_week.filter(status="No Show").count(),
    }

    appointment_chart = json.dumps(appointment_chart)

    # ---------------- Last 7 Days Trend ----------------

    trend_labels = []
    trend_data = []

    for i in range(6, -1, -1):

        day = today - timedelta(days=i)

        trend_labels.append(day.strftime("%d %b"))

        trend_data.append(
            Appointment.objects.filter(
                doctor=doctor,
                appointment_date=day
            ).count()
        )

    # ---------------- Male vs Female ----------------

    gender_stats = (
        Appointment.objects.filter(doctor=doctor)
        .values("patient__gender")
        .annotate(total=Count("id"))
    )

    male = 0
    female = 0

    for g in gender_stats:

        gender = (g["patient__gender"] or "").upper()

        if gender == "MALE":
            male = g["total"]

        elif gender == "FEMALE":
            female = g["total"]

    total_gender = male + female

    if total_gender:

        male_percentage = round((male / total_gender) * 100)

        female_percentage = round((female / total_gender) * 100)

    else:

        male_percentage = 0

        female_percentage = 0

    # ---------------- Peak Hour ----------------

    peak = (
        Appointment.objects.filter(doctor=doctor)
        .values("appointment_time")
        .annotate(total=Count("id"))
        .order_by("-total")
        .first()
    )

    if peak:

        peak_hour = peak["appointment_time"].strftime("%I:%M %p")

    else:

        peak_hour = "No Data"

    # ---------------- Weekly Revenue ----------------

    weekly_revenue = 0

    for appt in appointments_week.select_related("doctor"):

        if appt.status == "Completed":

            weekly_revenue += appt.doctor.consultation_fee

    # ---------------- Notifications (leave reminders, no-show alerts) ----------------
    notifications = []
    if today_leave:
        notifications.append({"type": "info", "text": "You are on leave today."})
    if emergency_patients:
        notifications.append({"type": "danger", "text": f"{emergency_patients.count()} high-risk patient(s) upcoming."})
    upcoming_leave = DoctorLeave.objects.filter(doctor=doctor, leave_date__gt=today, leave_date__lte=week_end).order_by("leave_date")
    for lv in upcoming_leave:
        notifications.append({"type": "warning", "text": f"Leave scheduled on {lv.leave_date}."})

    # ---------------- Recent messages ----------------
    try:
        from messaging.views import MESSAGES as _MESSAGES
        recent_messages = [
            m for m in _MESSAGES if m.get("receiver_id") == request.user.id or m.get("sender_id") == request.user.id
        ][-5:]
    except ImportError:
        # Messaging app doesn't expose MESSAGES this way in this project --
        # don't let that break the whole dashboard, just skip this widget.
        recent_messages = []

    context = {

    "doctor": doctor,

    "doctor_status": doctor_status,

    "todays_appointments": todays_appointments,

    "total_patients": total_patients,

    "total_completed": total_completed,

    "noshow_rate": noshow_rate,

    "high_risk_today": high_risk_today,

    "today_leave": today_leave,

    "today_attendance": today_attendance,

    "availability": availability,

    "admin_messages": [],
     "appointment_chart": appointment_chart,

    "trend_labels": json.dumps(trend_labels),

    "trend_data": json.dumps(trend_data),

    "male_percentage": male_percentage,

    "female_percentage": female_percentage,

    "peak_hour": peak_hour,

    "weekly_revenue": weekly_revenue,
    "upcoming_patients": upcoming_patients,
    "emergency_patients": emergency_patients,
    "recent_records": recent_records,
    "recent_prescriptions": recent_prescriptions,
    "appointment_chart": appointment_chart,
    "notifications": notifications,
    "recent_messages": recent_messages,

}

    return render(
        request,
        "hospital/doctor_dashboard.html",
        context,
    )
"""
ADD THIS to hospital/views.py (or wherever your doctor-role views live)
"""


@login_required
def manage_leave(request):
    if request.user.role != "DOCTOR":
        messages.error(request, "Access denied.")
        return redirect("dashboard")

    doctor = request.user.doctor_profile

    if request.method == "POST":
        date_str = request.POST.get("leave_date")
        reason = request.POST.get("reason", "").strip()
        try:
            leave_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except (ValueError, TypeError):
            messages.error(request, "Invalid date.")
            return redirect("manage_leave")

        DoctorLeave.objects.get_or_create(
            doctor=doctor, leave_date=leave_date, defaults={"reason": reason}
        )
        messages.success(request, f"Leave added for {leave_date}.")
        return redirect("manage_leave")

    leaves = DoctorLeave.objects.filter(doctor=doctor).order_by("leave_date")
    return render(request, "hospital/manage_leave.html", {"leaves": leaves})


@login_required
def delete_leave(request, pk):
    leave = get_object_or_404(DoctorLeave, pk=pk, doctor=request.user.doctor_profile)
    leave.delete()
    messages.success(request, "Leave removed.")
    return redirect("manage_leave")
def generate_week_schedule(request, doctor_id):

    doctor = get_object_or_404(
        Doctor,
        pk=doctor_id
    )

    schedule = [

        ("Monday", "09:00", "13:00"),
        ("Monday", "14:00", "17:00"),

        ("Tuesday", "09:00", "13:00"),
        ("Tuesday", "14:00", "17:00"),

        ("Wednesday", "09:00", "13:00"),
        ("Wednesday", "14:00", "17:00"),

        ("Thursday", "09:00", "13:00"),
        ("Thursday", "14:00", "17:00"),

        ("Friday", "09:00", "13:00"),
        ("Friday", "14:00", "17:00"),

        ("Saturday", "09:00", "12:00"),
    ]

    created = 0

    for day, start, end in schedule:

        obj, is_created = DoctorAvailability.objects.get_or_create(

            doctor=doctor,

            day_of_week=day,

            start_time=start,

            end_time=end,

            defaults={

                "is_available": True

            }

        )

        if is_created:
            created += 1

    messages.success(

        request,

        f"{created} availability slots created."

    )

    return redirect("availability_list")
from django.utils import timezone

def doctor_checkin(request):

    doctor = Doctor.objects.get(user=request.user)

    attendance, created = DoctorAttendance.objects.get_or_create(
        doctor=doctor,
        attendance_date=timezone.now().date(),
    )

    attendance.status = "AVAILABLE"
    attendance.check_in_time = timezone.now().time()
    attendance.save()

    status, created = DoctorStatus.objects.get_or_create(
        doctor=doctor
    )

    status.status = "AVAILABLE"
    status.save()

    return redirect("doctor_dashboard")
from django.utils import timezone

def doctor_checkout(request):

    doctor = Doctor.objects.get(user=request.user)

    attendance = DoctorAttendance.objects.filter(
        doctor=doctor,
        attendance_date=timezone.now().date()
    ).first()

    if attendance:
        attendance.check_out_time = timezone.now().time()
        attendance.status = "LEAVE"
        attendance.save()

    status, created = DoctorStatus.objects.get_or_create(
        doctor=doctor
    )

    status.status = "NOT_AVAILABLE"
    status.save()

    return redirect("doctor_dashboard")
from .models import DoctorStatus, Doctor

@login_required
def update_doctor_status(request):

    doctor = Doctor.objects.get(user=request.user)

    status, created = DoctorStatus.objects.get_or_create(
        doctor=doctor,
        defaults={
            "status": "AVAILABLE"
        }
    )
    if request.method == "POST":

        form = DoctorStatusForm(
            request.POST,
            instance=status
        )

        if form.is_valid():
            form.save()
            return redirect("doctor_dashboard")

    else:

        form = DoctorStatusForm(
            instance=status
        )

    return render(
        request,
        "hospital/update_status.html",
        {
            "form": form
        }
    )
@login_required
def attendance_list(request):

    attendance = DoctorAttendance.objects.select_related(
        "doctor__user"
    ).order_by("-attendance_date")

    return render(
        request,
        "hospital/attendance_list.html",
        {
            "attendance": attendance
        }
    )
@login_required
def doctor_status_list(request):

    status = DoctorStatus.objects.select_related(
        "doctor__user"
    )

    return render(
        request,
        "hospital/status_list.html",
        {
            "status": status
        }
    )
@login_required
def doctor_leave_list(request):

    leaves = DoctorLeave.objects.select_related(
        "doctor__user"
    )

    return render(
        request,
        "hospital/doctor_leave_list.html",
        {
            "leaves": leaves
        }
    )
@login_required
def doctor_leave_create(request):

    if request.method == "POST":

        form = DoctorLeaveForm(request.POST)

        if form.is_valid():

            leave = form.save()

            doctor = leave.doctor

            status, created = DoctorStatus.objects.get_or_create(
                doctor=doctor
            )

            status.status = "ON_LEAVE"
            status.save()

            messages.success(
                request,
                "Doctor Leave Added Successfully."
            )

            return redirect("doctor_leave_list")

    else:

        form = DoctorLeaveForm()

    return render(
        request,
        "hospital/doctor_leave_form.html",
        {
            "form": form
        }
    )
@login_required
def doctor_leave_delete(request, pk):

    leave = get_object_or_404(
        DoctorLeave,
        pk=pk
    )

    doctor = leave.doctor

    leave.delete()

    status, created = DoctorStatus.objects.get_or_create(
        doctor=doctor
    )

    status.status = "AVAILABLE"
    status.save()

    messages.success(
        request,
        "Leave Deleted Successfully."
    )

    return redirect("doctor_leave_list")
@login_required
def contact_admin(request):
    return redirect("chat_widget")


@login_required
def project_overview(request):
    from patients.models import Patient
    from hospital.models import Doctor, Department
    from appointments.models import Appointment
    from medical_records.models import MedicalRecord
    from prescriptions.models import Prescription
    from billing.models import Bill

    stats = {
        "patients": Patient.objects.count(),
        "doctors": Doctor.objects.filter(is_active=True).count(),
        "departments": Department.objects.count(),
        "appointments": Appointment.objects.count(),
        "high_risk": Appointment.objects.filter(risk_level="HIGH").count(),
        "medical_records": MedicalRecord.objects.count(),
        "prescriptions": Prescription.objects.count(),
        "bills": Bill.objects.count(),
    }

    return render(request, "hospital/project_overview.html", {"stats": stats})