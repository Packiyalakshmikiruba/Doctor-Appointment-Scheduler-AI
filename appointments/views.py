from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q
from hospital.models import Department
from django.core.paginator import Paginator
from .forms import AppointmentForm
from .models import Appointment


def appointment_create(request):

    if request.method == "POST":

        form = AppointmentForm(request.POST)

        if form.is_valid():
            appointment = form.save(commit=False)
            appointment.status = "Pending"   # எப்போதும் Pending-ஆ தான் ஆரம்பிக்கும்
            appointment.save()
            return redirect("appointment_list")

    else:
        form = AppointmentForm()

    return render(
        request,
        "appointments/appointment_form.html",
        {"form": form},
    )


def appointment_list(request):

    appointments = Appointment.objects.select_related(
        "patient__user",
        "doctor__user",
        "doctor__department",
    ).all()

    # ---------------- Search & Filters ----------------

    patient = request.GET.get("patient", "").strip()
    doctor = request.GET.get("doctor", "").strip()
    department = request.GET.get("department", "").strip()
    status = request.GET.get("status", "").strip()
    risk = request.GET.get("risk", "").strip()
    from_date = request.GET.get("from_date", "").strip()
    to_date = request.GET.get("to_date", "").strip()

    # Patient Search
    if patient:
        appointments = appointments.filter(
            Q(patient__user__username__icontains=patient) |
            Q(patient__user__first_name__icontains=patient) |
            Q(patient__user__last_name__icontains=patient)
        )

    # Doctor Search
    if doctor:
        appointments = appointments.filter(
            Q(doctor__user__username__icontains=doctor) |
            Q(doctor__user__first_name__icontains=doctor) |
            Q(doctor__user__last_name__icontains=doctor)
        )

    # Department Filter
    if department:
        appointments = appointments.filter(
            doctor__department__id=department
        )

    # Status Filter
    if status:
        appointments = appointments.filter(
            status=status
        )

    # Risk Filter
    if risk:
        appointments = appointments.filter(
            risk_level=risk
        )

    # Date Filter
    if from_date:
        appointments = appointments.filter(
            appointment_date__gte=from_date
        )

    if to_date:
        appointments = appointments.filter(
            appointment_date__lte=to_date
        )

    appointments = appointments.order_by(
        "-appointment_date",
        "-appointment_time",
    )
    # Pagination

    paginator = Paginator(appointments, 10)

    page_number = request.GET.get("page")

    appointments = paginator.get_page(page_number)
    return render(
        request,
        "appointments/appointment_list.html",
        {
            "appointments": appointments,
            "departments": Department.objects.all(),

            "patient_search": patient,
            "doctor_search": doctor,
            "selected_department": department,
            "selected_status": status,
            "selected_risk": risk,
            "from_date": from_date,
            "to_date": to_date,
        },
    )


def appointment_update(request, pk):

    appointment = get_object_or_404(Appointment, pk=pk)

    if request.method == "POST":
        form = AppointmentForm(request.POST, instance=appointment)

        if form.is_valid():
            form.save()   # இதுவும் pre_save trigger ஆகும், risk_score refresh ஆகும்
            return redirect("appointment_list")

    else:
        form = AppointmentForm(instance=appointment)

    return render(
        request,
        "appointments/appointment_form.html",
        {"form": form},
    )


def appointment_delete(request, pk):

    appointment = get_object_or_404(Appointment, pk=pk)

    if request.method == "POST":
        appointment.delete()
        return redirect("appointment_list")

    return render(
        request,
        "appointments/appointment_confirm_delete.html",
        {"appointment": appointment},
    )
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
import json
from datetime import datetime, timedelta
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

# 1. Models & Predictor Import
from appointments.models import Appointment
from ai_prediction.models import Prediction
from ai_prediction.predictor import predict_no_show  # Exact predictor function import!

@csrf_exempt
# appointments/views.py

@csrf_exempt
def voice_call_booking_api(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            spoken_text = data.get("spoken_text", "").lower()

            patient = getattr(request.user, 'patient', None) if request.user.is_authenticated else None
            from patients.models import Patient
            from hospital.models import Doctor
            
            if not patient:
                patient = Patient.objects.first()

            # Dynamic-a Doctor details edukkom
            doctor = Doctor.objects.first() 
            
            # 1. Appointment Date Calculation
            appt_date = datetime.now().date() + timedelta(days=1)  # Tomorrow
            
            # Oruvelai spoken_text-la 'sunday' irundha, adutha Sunday date-ah edukkirom
            if "sunday" in spoken_text:
                days_until_sunday = (6 - datetime.now().weekday()) % 7
                if days_until_sunday == 0:
                    days_until_sunday = 7
                appt_date = datetime.now().date() + timedelta(days=days_until_sunday)

            # 2. DOCTOR SUNDAY / AVAILABILITY CHECK 🚫
            # Doctor-oda available days-la Sunday illana, or Sunday check block:
            if appt_date.strftime('%A') == 'Sunday':
                response_msg = f"Sorry, Dr. {doctor} is not available on Sunday. Please choose another day from Monday to Saturday."
                return JsonResponse({
                    "status": "error",
                    "voice_response": response_msg
                })

            if not patient or not doctor:
                return JsonResponse({"status": "error", "voice_response": "Patient or Doctor details not found."})

            # 3. Predict & Book (If Doctor is Available)
            ml_input_data = {
                "gender": getattr(patient, 'gender', 'M'),
                "department": getattr(doctor.department, 'name', 'General') if hasattr(doctor, 'department') else 'General',
                "appointment_weekday": appt_date.strftime('%A'),
                "appointment_time": "10:00:00",
                "age": getattr(patient, 'age', 30),
                "lead_time": (appt_date - datetime.now().date()).days,
                "sms_reminder": 1
            }

            probability, risk_level = predict_no_show(ml_input_data)
            risk_score_percentage = round(probability * 100, 2)

            appointment = Appointment.objects.create(
                patient=patient,
                doctor=doctor,
                appointment_date=appt_date,
                status='Pending'
            )

            Prediction.objects.create(
                appointment=appointment,
                risk_score=risk_score_percentage,
                prediction=risk_level,
                confidence_score=round((1 - abs(0.5 - probability)) * 100, 2),
                model_version="v1.0-xgboost"
            )

            voice_msg = (
                f"Your appointment with Dr. {doctor} for {appt_date.strftime('%A, %B %d')} is confirmed! "
                f"No-Show risk evaluated as {risk_level} ({risk_score_percentage}%)."
            )

            return JsonResponse({
                "status": "success",
                "voice_response": voice_msg,
                "risk_level": risk_level
            })

        except Exception as e:
            return JsonResponse({"status": "error", "voice_response": f"Error: {str(e)}"})

    return JsonResponse({"status": "error", "voice_response": "Invalid Request Method"})
def voice_booking_page(request):
    """
    Renders the HTML Voice Assistant Page
    """
    return render(request, 'appointments/voice_booking.html')


# 2. Voice Booking API Endpoint
@csrf_exempt
def voice_call_booking_api(request):
    """
    Processes voice speech text, runs AI prediction, and creates appointment
    """
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            spoken_text = data.get("spoken_text", "").lower()
            
            # Simple success response for testing
            return JsonResponse({
                "status": "success",
                "voice_response": f"Received booking request: '{spoken_text}'. Appointment processed successfully!"
            })
        except Exception as e:
            return JsonResponse({"status": "error", "voice_response": str(e)})

    return JsonResponse({"status": "error", "voice_response": "Invalid HTTP Method"})