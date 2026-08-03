import os
import json
from datetime import datetime
from datetime import timedelta
from datetime import date
import joblib
from django.conf import settings
from django.db.models import Q
from langchain.tools import tool
from hospital.models import (
    Doctor,
    DoctorAvailability,
    DoctorLeave,
    DoctorStatus,
)
from patients.models import Patient
from appointments.models import Appointment
from billing.models import Bill

# =====================================================
# ML MODEL LOADING
# =====================================================

ML_MODEL_PATH = os.path.join(
    settings.BASE_DIR,
    "ml_model",
    "noshow_model.pkl",
)

ENCODER_PATH = os.path.join(
    settings.BASE_DIR,
    "ml_model",
    "encoders.pkl",
)

METRIC_PATH = os.path.join(
    settings.BASE_DIR,
    "ml_model",
    "model_metrics.json",
)


try:

    MODEL = joblib.load(ML_MODEL_PATH)

    ENCODERS = joblib.load(ENCODER_PATH)

    with open(METRIC_PATH, "r") as f:

        METRICS = json.load(f)

    OPERATING_THRESHOLD = METRICS["operating_threshold"]

except Exception:

    MODEL = None

    ENCODERS = {}

    OPERATING_THRESHOLD = 0.50


# =====================================================
# HELPER FUNCTIONS
# =====================================================

def calculate_age(dob):

    today = date.today()

    return (

        today.year

        - dob.year

        - (

            (today.month, today.day)

            <

            (dob.month, dob.day)

        )

    )


def safe_encode(column, value):

    if column not in ENCODERS:

        return 0

    encoder = ENCODERS[column]

    try:

        return int(

            encoder.transform([str(value)])[0]

        )

    except Exception:

        return 0


# =====================================================
# SEARCH DOCTOR
# =====================================================

@tool
def search_doctor(query: str) -> str:
    """
    Search doctor by

    Name
    Department
    Specialization
    """

    doctors = (
        Doctor.objects
        .filter(is_active=True)
        .filter(
            Q(user__first_name__icontains=query)
            | Q(user__last_name__icontains=query)
            | Q(user__username__icontains=query)
            | Q(department__department_name__icontains=query)
            | Q(specialization__icontains=query)
        )
        .select_related(
            "user",
            "department",
        )
    )

    if not doctors.exists():

        return "No doctor found."

    result = []

    for doctor in doctors:

        status = getattr(
            doctor,
            "current_status",
            None,
        )

        if status:

            if status and status.status != "AVAILABLE":
                continue

        doctor_name = (
            doctor.user.get_full_name()
            or doctor.user.username
        )

        result.append(
            f"""
Doctor ID : {doctor.id}

Doctor Name : Dr. {doctor_name}

Department : {doctor.department.department_name}

Specialization : {doctor.specialization}

Consultation Fee : ₹{doctor.consultation_fee}
"""
        )

    if not result:

        return "No available doctor."

    return "\n".join(result)
# =====================================================
# DOCTOR AVAILABILITY
# =====================================================

@tool
def check_doctor_availability(doctor_id: int) -> str:
    """
    Returns doctor's weekly schedule.

    Example:
    Doctor ID = 1
    """

    try:

        doctor = (

            Doctor.objects

            .select_related(
                "user",
                "department"
            )

            .get(
                id=doctor_id,
                is_active=True
            )

        )

    except Doctor.DoesNotExist:

        return "Doctor not found."

    schedules = (

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

    if not schedules.exists():

        return "Doctor has no available schedule."

    reply = []

    doctor_name = (

        doctor.user.get_full_name()

        or

        doctor.user.username

    )

    reply.append(

        f"Dr. {doctor_name}"

    )

    reply.append(

        f"Department : {doctor.department.department_name}"

    )

    reply.append("")

    reply.append("Weekly Schedule")

    reply.append("--------------------------")

    for slot in schedules:

        reply.append(

            f"{slot.day_of_week}"

            f" : "

            f"{slot.start_time.strftime('%I:%M %p')}"

            f" - "

            f"{slot.end_time.strftime('%I:%M %p')}"

        )

    return "\n".join(reply)


# =====================================================
# NEXT AVAILABLE SLOT
# =====================================================

@tool
def find_next_available_slot(doctor_id: int) -> str:
    """
    Finds doctor's next available day.

    Uses Leave table also.
    """

    try:

        doctor = Doctor.objects.get(

            id=doctor_id,

            is_active=True

        )

    except Doctor.DoesNotExist:

        return "Doctor not found."

    today = date.today()

    weekdays = [

        "Monday",

        "Tuesday",

        "Wednesday",

        "Thursday",

        "Friday",

        "Saturday",

        "Sunday"

    ]

    for i in range(7):

        current_date = today + timedelta(days=i)

        day = current_date.strftime("%A")

        if DoctorLeave.objects.filter(

            doctor=doctor,

            leave_date=current_date

        ).exists():

            continue

        slots = (

            DoctorAvailability.objects

            .filter(

                doctor=doctor,

                day_of_week=day,

                is_available=True

            )

            .order_by(

                "start_time"

            )

        )

        if slots.exists():

            result = []

            result.append(

                f"Next Available Date : {current_date}"

            )

            result.append("")

            for slot in slots:

                result.append(

                    f"{slot.start_time.strftime('%I:%M %p')}"

                    f" - "

                    f"{slot.end_time.strftime('%I:%M %p')}"

                )

            return "\n".join(result)

    return "No available slots for the next 7 days."


# =====================================================
# TODAY'S AVAILABILITY
# =====================================================

@tool
def today_available_doctors() -> str:
    """
    Shows all doctors available today.
    """

    today = date.today()

    day = today.strftime("%A")

    doctors = (

        DoctorAvailability.objects

        .filter(

            day_of_week=day,

            is_available=True,

            doctor__is_active=True

        )

        .select_related(

            "doctor__user",

            "doctor__department"

        )

    )

    if not doctors.exists():

        return "No doctors available today."

    result = []

    result.append(

        f"Available Doctors Today ({day})"

    )

    result.append("")

    for slot in doctors:

        doctor = slot.doctor

        result.append(

            f"Dr. "

            f"{doctor.user.get_full_name()}"

        )

        result.append(

            f"{doctor.department.department_name}"

        )

        result.append(

            f"{slot.start_time.strftime('%I:%M %p')}"

            f" - "

            f"{slot.end_time.strftime('%I:%M %p')}"

        )

        result.append("")

    return "\n".join(result)
# =====================================================
# BOOK APPOINTMENT
# =====================================================

@tool
def book_appointment(
    patient_id: int,
    doctor_id: int,
    appointment_date: str,
    appointment_time: str,
    reason: str,
) -> str:
    """
    Books an appointment.
    appointment_date -> YYYY-MM-DD
    appointment_time -> HH:MM (24 hour)
    """
    if doctor_id is None:
        return "Doctor ID is required."

    if patient_id is None:
        return "Patient not found."

    if not appointment_date:
        return "Appointment date is required."

    if not appointment_time:
        return "Appointment time is required."

    if not reason:
        reason = "General Consultation"
    from appointments.notifications import send_appointment_confirmation

    # -------------------------------
    # Patient
    # -------------------------------
    try:
        patient = Patient.objects.select_related("user").get(id=patient_id)
    except Patient.DoesNotExist:
        return "Patient not found."

    # -------------------------------
    # Doctor (fetch FIRST, before checking status)
    # -------------------------------
    try:
        doctor = Doctor.objects.select_related("user", "department").get(
            id=doctor_id, is_active=True
        )
    except Doctor.DoesNotExist:
        return "Doctor not found."

    # -------------------------------
    # Doctor Current Status Check (now doctor is defined)
    # -------------------------------
    doctor_status = getattr(doctor, "current_status", None)

    if doctor_status:
        if doctor_status.status == "NOT_AVAILABLE":
            return "Doctor is currently not available."
        elif doctor_status.status == "BUSY":
            return "Doctor is currently busy."
        elif doctor_status.status == "EMERGENCY":
            return "Doctor is attending an emergency case."
        elif doctor_status.status == "ON_LEAVE":
            return "Doctor is currently on leave."

    # -------------------------------
    # Date Conversion
    # -------------------------------
    try:
        booking_date = datetime.strptime(appointment_date, "%Y-%m-%d").date()
        booking_time = datetime.strptime(appointment_time, "%H:%M").time()
    except Exception:
        return "Invalid Date/Time.\nDate : YYYY-MM-DD\nTime : HH:MM"

   
    # -------------------------------
    # Past Date Check
    # -------------------------------

    if booking_date < date.today():

        return "Cannot book appointment in the past."

    # -------------------------------
    # Doctor Leave Check
    # -------------------------------

    if DoctorLeave.objects.filter(

        doctor=doctor,

        leave_date=booking_date

    ).exists():

        return (
            "Doctor is on leave on "
            f"{booking_date}."
        )

    # -------------------------------
    # Availability Check
    # -------------------------------

    weekday = booking_date.strftime("%A")

    slots = DoctorAvailability.objects.filter(

        doctor=doctor,

        day_of_week=weekday,

        is_available=True

    )

    if not slots.exists():

        return (

            f"Doctor is unavailable on "

            f"{weekday}."

        )

    inside_slot = False

    for slot in slots:

        if (

            slot.start_time

            <= booking_time

            <= slot.end_time

        ):

            inside_slot = True

            break

    if not inside_slot:

        return (

            "Selected time is outside "

            "doctor working hours."

        )

    # -------------------------------
    # Doctor Clash
    # -------------------------------

    doctor_busy = Appointment.objects.filter(

        doctor=doctor,

        appointment_date=booking_date,

        appointment_time=booking_time

    ).exclude(

        status="Cancelled"

    ).exists()

    if doctor_busy:

        return (

            "Doctor already has another "

            "appointment at this time."

        )

    # -------------------------------
    # Patient Clash
    # -------------------------------

    patient_busy = Appointment.objects.filter(

        patient=patient,

        appointment_date=booking_date,

        appointment_time=booking_time

    ).exclude(

        status="Cancelled"

    ).exists()

    if patient_busy:

        return (

            "Patient already has another "

            "appointment at this time."

        )

    # -------------------------------
    # Patient History
    # -------------------------------

    previous = Appointment.objects.filter(

        patient=patient

    )

    prior_visits = previous.count()

    prior_noshows = previous.filter(

        status="No Show"

    ).count()

    if prior_visits == 0:

        ratio = 0

    else:

        ratio = round(

            prior_noshows /

            prior_visits,

            2

        )

    # -------------------------------
    # Create Appointment
    # -------------------------------

    appointment = Appointment.objects.create(

        patient=patient,

        doctor=doctor,

        appointment_date=booking_date,

        appointment_time=booking_time,

        reason=reason,

        status="Pending",

        prior_visits=prior_visits,

        prior_noshows=prior_noshows,

        history_noshow_ratio=ratio,

        distance_from_clinic=float(

            patient.distance_from_clinic

        ),

    )

    # -------------------------------
    # Notification
    # -------------------------------

    try:

        send_appointment_confirmation(

            appointment

        )

    except Exception:

        pass

    doctor_name = (

        doctor.user.get_full_name()

        or

        doctor.user.username

    )

    return (
    f"✅ Appointment booked successfully.\n\n"
    f"Appointment ID : {appointment.id}\n"
    f"Doctor ID : {doctor.id}\n"
    f"Doctor : Dr. {doctor_name}\n"
    f"Department : {doctor.department.department_name}\n"
    f"Date : {booking_date}\n"
    f"Time : {booking_time.strftime('%I:%M %p')}\n"
    f"Status : Pending"
)
# =====================================================
# PREDICT NO SHOW RISK
# =====================================================

@tool
def predict_noshow_risk(appointment_id: int) -> str:
    """
    Predict no-show probability.

    Saves:

    - risk_score
    - risk_level

    back to Appointment.
    """

    if MODEL is None:

        return (
            "Prediction model is currently unavailable."
        )

    try:

        appointment = (

            Appointment.objects

            .select_related(

                "patient",

                "doctor",

                "doctor__department"

            )

            .get(

                id=appointment_id

            )

        )

    except Appointment.DoesNotExist:

        return (

            "Appointment not found."

        )

    patient = appointment.patient

    # -----------------------------------
    # AGE
    # -----------------------------------

    age = calculate_age(

        patient.date_of_birth

    )

    # -----------------------------------
    # WEEKDAY
    # -----------------------------------

    weekday = appointment.appointment_date.weekday()

    # -----------------------------------
    # FEATURES
    # -----------------------------------

    features = [[

        age,

        safe_encode(

            "gender",

            patient.gender

        ),

        safe_encode(

            "department",

            appointment.doctor.department.department_name

        ),

        appointment.lead_time_days,

        weekday,

        safe_encode(

            "appointment_time",

            appointment.time_bucket

        ),

        int(

            appointment.sms_reminder_sent

        ),

        appointment.prior_visits,

        appointment.prior_noshows,

        appointment.history_noshow_ratio,

        float(

            appointment.distance_from_clinic

        )

    ]]

    # -----------------------------------
    # MODEL
    # -----------------------------------

    probability = float(

        MODEL.predict_proba(

            features

        )[0][1]

    )

    risk_percent = round(

        probability * 100,

        2

    )

    # -----------------------------------
    # RISK LEVEL
    # -----------------------------------

    if probability >= OPERATING_THRESHOLD:
        level = "HIGH"
    elif probability >= 0.40:
        level = "MEDIUM"
    else:
        level = "LOW"

    # -----------------------------------
    # SAVE
    # -----------------------------------

    appointment.risk_score = round(

        probability,

        4

    )

    appointment.risk_level = level

    appointment.save(

        update_fields=[

            "risk_score",

            "risk_level"

        ]

    )

    # -----------------------------------
    # RESPONSE
    # -----------------------------------

    doctor_name = (

        appointment.doctor.user.get_full_name()

        or

        appointment.doctor.user.username

    )

    return f"""
AI Prediction Completed

Appointment ID : {appointment.id}

Doctor : Dr. {doctor_name}

Risk Score : {risk_percent}%

Risk Level : {level}

Recommendation :

{"Patient should receive reminder calls and SMS." if level=="HIGH" else ""}

{"Patient should receive SMS reminder." if level=="MEDIUM" else ""}

{"Appointment appears safe." if level=="LOW" else ""}
"""
# =====================================================
# BILLING INFORMATION
# =====================================================

@tool
def get_billing_info(appointment_id: int) -> str:
    """
    Returns complete billing details for
    an appointment.
    """

    try:

        bill = (

            Bill.objects

            .select_related(

                "appointment",

                "appointment__patient__user",

                "appointment__doctor__user"

            )

            .get(

                appointment_id=appointment_id

            )

        )

    except Bill.DoesNotExist:

        return (

            "Bill has not been generated "

            "for this appointment."

        )

    patient_name = (

        bill.appointment.patient.user.get_full_name()

        or

        bill.appointment.patient.user.username

    )

    doctor_name = (

        bill.appointment.doctor.user.get_full_name()

        or

        bill.appointment.doctor.user.username

    )

    return f"""
========== BILL DETAILS ==========

Bill ID

{bill.id}

Patient

{patient_name}

Doctor

Dr. {doctor_name}

--------------------------------

Consultation Fee

₹{bill.consultation_fee}

Medicine Cost

₹{bill.medicine_cost}

Lab Test Cost

₹{bill.lab_test_cost}

GST

₹{bill.gst}

Discount

₹{bill.discount}

--------------------------------

Total Amount

₹{bill.total_amount}

Amount Paid

₹{bill.total_paid}

Balance Due

₹{bill.balance_due}

Payment Status

{bill.payment_status}

================================
"""
# =====================================================
# DOCTOR SCHEDULE
# =====================================================

@tool
def get_my_schedule(doctor_id: int) -> str:
    """
    Returns doctor's appointments
    for next 7 days.
    """

    try:

        doctor = (

            Doctor.objects

            .select_related(

                "user"

            )

            .get(

                id=doctor_id

            )

        )

    except Doctor.DoesNotExist:

        return "Doctor not found."

    today = date.today()

    end_date = today + timedelta(days=7)

    appointments = (

        Appointment.objects

        .filter(

            doctor=doctor,

            appointment_date__gte=today,

            appointment_date__lte=end_date

        )

        .exclude(

            status="Cancelled"

        )

        .select_related(

            "patient__user"

        )

        .order_by(

            "appointment_date",

            "appointment_time"

        )

    )

    if not appointments.exists():

        return (

            "No appointments "

            "for next 7 days."

        )

    result = []

    result.append(

        "NEXT 7 DAYS SCHEDULE"

    )

    result.append("")

    for appt in appointments:

        patient_name = (

            appt.patient.user.get_full_name()

            or

            appt.patient.user.username

        )

        result.append(

            f"{appt.appointment_date}"

        )

        result.append(

            f"{appt.appointment_time.strftime('%I:%M %p')}"

        )

        result.append(

            f"Patient : {patient_name}"

        )

        result.append(

            f"Status : {appt.status}"

        )

        result.append(

            f"Risk : {appt.risk_level}"

        )

        result.append("")

    return "\n".join(result)
# =====================================================
# PATIENT PENDING BILLS
# =====================================================

@tool
def get_patient_pending_bills(patient_id: int) -> str:
    """
    Shows pending bills.
    """

    bills = (

        Bill.objects

        .filter(

            appointment__patient_id=patient_id

        )

        .exclude(

            payment_status="Paid"

        )

    )

    if not bills.exists():

        return "No pending bills."

    total = 0

    result = []

    result.append(

        "Pending Bills"

    )

    result.append("")

    for bill in bills:

        total += bill.balance_due

        result.append(

            f"Bill #{bill.id}"

        )

        result.append(

            f"Balance : ₹{bill.balance_due}"

        )

        result.append("")

    result.append(

        f"Total Due : ₹{total}"

    )

    return "\n".join(result)
# =====================================================
# CANCEL APPOINTMENT
# =====================================================

@tool
def cancel_appointment(appointment_id: int) -> str:
    """
    Cancel an appointment.
    """

    try:
        appointment = Appointment.objects.get(id=appointment_id)

    except Appointment.DoesNotExist:
        return "Appointment not found."

    if appointment.status == "Cancelled":
        return "Appointment is already cancelled."

    if appointment.status == "Completed":
        return "Completed appointments cannot be cancelled."

    appointment.status = "Cancelled"
    appointment.save(update_fields=["status"])

    return (
        f"Appointment #{appointment.id} "
        "has been cancelled successfully."
    )
# =====================================================
# RESCHEDULE APPOINTMENT
# =====================================================

@tool
def reschedule_appointment(
    appointment_id: int,
    new_date: str,
    new_time: str
) -> str:
    """
    Reschedule appointment.
    """

    try:

        appointment = Appointment.objects.get(
            id=appointment_id
        )

    except Appointment.DoesNotExist:

        return "Appointment not found."

    try:

        date_obj = datetime.strptime(
            new_date,
            "%Y-%m-%d"
        ).date()

        time_obj = datetime.strptime(
            new_time,
            "%H:%M"
        ).time()

    except Exception:

        return "Invalid date/time."

    appointment.appointment_date = date_obj
    appointment.appointment_time = time_obj
    appointment.status = "Pending"

    appointment.save()

    return (
        f"Appointment #{appointment.id} "
        f"rescheduled to "
        f"{new_date} "
        f"{new_time}"
    )
# =====================================================
# APPOINTMENT HISTORY
# =====================================================

@tool
def appointment_history(patient_id: int) -> str:
    """
    Returns appointment history.
    """

    appointments = (

        Appointment.objects

        .filter(

            patient_id=patient_id

        )

        .select_related(

            "doctor__user"

        )

        .order_by(

            "-appointment_date"

        )

    )

    if not appointments.exists():

        return "No appointment history."

    result = []

    for appointment in appointments:

        doctor = (

            appointment.doctor.user.get_full_name()

            or

            appointment.doctor.user.username

        )

        result.append(

            f"{appointment.appointment_date}"

        )

        result.append(

            f"Dr. {doctor}"

        )

        result.append(

            f"{appointment.status}"

        )

        result.append("")

    return "\n".join(result)
# =====================================================
# PATIENT SUMMARY
# =====================================================

@tool
def patient_summary(patient_id: int) -> str:
    """
    Returns patient summary.
    """

    try:

        patient = Patient.objects.select_related(
            "user"
        ).get(
            id=patient_id
        )

    except Patient.DoesNotExist:

        return "Patient not found."

    total = Appointment.objects.filter(
        patient=patient
    ).count()

    completed = Appointment.objects.filter(
        patient=patient,
        status="Completed"
    ).count()

    pending = Appointment.objects.filter(
        patient=patient,
        status="Pending"
    ).count()

    return f"""
Patient

{patient.user.get_full_name()}

Total Appointments : {total}

Completed : {completed}

Pending : {pending}

Distance : {patient.distance_from_clinic} km
"""
# =====================================================
# DOCTOR SUMMARY
# =====================================================

@tool
def doctor_summary(doctor_id: int) -> str:
    """
    Doctor statistics.
    """

    try:

        doctor = Doctor.objects.select_related(
            "user",
            "department"
        ).get(
            id=doctor_id
        )

    except Doctor.DoesNotExist:

        return "Doctor not found."

    total = Appointment.objects.filter(
        doctor=doctor
    ).count()

    today = Appointment.objects.filter(
        doctor=doctor,
        appointment_date=date.today()
    ).count()

    return f"""
Doctor

Dr. {doctor.user.get_full_name()}

Department

{doctor.department.department_name}

Appointments

{total}

Today's Appointments

{today}
"""
# =====================================================
# HOSPITAL STATISTICS
# =====================================================

@tool
def hospital_statistics(dummy: str = "") -> str:
    """
    Hospital dashboard summary.
    """

    doctors = Doctor.objects.filter(
        is_active=True
    ).count()

    patients = Patient.objects.count()

    appointments = Appointment.objects.count()

    bills = Bill.objects.count()

    return f"""
Hospital Statistics

Doctors : {doctors}

Patients : {patients}

Appointments : {appointments}

Bills : {bills}
"""
@tool
def suggest_alternate_doctors(doctor_id: int) -> str:
    """
    Suggest alternative available doctors
    from the same department when the
    requested doctor is unavailable,
    busy, on leave, or attending an emergency.
    """

    try:
        doctor = Doctor.objects.select_related(
            "department"
        ).get(id=doctor_id)

    except Doctor.DoesNotExist:
        return "Doctor not found."

    doctors = (
        Doctor.objects.filter(
            department=doctor.department,
            is_active=True
        )
        .exclude(id=doctor.id)
        .select_related("user")
    )

    response = []

    for d in doctors:

        status = getattr(
            d,
            "current_status",
            None
        )

        if status and status.status != "AVAILABLE":
            continue
        

        response.append(
            f"""
Doctor ID : {d.id}

Doctor : Dr. {d.user.get_full_name()}

Department : {d.department.department_name}

Specialization : {d.specialization}

Fee : ₹{d.consultation_fee}
"""
        )

    if not response:
        return "No alternate doctors are currently available."

    return (
    "Requested doctor unavailable.\n\n"
    "Available alternatives:\n\n"
    + "\n".join(response)
)
# =====================================================
# SYMPTOM TO DEPARTMENT
# =====================================================

SYMPTOM_MAP = {
    "fever": "General Medicine",
    "cold": "General Medicine",
    "cough": "General Medicine",
    "body pain": "General Medicine",
    "weakness": "General Medicine",

    "chest pain": "Cardiology",
    "heart pain": "Cardiology",
    "palpitations": "Cardiology",
    "high bp": "Cardiology",

    "skin rash": "Dermatology",
    "allergy": "Dermatology",
    "acne": "Dermatology",

    "headache": "Neurology",
    "dizziness": "Neurology",
    "numbness": "Neurology",

    "joint pain": "Orthopedics",
    "fracture": "Orthopedics",
    "back pain": "Orthopedics",
}


@tool
def symptom_to_department(symptom: str) -> str:
    """
    Maps symptoms to department.
    """

    symptom = symptom.lower()

    for key, dept in SYMPTOM_MAP.items():

        if key in symptom:

            return dept

    return "General Medicine"
from medical_records.models import MedicalRecord

@tool
def view_medical_records(patient_id: int) -> str:
    """
    View patient's medical records.
    """

    records = (
        MedicalRecord.objects
        .filter(appointment__patient_id=patient_id)
        .select_related("appointment__doctor__user")
        .order_by("-created_at")
    )

    if not records.exists():
        return "No medical records found."

    result = []

    for record in records:

        doctor = (
            record.appointment.doctor.user.get_full_name()
            or record.appointment.doctor.user.username
        )

        result.append(
            f"""
Date : {record.created_at.date()}

Doctor : Dr. {doctor}

Symptoms : {record.symptoms}

Diagnosis : {record.diagnosis}
"""
        )

    return "\n".join(result)
from prescriptions.models import Prescription
from medical_records.models import MedicalRecord

@tool
def create_prescription(
    appointment_id: int,
    medicine_name: str,
    dosage: str,
    frequency: str,
    duration: int,
    before_after_food: str,
) -> str:
    """
    Create prescription for a patient.
    """

    try:
        record = MedicalRecord.objects.get(
            appointment_id=appointment_id
        )

    except MedicalRecord.DoesNotExist:
        return "Medical record not found."

    Prescription.objects.create(
        medical_record=record,
        medicine_name=medicine_name,
        dosage=dosage,
        frequency=frequency,
        duration=duration,
        before_after_food=before_after_food,
    )

    return "Prescription created successfully."


@tool
def doctor_full_details(name: str) -> str:
    """
    Search a doctor by name and return their full details including
    department, specialization, consultation fee, and weekly availability.
    """

    doctor = (
        Doctor.objects
        .filter(
            Q(user__first_name__icontains=name)
            | Q(user__last_name__icontains=name)
        )
        .select_related("user", "department")
        .first()
    )

    if not doctor:
        return "Doctor not found."

    slots = DoctorAvailability.objects.filter(
        doctor=doctor,
        is_available=True
    )

    text = f"""
Doctor Name : Dr. {doctor.user.get_full_name()}

Department : {doctor.department.department_name}

Specialization : {doctor.specialization}

Consultation Fee : ₹{doctor.consultation_fee}

Availability

"""

    for slot in slots:
        text += (
            f"{slot.day_of_week}\n"
            f"{slot.start_time.strftime('%I:%M %p')} - "
            f"{slot.end_time.strftime('%I:%M %p')}\n\n"
        )

    return text
