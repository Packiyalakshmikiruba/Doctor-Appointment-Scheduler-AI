"""
chatbot/tools.py
LangChain tools for the Doctor Appointment Scheduler AI agent.

Flow this file implements:
    Search Doctor Tool -> Availability Tool -> Appointment Tool -> ML Prediction Tool
"""

import os
import json
from datetime import datetime
from billing.models import Bill
import joblib
from django.conf import settings
from django.db.models import Q
from langchain.tools import tool

from hospital.models import Doctor, DoctorAvailability
from patients.models import Patient
from appointments.models import Appointment
from appointments.notifications import send_appointment_confirmation

# ---------------------------------------------------------------------------
# ML model — loaded once at import time (not per-request) for performance.
# ---------------------------------------------------------------------------
ML_MODEL_PATH = os.path.join(settings.BASE_DIR, "ml_model", "noshow_model.pkl")
ENCODERS_PATH = os.path.join(settings.BASE_DIR, "ml_model", "encoders.pkl")
METRICS_PATH = os.path.join(settings.BASE_DIR, "ml_model", "model_metrics.json")

_model = joblib.load(ML_MODEL_PATH)
_encoders = joblib.load(ENCODERS_PATH)

with open(METRICS_PATH, "r") as f:
    _metrics = json.load(f)

# Loaded dynamically from training output -- always stays in sync with
# whatever threshold train_model.py actually used, no manual sync needed.
OPERATING_THRESHOLD = _metrics["threshold"]

FEATURE_ORDER = [
    "age",
    "gender",
    "department",
    "lead_time_days",
    "appointment_weekday",
    "appointment_time",
    "sms_reminder_sent",
    "prior_visits",
    "prior_noshows",
    "history_noshow_ratio",
    "distance_from_clinic",
]


def _safe_encode(column: str, value: str) -> int:
    """
    Encode a categorical value using the trained LabelEncoder.
    Falls back to 0 if the value was never seen during training,
    instead of crashing the whole prediction.
    """
    le = _encoders[column]
    try:
        return int(le.transform([str(value)])[0])
    except ValueError:
        return 0


# ---------------------------------------------------------------------------
# Tool 1 — Search Doctor
# ---------------------------------------------------------------------------
@tool
def search_doctor(query: str) -> str:
    """
    Search for active doctors by department name or specialization.
    Example inputs: "Cardiology", "Cardiologist", "ENT".
    Returns doctor_id, name, specialization, department, and consultation fee.
    """
    doctors = (
        Doctor.objects.filter(is_active=True)
        .filter(
            Q(department__department_name__icontains=query)
            | Q(specialization__icontains=query)
        )
        .select_related("user", "department")
    )

    if not doctors.exists():
        return f"No active doctors found matching '{query}'."

    lines = []
    for d in doctors:
        name = d.user.get_full_name() or d.user.username
        lines.append(
            f"doctor_id: {d.id} | Dr. {name} | {d.specialization} | "
            f"Dept: {d.department.department_name} | Fee: ₹{d.consultation_fee}"
        )
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Tool 2 — Check Availability
# ---------------------------------------------------------------------------
@tool
def check_doctor_availability(doctor_id: int) -> str:
    """
    Check a doctor's weekly available time slots by doctor_id.
    Use search_doctor first to find the doctor_id.
    """
    slots = DoctorAvailability.objects.filter(
        doctor_id=doctor_id, is_available=True
    ).order_by("day_of_week", "start_time")

    if not slots.exists():
        return f"No available slots found for doctor_id {doctor_id}."

    lines = [
        f"{s.day_of_week}: {s.start_time.strftime('%I:%M %p')} - {s.end_time.strftime('%I:%M %p')}"
        for s in slots
    ]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Tool 3 — Book Appointment (now with availability + double-booking checks)
# ---------------------------------------------------------------------------
@tool
def book_appointment(
    patient_id: int, doctor_id: int, appointment_date: str, appointment_time: str, reason: str
) -> str:
    """
    Book an appointment.
    appointment_date must be in YYYY-MM-DD format.
    appointment_time must be in HH:MM 24-hour format (e.g. "14:30").
    Returns the new appointment_id, which is needed for risk prediction.
    """
    try:
        patient = Patient.objects.get(id=patient_id)
        doctor = Doctor.objects.get(id=doctor_id, is_active=True)
    except Patient.DoesNotExist:
        return f"No patient found with patient_id {patient_id}."
    except Doctor.DoesNotExist:
        return f"No active doctor found with doctor_id {doctor_id}."

    try:
        date_obj = datetime.strptime(appointment_date, "%Y-%m-%d").date()
        time_obj = datetime.strptime(appointment_time, "%H:%M").time()
    except ValueError:
        return "Invalid date/time format. Use YYYY-MM-DD for date and HH:MM for time."

    # --- Doctor availability check (same rule as the web booking form) ---
    day_name = date_obj.strftime("%A")
    availability = DoctorAvailability.objects.filter(
        doctor=doctor, day_of_week=day_name, is_available=True
    ).first()

    if not availability:
        doctor_name = doctor.user.get_full_name() or doctor.user.username
        return f"Dr. {doctor_name} is not available on {day_name}."

    if time_obj < availability.start_time or time_obj > availability.end_time:
        return (f"Doctor is available only between "
                f"{availability.start_time} and {availability.end_time} on {day_name}.")

    # --- Double-booking check ---
    clash = Appointment.objects.filter(
        doctor=doctor, appointment_date=date_obj, appointment_time=time_obj
    ).exists()

    if clash:
        return "This doctor already has an appointment at this time. Please choose a different slot."

    # --- Compute prior visit history for the ML features ---
    past_appts = Appointment.objects.filter(patient=patient, status__in=["Completed", "No Show"])
    prior_visits = past_appts.count()
    prior_noshows = Appointment.objects.filter(patient=patient, status="No Show").count()
    history_noshow_ratio = round(prior_noshows / prior_visits, 3) if prior_visits > 0 else 0.0

    appt = Appointment.objects.create(
        patient=patient,
        doctor=doctor,
        appointment_date=date_obj,
        appointment_time=time_obj,
        reason=reason,
        status="Pending",
        prior_visits=prior_visits,
        prior_noshows=prior_noshows,
        history_noshow_ratio=history_noshow_ratio,
        distance_from_clinic=float(patient.distance_from_clinic),
    )
    send_appointment_confirmation(appt)


    return f"Appointment booked successfully. appointment_id: {appt.id}"


# ---------------------------------------------------------------------------
# Tool 4 — Predict No-Show Risk
# ---------------------------------------------------------------------------
@tool
def predict_noshow_risk(appointment_id: int) -> str:
    """
    Predict the no-show risk for a booked appointment using the trained ML model.
    Saves the risk_score and risk_level back onto the Appointment record.
    """
    try:
        appt = Appointment.objects.select_related("patient", "doctor__department").get(
            id=appointment_id
        )
    except Appointment.DoesNotExist:
        return f"No appointment found with appointment_id {appointment_id}."

    patient = appt.patient

    features = [
        patient.age,
        _safe_encode("gender", patient.gender),
        _safe_encode("department", appt.doctor.department.department_name),
        appt.lead_time_days,
        appt.appointment_date.weekday(),
        _safe_encode("appointment_time", appt.time_bucket),
        int(appt.sms_reminder_sent),
        appt.prior_visits,
        appt.prior_noshows,
        appt.history_noshow_ratio,
        appt.distance_from_clinic,
    ]

    risk_prob = _model.predict_proba([features])[0][1]
    risk_pct = round(risk_prob * 100, 1)

    if risk_prob >= 0.60:
        risk_level = "HIGH"
    elif risk_prob >= OPERATING_THRESHOLD:
        risk_level = "MEDIUM"
    else:
        risk_level = "LOW"

    appt.risk_score = round(float(risk_prob), 4)
    appt.risk_level = risk_level
    appt.save(update_fields=["risk_score", "risk_level"])

    return (
        f"Appointment {appointment_id} risk assessment: "
        f"{risk_pct}% no-show probability ({risk_level} risk)."
    )
@tool
def get_billing_info(appointment_id: int) -> str:
    """
    Get the billing breakdown and payment status for a given appointment_id.
    Use this when a patient asks about their bill, fees, or how much they owe.
    """
    try:
        bill = Bill.objects.select_related("appointment__patient", "appointment__doctor").get(
            appointment_id=appointment_id
        )
    except Bill.DoesNotExist:
        return f"No bill has been generated yet for appointment_id {appointment_id}."

    return (
        f"Bill #{bill.id} for {bill.appointment.patient}:\n"
        f"Consultation Fee: ₹{bill.consultation_fee}\n"
        f"Medicine Cost: ₹{bill.medicine_cost}\n"
        f"Lab Test Cost: ₹{bill.lab_test_cost}\n"
        f"GST: ₹{bill.gst}\n"
        f"Discount: -₹{bill.discount}\n"
        f"Total Amount: ₹{bill.total_amount}\n"
        f"Amount Paid: ₹{bill.total_paid}\n"
        f"Balance Due: ₹{bill.balance_due}\n"
        f"Payment Status: {bill.payment_status}"
    )