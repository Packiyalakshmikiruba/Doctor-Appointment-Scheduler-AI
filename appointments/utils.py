"""
appointments/utils.py
Doctor Availability Check — used when booking an appointment,
so patients can't book outside a doctor's working hours or
double-book an already-taken slot.
"""

from hospital.models import DoctorAvailability
from appointments.models import Appointment


def is_doctor_available(doctor, appointment_date, appointment_time):
    """
    Returns (True, "") if the doctor can be booked at this date/time,
    or (False, "<reason>") if not.
    """
    weekday_name = appointment_date.strftime("%A")  # "Monday", "Tuesday", ...

    slot = DoctorAvailability.objects.filter(
        doctor=doctor,
        day_of_week=weekday_name,
        is_available=True,
        start_time__lte=appointment_time,
        end_time__gte=appointment_time,
    ).first()

    if not slot:
        return False, f"Dr. {doctor} is not available on {weekday_name} at {appointment_time}."

    clash = Appointment.objects.filter(
        doctor=doctor,
        appointment_date=appointment_date,
        appointment_time=appointment_time,
    ).exclude(status="Cancelled").exists()

    if clash:
        return False, "This time slot is already booked. Please choose a different time."

    return True, ""
