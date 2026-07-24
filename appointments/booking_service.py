"""
appointments/booking_service.py

Single source of truth for booking.
"""

from django.db import transaction
from django.conf import settings
from django.core.mail import send_mail

from notifications.models import Notification

from .models import Appointment, Waitlist
from .utils import is_doctor_available
from .risk import predict_and_save_risk
from .notifications import send_appointment_confirmation


class BookingError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(message)


@transaction.atomic
def book_appointment_full(
    patient,
    doctor,
    appointment_date,
    appointment_time,
    reason,
):
    """
    Complete Appointment Booking Flow
    """

    # ----------------------------------------
    # Doctor Availability
    # ----------------------------------------
    available, reason_msg = is_doctor_available(
        doctor,
        appointment_date,
        appointment_time,
    )

    if not available:
        raise BookingError(reason_msg)

    # ----------------------------------------
    # Duplicate Appointment Check
    # ----------------------------------------
    duplicate = Appointment.objects.filter(
        patient=patient,
        doctor=doctor,
        appointment_date=appointment_date,
    ).exclude(
        status="Cancelled"
    ).exists()

    if duplicate:
        raise BookingError(
            "You already booked this doctor on the selected date."
        )

    # ----------------------------------------
    # Patient History
    # ----------------------------------------
    previous = Appointment.objects.filter(
        patient=patient
    )

    completed = previous.filter(
        status="Completed"
    ).count()

    no_show = previous.filter(
        status="No Show"
    ).count()

    prior_visits = completed + no_show

    history_ratio = (
        round(no_show / prior_visits, 3)
        if prior_visits
        else 0
    )

    # ----------------------------------------
    # Create Appointment
    # ----------------------------------------
    appointment = Appointment.objects.create(
        patient=patient,
        doctor=doctor,
        appointment_date=appointment_date,
        appointment_time=appointment_time,
        reason=reason,
        status="Confirmed",
        prior_visits=prior_visits,
        prior_noshows=no_show,
        history_noshow_ratio=history_ratio,
        distance_from_clinic=float(patient.distance_from_clinic),
        sms_reminder_sent=False,
    )

    # ----------------------------------------
    # AI Risk Prediction
    # ----------------------------------------
    try:
        predict_and_save_risk(appointment)
    except Exception as e:
        print("AI Prediction Error:", e)

    # ----------------------------------------
    # Email Confirmation
    # ----------------------------------------
    try:
        send_appointment_confirmation(appointment)
    except Exception as e:
        print("Email Error:", e)

    # ----------------------------------------
    # Website Notification
    # ----------------------------------------
    try:
        Notification.objects.create(
            user=appointment.patient.user,
            title="Appointment Confirmed",
            message=(
                f"Your appointment with "
                f"Dr. {appointment.doctor.user.get_full_name()} "
                f"has been confirmed for "
                f"{appointment.appointment_date} "
                f"at {appointment.appointment_time}."
            ),
        )
    except Exception as e:
        print("Notification Error:", e)

    return appointment


def handle_cancellation(appointment):
    """
    Offer cancelled slot to earliest waitlist patient.
    """

    entry = (
        Waitlist.objects.filter(
            doctor=appointment.doctor,
            notified=False
        )
        .order_by("created_at")
        .first()
    )

    if not entry:
        return None

    patient = entry.patient

    doctor_name = (
        appointment.doctor.user.get_full_name()
        or appointment.doctor.user.username
    )

    subject = "Appointment Slot Available"

    message = f"""
Dear {patient.user.get_full_name()},

A slot has become available.

Doctor:
Dr. {doctor_name}

Date:
{appointment.appointment_date}

Time:
{appointment.appointment_time}

Please login immediately to book this slot.

Thank you,
Hospital Management System
"""

    # Email
    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [patient.user.email],
            fail_silently=False,
        )
    except Exception as e:
        print("Waitlist Email Error:", e)

    # Website Notification
    try:
        Notification.objects.create(
            user=patient.user,
            title="Appointment Slot Available",
            message=(
                f"A slot with Dr. {doctor_name} "
                f"is available on "
                f"{appointment.appointment_date} "
                f"at {appointment.appointment_time}."
            ),
        )
    except Exception as e:
        print("Notification Error:", e)

    entry.notified = True
    entry.save(update_fields=["notified"])

    return entry