"""
appointments/booking_service.py
Single source of truth for booking. Called from appointment_create view
AND the LangChain book_appointment tool.

Also provides handle_cancellation(), meant to be called from your
existing mark_cancelled view (appointments/urls.py already has this URL).
"""

from .models import Appointment
from .utils import is_doctor_available
from .risk import predict_and_save_risk
from .notifications import send_appointment_confirmation, send_sms_confirmation


class BookingError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(message)


def book_appointment_full(patient, doctor, appointment_date, appointment_time, reason):
    # Step 1 — Check Availability
    available, reason_msg = is_doctor_available(doctor, appointment_date, appointment_time)
    if not available:
        raise BookingError(reason_msg)

    # Step 2 — Check Existing Appointment (no duplicate booking same day/doctor)
    duplicate = Appointment.objects.filter(
        patient=patient, doctor=doctor, appointment_date=appointment_date,
    ).exclude(status="Cancelled").exists()
    if duplicate:
        raise BookingError("You already have an appointment with this doctor on this date.")

    past_appts = Appointment.objects.filter(patient=patient)
    prior_visits = past_appts.filter(status="Completed").count() + past_appts.filter(status="No Show").count()
    prior_noshows = past_appts.filter(status="No Show").count()
    history_noshow_ratio = round(prior_noshows / prior_visits, 3) if prior_visits > 0 else 0.0

    appointment = Appointment.objects.create(
        patient=patient, doctor=doctor,
        appointment_date=appointment_date, appointment_time=appointment_time,
        reason=reason, status="Pending",
        prior_visits=prior_visits, prior_noshows=prior_noshows,
        history_noshow_ratio=history_noshow_ratio,
        distance_from_clinic=float(patient.distance_from_clinic),
    )

    # Step 3 — Predict No Show
    risk_level = predict_and_save_risk(appointment)

    # Step 4 — Auto Confirm
    appointment.status = "Confirmed"
    appointment.save(update_fields=["status"])

    # Step 5 — Email + Step 6 — SMS
    send_appointment_confirmation(appointment)
    sms_sent = send_sms_confirmation(appointment)
    if sms_sent:
        appointment.sms_reminder_sent = True
        appointment.save(update_fields=["sms_reminder_sent"])

    # Step 7 — Dashboard Updated: automatic, dashboards query Appointment live.
    return appointment


def handle_cancellation(appointment):
    """
    Call this from your existing mark_cancelled view, AFTER setting
    appointment.status = "Cancelled" and saving it:

        appt.status = "Cancelled"
        appt.save()
        handle_cancellation(appt)   # <-- add this line

    Offers the freed slot to the earliest waitlisted patient for this doctor.
    Requires the Waitlist model (see models_waitlist.py) merged into models.py.
    """
    from .models import Waitlist  # local import: only needed if Waitlist exists

    entry = Waitlist.objects.filter(doctor=appointment.doctor, notified=False).order_by("created_at").first()
    if not entry:
        return None

    patient = entry.patient
    doctor_name = appointment.doctor.user.get_full_name() or appointment.doctor.user.username
    message = (
        f"Good news! A slot with Dr. {doctor_name} on "
        f"{appointment.appointment_date} at {appointment.appointment_time} just opened up. "
        f"Book now before it's taken."
    )

    # Simple simulated notifications (waitlist offer isn't an "appointment
    # confirmation", so it doesn't reuse send_appointment_confirmation).
    if patient.phone_number:
        print(f"[SMS SIMULATED] To {patient.phone_number}: {message}")
    patient_email = getattr(patient.user, "email", None)
    if patient_email:
        try:
            from django.core.mail import send_mail
            from django.conf import settings
            send_mail("A slot just opened up!", message, settings.DEFAULT_FROM_EMAIL, [patient_email])
        except Exception as exc:  # noqa: BLE001
            print(f"[EMAIL FAILED] {exc}")

    entry.notified = True
    entry.save(update_fields=["notified"])
    return entry
