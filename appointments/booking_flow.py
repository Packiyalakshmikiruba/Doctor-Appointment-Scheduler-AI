"""
appointments/booking_flow.py

Reminder functions (Email only)
"""

from .notifications import send_email_notification


def send_one_day_reminder(appointment):
    patient = appointment.patient

    subject = "Appointment Reminder (Tomorrow)"

    message = (
        f"Dear {patient.user.get_full_name()},\n\n"
        f"This is a reminder that you have an appointment tomorrow.\n\n"
        f"Doctor: Dr. {appointment.doctor.user.get_full_name()}\n"
        f"Date: {appointment.appointment_date}\n"
        f"Time: {appointment.appointment_time}\n\n"
        f"Please arrive 15 minutes early.\n\n"
        f"Thank you."
    )

    send_email_notification(
        patient.user.email,
        subject,
        message
    )

    appointment.status = "Confirmed"
    appointment.save(update_fields=["status"])


def send_two_hour_reminder(appointment):
    patient = appointment.patient

    subject = "Appointment Reminder (2 Hours Left)"

    message = (
        f"Dear {patient.user.get_full_name()},\n\n"
        f"Your appointment is in 2 hours.\n\n"
        f"Doctor: Dr. {appointment.doctor.user.get_full_name()}\n"
        f"Time: {appointment.appointment_time}\n\n"
        f"Please arrive 15 minutes early.\n\n"
        f"Thank you."
    )

    send_email_notification(
        patient.user.email,
        subject,
        message
    )