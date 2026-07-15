"""
appointments/booking_flow.py

NOTE: booking + cancellation logic now lives in booking_service.py
(book_appointment_full, handle_cancellation) to avoid duplicate logic.
This file only keeps the two reminder functions, used by the
send_day_before_reminders / send_two_hour_reminders management commands.
"""

from .notifications import send_email_notification, send_sms_notification


def send_one_day_reminder(appointment):
    patient = appointment.patient
    message = (
        f"Reminder: You have an appointment with Dr. {appointment.doctor} tomorrow, "
        f"{appointment.appointment_date} at {appointment.appointment_time}."
    )
    send_sms_notification(patient.phone_number, message)
    send_email_notification(getattr(patient.user, "email", None), "Appointment Reminder (Tomorrow)", message)
    appointment.sms_reminder_sent = True
    appointment.status = "Confirmed"
    appointment.save(update_fields=["sms_reminder_sent", "status"])


def send_two_hour_reminder(appointment):
    patient = appointment.patient
    message = (
        f"Reminder: Your appointment with Dr. {appointment.doctor} is in 2 hours, "
        f"at {appointment.appointment_time} today. Please arrive 15 minutes early."
    )
    send_sms_notification(patient.phone_number, message)
