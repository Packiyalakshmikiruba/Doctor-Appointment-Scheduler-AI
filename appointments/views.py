from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q
from django.core.paginator import Paginator
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django import forms
from hospital.models import Department, Doctor
from .forms import AppointmentForm
from .models import Appointment
from patients.models import Patient
from .notifications import send_appointment_confirmation
from appointments.booking_service import book_appointment_full, handle_cancellation, BookingError


@login_required
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


@login_required
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


@login_required
def appointment_delete(request, pk):

    appointment = get_object_or_404(Appointment, pk=pk)

    if request.method == "POST":
        appointment.delete()
        return redirect("appointment_list")

    return render(request, "appointments/appointment_confirm_delete.html", {"appointment": appointment})


@login_required
def mark_confirmed(request, pk):
    appointment = get_object_or_404(Appointment, pk=pk)
    appointment.status = "Confirmed"
    appointment.save()
    return redirect("appointment_list")


@login_required
def mark_noshow(request, pk):
    appointment = get_object_or_404(Appointment, pk=pk)
    appointment.status = "No Show"
    appointment.save()
    return redirect("appointment_list")


@login_required
def mark_cancelled(request, pk):
    appointment = get_object_or_404(Appointment, pk=pk)
    appointment.status = "Cancelled"
    appointment.save()

    try:
        handle_cancellation(appointment)
    except Exception:
        pass

    return redirect("appointment_list")


def get_doctors_by_department(request, department_id):
    doctors = Doctor.objects.filter(department_id=department_id, is_active=True).select_related("user")
    data = [
        {"id": d.id, "name": f"Dr. {d.user.get_full_name() or d.user.username}", "fee": str(d.consultation_fee)}
        for d in doctors
    ]
    return JsonResponse({"doctors": data})


def get_doctor_availability(request, doctor_id):
    from hospital.models import DoctorAvailability
    slots = DoctorAvailability.objects.filter(
        doctor_id=doctor_id, is_available=True
    ).order_by("day_of_week")
    data = [
        {
            "day": s.day_of_week,
            "start": s.start_time.strftime("%I:%M %p"),
            "end": s.end_time.strftime("%I:%M %p"),
            "start_24h": s.start_time.strftime("%H:%M"),
            "end_24h": s.end_time.strftime("%H:%M"),
        }
        for s in slots
    ]
    return JsonResponse({"availability": data})


# ---------------- Voice Booking ----------------
# Voice booking reuses the SAME chat agent as the text chat widget --
# see chatbot/views.py chat_api and appointments/templates/appointments/voice_booking.html.
# There is no separate voice-only booking endpoint -- one booking brain,
# two input methods (typing or speaking).

def voice_booking_page(request):
    return render(request, "appointments/voice_booking.html")


@login_required
def patient_cancel_appointment(request, pk):
    appointment = get_object_or_404(Appointment, pk=pk)

    # Security: patient தன் appointment-ஐ மட்டும் cancel பண்ண முடியும்
    if appointment.patient != getattr(request.user, "patient_profile", None):
        messages.error(request, "Access denied.")
        return redirect("dashboard")

    if request.method == "POST":
        appointment.status = "Cancelled"
        appointment.save()
        messages.success(request, "Appointment cancelled.")
        return redirect("dashboard")

    return render(request, "appointments/patient_cancel_confirm.html", {"appointment": appointment})


@login_required
def patient_history_view(request, patient_id):
    if request.user.role != "DOCTOR":
        messages.error(request, "Access denied.")
        return redirect("dashboard")

    patient = get_object_or_404(Patient, pk=patient_id)

    appointments = Appointment.objects.filter(patient=patient).select_related(
        "doctor__user", "doctor__department"
    ).order_by("-appointment_date")

    from medical_records.models import MedicalRecord
    records = MedicalRecord.objects.filter(appointment__patient=patient).select_related(
        "appointment__doctor__user"
    ).prefetch_related("prescriptions").order_by("-created_at")

    return render(request, "appointments/patient_history.html", {
        "patient": patient,
        "appointments": appointments,
        "records": records,
    })
@login_required
def appointment_create(request):

    if request.user.role not in ("ADMIN", "PATIENT"):
        messages.error(request, "Access denied.")
        return redirect("dashboard")

    is_self_booking = request.user.role == "PATIENT"

    if request.method == "POST":

        form = AppointmentForm(request.POST)

        if is_self_booking:
            form.data = form.data.copy()
            form.data["patient"] = request.user.patient_profile.id

        if form.is_valid():

            try:

                appointment = book_appointment_full(
                    patient=form.cleaned_data["patient"],
                    doctor=form.cleaned_data["doctor"],
                    appointment_date=form.cleaned_data["appointment_date"],
                    appointment_time=form.cleaned_data["appointment_time"],
                    reason=form.cleaned_data["reason"],
                )

                messages.success(
                    request,
                    "Appointment booked successfully."
                )

                return redirect("dashboard")

            except BookingError as e:
                messages.error(request, e.message)

    else:

        form = AppointmentForm()

        if is_self_booking:
            form.fields["patient"].widget = forms.HiddenInput()
            form.fields["patient"].initial = request.user.patient_profile.id

    return render(
        request,
        "appointments/appointment_form.html",
        {
            "form": form,
            "is_self_booking": is_self_booking,
        },
    )