"""
notifications.py
-----------------
Appointment confirmation via Email only.
"""

from django.core.mail import send_mail
from django.conf import settings


def send_email_confirmation(appointment):

    patient_email = appointment.patient.user.email

    if not patient_email:
        print(f"[EMAIL SKIPPED] No email for {appointment.patient}")
        return False

    doctor_name = (
        appointment.doctor.user.get_full_name()
        or appointment.doctor.user.username
    )

    subject = "Appointment Confirmation - AI Doctor Scheduler"

    message = f"""
Dear {appointment.patient.user.get_full_name()},

Your appointment has been booked successfully.

Doctor :
Dr. {doctor_name}

Department :
{appointment.doctor.department.department_name}

Date :
{appointment.appointment_date}

Time :
{appointment.appointment_time}

Reason :
{appointment.reason}

Status :
{appointment.status}

Please arrive 15 minutes before your appointment.

Thank you,
AI Doctor Appointment Scheduler
"""

    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [patient_email],
            fail_silently=False,
        )

        print(f"[EMAIL SENT] {patient_email}")
        return True

    except Exception as e:
        print(f"[EMAIL FAILED] {e}")
        return False


def send_appointment_confirmation(appointment):
    return send_email_confirmation(appointment)