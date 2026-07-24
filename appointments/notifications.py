from django.core.mail import send_mail
from django.conf import settings


def send_email_notification(email, subject, message):
    if not email:
        return False

    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [email],
            fail_silently=False,
        )
        return True
    except Exception as e:
        print("Email Error:", e)
        return False


def send_appointment_confirmation(appointment):
    patient_email = appointment.patient.user.email

    if not patient_email:
        return False

    doctor_name = (
        appointment.doctor.user.get_full_name()
        or appointment.doctor.user.username
    )

    subject = "Appointment Confirmation - AI Doctor Scheduler"

    message = f"""
Dear {appointment.patient.user.get_full_name()},

Your appointment has been booked successfully.

Doctor: Dr. {doctor_name}
Department: {appointment.doctor.department.department_name}

Date: {appointment.appointment_date}
Time: {appointment.appointment_time}

Reason: {appointment.reason}

Status: {appointment.status}

Please arrive 15 minutes early.

Thank you,
AI Doctor Appointment Scheduler
"""

    return send_email_notification(
        patient_email,
        subject,
        message,
    )