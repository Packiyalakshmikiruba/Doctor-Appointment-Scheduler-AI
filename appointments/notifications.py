"""
notifications.py
-----------------
Sends real appointment confirmation via Email (Gmail SMTP).
Fails gracefully -- if credentials aren't configured, logs to console
instead of crashing the booking flow.
"""

from django.core.mail import send_mail
from django.conf import settings


def send_email_confirmation(appointment):
    patient_email = appointment.patient.user.email

    if not patient_email:
        print(f"[EMAIL SKIPPED] No email on file for {appointment.patient}")
        return False

    if not settings.EMAIL_HOST_USER:
        print(f"[EMAIL SIMULATED] To: {patient_email} -- Appointment with "
              f"Dr. {appointment.doctor.user.get_full_name()} on "
              f"{appointment.appointment_date} at {appointment.appointment_time}")
        return False

    doctor_name = appointment.doctor.user.get_full_name() or appointment.doctor.user.username

    subject = "Appointment Confirmation - AI Doctor Scheduler"
    message = (
        f"Dear {appointment.patient},\n\n"
        f"Your appointment has been booked successfully.\n\n"
        f"Doctor: Dr. {doctor_name}\n"
        f"Department: {appointment.doctor.department.department_name}\n"
        f"Date: {appointment.appointment_date}\n"
        f"Time: {appointment.appointment_time}\n"
        f"Reason: {appointment.reason}\n"
        f"Status: {appointment.status}\n\n"
        f"Please arrive 15 minutes early.\n\n"
        f"Thank you,\nAI Doctor Appointment Scheduler"
    )

    try:
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [patient_email])
        print(f"[EMAIL SENT] To: {patient_email}")
        return True
    except Exception as e:
        print(f"[EMAIL FAILED] {e}")
        return False


def send_appointment_confirmation(appointment):
    """Call this after any appointment is created."""
    send_email_confirmation(appointment)


def send_sms_confirmation(appointment):
    phone = appointment.patient.phone_number

    if not phone:
        print(f"[SMS SKIPPED] No phone number on file for {appointment.patient}")
        return False

    doctor_name = appointment.doctor.user.get_full_name() or appointment.doctor.user.username
    message = (
        f"Your appointment with Dr. {doctor_name} on "
        f"{appointment.appointment_date} at {appointment.appointment_time} is confirmed."
    )
    # --- Simulated SMS (replace with real gateway call later) ---
    print(f"[SMS SIMULATED] To {phone}: {message}")
    return True