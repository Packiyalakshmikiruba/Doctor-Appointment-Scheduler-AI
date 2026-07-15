import json
from datetime import datetime, timedelta
from .notifications import send_appointment_confirmation

from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from hospital.models import Department, Doctor, DoctorAvailability
from patients.models import Patient
from .forms import AppointmentForm
from .models import Appointment


def appointment_create(request):

    doctors = Doctor.objects.all()

    if request.method == "POST":

        form = AppointmentForm(request.POST)

        if form.is_valid():
            appointment = form.save(commit=False)
            appointment.status = "Pending"
            appointment.save()
            return redirect("appointment_list")

    else:

        form = AppointmentForm()

    return render(
        request,
        "appointments/appointment_form.html",
        {
            "form": form,
            "doctors": doctors,
        },
    )

def appointment_list(request):

    appointments = Appointment.objects.select_related(
        "patient__user", "doctor__user", "doctor__department",
    ).all()

    patient = request.GET.get("patient", "").strip()
    doctor = request.GET.get("doctor", "").strip()
    department = request.GET.get("department", "").strip()
    status = request.GET.get("status", "").strip()
    risk = request.GET.get("risk", "").strip()
    from_date = request.GET.get("from_date", "").strip()
    to_date = request.GET.get("to_date", "").strip()

    if patient:
        appointments = appointments.filter(
            Q(patient__user__username__icontains=patient) |
            Q(patient__user__first_name__icontains=patient) |
            Q(patient__user__last_name__icontains=patient)
        )

    if doctor:
        appointments = appointments.filter(
            Q(doctor__user__username__icontains=doctor) |
            Q(doctor__user__first_name__icontains=doctor) |
            Q(doctor__user__last_name__icontains=doctor)
        )

    if department:
        appointments = appointments.filter(doctor__department__id=department)

    if status:
        appointments = appointments.filter(status=status)

    if risk:
        appointments = appointments.filter(risk_level=risk)

    if from_date:
        appointments = appointments.filter(appointment_date__gte=from_date)

    if to_date:
        appointments = appointments.filter(appointment_date__lte=to_date)

    appointments = appointments.order_by("-appointment_date", "-appointment_time")

    paginator = Paginator(appointments, 10)
    page_number = request.GET.get("page")
    appointments = paginator.get_page(page_number)

    return render(request, "appointments/appointment_list.html", {
        "appointments": appointments,
        "departments": Department.objects.all(),
        "patient_search": patient,
        "doctor_search": doctor,
        "selected_department": department,
        "selected_status": status,
        "selected_risk": risk,
        "from_date": from_date,
        "to_date": to_date,
    })


def appointment_update(request, pk):

    appointment = get_object_or_404(Appointment, pk=pk)

    if request.method == "POST":
        form = AppointmentForm(request.POST, instance=appointment)
        if form.is_valid():
            form.save()
            return redirect("appointment_list")
    else:
        form = AppointmentForm(instance=appointment)

    return render(request, "appointments/appointment_form.html", {"form": form})


def appointment_delete(request, pk):

    appointment = get_object_or_404(Appointment, pk=pk)

    if request.method == "POST":
        appointment.delete()
        return redirect("appointment_list")

    return render(request, "appointments/appointment_confirm_delete.html", {"appointment": appointment})


def mark_confirmed(request, pk):
    appointment = get_object_or_404(Appointment, pk=pk)
    appointment.status = "Confirmed"
    appointment.save()
    return redirect("appointment_list")


def mark_cancelled(request, pk):
    appointment = get_object_or_404(Appointment, pk=pk)
    appointment.status = "Cancelled"
    appointment.save()
    return redirect("appointment_list")


def mark_noshow(request, pk):
    appointment = get_object_or_404(Appointment, pk=pk)
    appointment.status = "No Show"
    appointment.save()
    return redirect("appointment_list")


def get_doctors_by_department(request, department_id):
    doctors = Doctor.objects.filter(department_id=department_id, is_active=True).select_related("user")
    data = [
        {"id": d.id, "name": f"Dr. {d.user.get_full_name() or d.user.username}", "fee": str(d.consultation_fee)}
        for d in doctors
    ]
    return JsonResponse({"doctors": data})


# ---------------- Voice Booking ----------------

def voice_booking_page(request):
    return render(request, "appointments/voice_booking.html")


@csrf_exempt
def voice_call_booking_api(request):
    """
    Books an appointment from spoken text. Risk score is computed
    automatically by the pre_save signal (appointments/signals.py) --
    no manual prediction call needed here, avoiding duplicate logic.
    """
    if request.method != "POST":
        return JsonResponse({"status": "error", "voice_response": "Invalid Request Method"})

    try:
        data = json.loads(request.body)
        spoken_text = data.get("spoken_text", "").lower()

        patient = getattr(request.user, "patient_profile", None) if request.user.is_authenticated else None
        if not patient:
            patient = Patient.objects.first()

        doctor = Doctor.objects.filter(is_active=True).first()

        if not patient or not doctor:
            return JsonResponse({"status": "error", "voice_response": "Patient or Doctor details not found."})

        # Determine appointment date from spoken text
        appt_date = datetime.now().date() + timedelta(days=1)

        if "sunday" in spoken_text:
            days_until_sunday = (6 - datetime.now().weekday()) % 7
            days_until_sunday = days_until_sunday or 7
            appt_date = datetime.now().date() + timedelta(days=days_until_sunday)

        # Availability check (reuses the same rule as the web booking form)
        day_name = appt_date.strftime("%A")
        availability = DoctorAvailability.objects.filter(
            doctor=doctor, day_of_week=day_name, is_available=True
        ).first()

        if not availability:
            return JsonResponse({
                "status": "error",
                "voice_response": (
                    f"Sorry, Dr. {doctor.user.get_full_name() or doctor.user.username} "
                    f"is not available on {day_name}. Please choose another day."
                ),
            })

        appt_time = availability.start_time

        # Create the appointment -- pre_save signal auto-computes risk_score/risk_level
        appointment = Appointment.objects.create(
            patient=patient,
            doctor=doctor,
            appointment_date=appt_date,
            appointment_time=appt_time,
            reason=f"Voice booking: {spoken_text}",
            status="Pending",
        )

        voice_msg = (
            f"Your appointment with Dr. {doctor.user.get_full_name() or doctor.user.username} "
            f"for {appt_date.strftime('%A, %B %d')} at {appt_time} is confirmed! "
            f"No-Show risk evaluated as {appointment.risk_level} "
            f"({round(appointment.risk_score * 100, 1)}%)."
        )

        return JsonResponse({
            "status": "success",
            "voice_response": voice_msg,
            "risk_level": appointment.risk_level,
        })

    except Exception as e:
        return JsonResponse({"status": "error", "voice_response": f"Error: {str(e)}"})

def appointment_create(request):

    if request.method == "POST":
        form = AppointmentForm(request.POST)

        if form.is_valid():
            appointment = form.save(commit=False)
            appointment.status = "Pending"
            appointment.save()

            send_appointment_confirmation(appointment)   # புது line

            return redirect("appointment_list")

    else:
        form = AppointmentForm()

    return render(request, "appointments/appointment_form.html", {"form": form})