from dataclasses import dataclass
from datetime import datetime, date, timedelta

from appointments.models import Appointment
from hospital.models import (
    Doctor,
    DoctorAvailability,
    DoctorLeave,
)
from patients.models import Patient

@dataclass
class BookingResponse:
    success: bool
    message: str
    appointment: Appointment | None = None

class BookingService:
    @staticmethod
    def validate_patient(patient_id):
        try:
            return Patient.objects.select_related("user").get(id=patient_id)
        except Patient.DoesNotExist:
            return None

    @staticmethod
    def validate_doctor(doctor_id):
        try:
            return Doctor.objects.select_related("user", "department").get(
                id=doctor_id, is_active=True
            )
        except Doctor.DoesNotExist:
            return None

    @staticmethod
    def validate_datetime(appointment_date, appointment_time):
        try:
            booking_date = datetime.strptime(appointment_date, "%Y-%m-%d").date()
            booking_time = datetime.strptime(appointment_time, "%H:%M").time()
            return booking_date, booking_time
        except:
            return None, None

    @staticmethod
    def validate_future_date(booking_date):
        return booking_date >= date.today()

    @staticmethod
    def check_leave(doctor, booking_date):
        return DoctorLeave.objects.filter(doctor=doctor, leave_date=booking_date).exists()

    @staticmethod
    def get_schedule(doctor, booking_date):
        weekday = booking_date.strftime("%A")
        return DoctorAvailability.objects.filter(
            doctor=doctor, day_of_week=weekday, is_available=True
        )

    @staticmethod
    def validate_doctor_status(doctor):
        status = getattr(doctor, "current_status", None)
        if status is None:
            return True, ""
        if status.status == "AVAILABLE":
            return True, ""
        if status.status == "BUSY":
            return False, "Doctor is currently busy."
        if status.status == "ON_LEAVE":
            return False, "Doctor is currently on leave."
        if status.status == "EMERGENCY":
            return False, "Doctor is attending an emergency."
        if status.status == "NOT_AVAILABLE":
            return False, "Doctor is unavailable."
        return True, ""

    @staticmethod
    def validate_time_slot(schedules, booking_time):
        for slot in schedules:
            if slot.start_time <= booking_time <= slot.end_time:
                return True
        return False

    @staticmethod
    def doctor_busy(doctor, booking_date, booking_time):
        return Appointment.objects.filter(
            doctor=doctor, appointment_date=booking_date, appointment_time=booking_time
        ).exclude(status="Cancelled").exists()

    @staticmethod
    def patient_busy(patient, booking_date, booking_time):
        return Appointment.objects.filter(
            patient=patient, appointment_date=booking_date, appointment_time=booking_time
        ).exclude(status="Cancelled").exists()

    @staticmethod
    def patient_history(patient):
        qs = Appointment.objects.filter(patient=patient)
        visits = qs.count()
        noshows = qs.filter(status="No Show").count()
        ratio = 0
        if visits:
            ratio = round(noshows / visits, 2)
        return visits, noshows, ratio

    @staticmethod
    def book(
        *,
        patient_id: int,
        doctor_id: int,
        appointment_date: str,
        appointment_time: str,
        reason: str,
    ) -> BookingResponse:
        
        # 1. Validation
        patient = BookingService.validate_patient(patient_id)
        if patient is None:
            return BookingResponse(False, "Patient not found.")

        doctor = BookingService.validate_doctor(doctor_id)
        if doctor is None:
            return BookingResponse(False, "Doctor not found.")

        ok, message = BookingService.validate_doctor_status(doctor)
        if not ok:
            return BookingResponse(False, message)

        booking_date, booking_time = BookingService.validate_datetime(appointment_date, appointment_time)
        if booking_date is None:
            return BookingResponse(False, "Invalid date or time.")

        if not BookingService.validate_future_date(booking_date):
            return BookingResponse(False, "Cannot book past date.")

        if BookingService.check_leave(doctor, booking_date):
            return BookingResponse(False, "Doctor is on leave.")

        schedules = BookingService.get_schedule(doctor, booking_date)
        if not schedules.exists():
            return BookingResponse(False, "Doctor unavailable on selected day.")

        if not BookingService.validate_time_slot(schedules, booking_time):
            return BookingResponse(False, "Outside working hours.")

        if BookingService.doctor_busy(doctor, booking_date, booking_time):
            return BookingResponse(False, "Doctor already has appointment.")

        if BookingService.patient_busy(patient, booking_date, booking_time):
            return BookingResponse(False, "Patient already has another appointment.")

        visits, noshows, ratio = BookingService.patient_history(patient)

        # 2. Booking Creation
        appointment = Appointment.objects.create(
            patient=patient,
            doctor=doctor,
            appointment_date=booking_date,
            appointment_time=booking_time,
            reason=reason,
            status="Pending",
            prior_visits=visits,
            prior_noshows=noshows,
            history_noshow_ratio=ratio,
            distance_from_clinic=float(patient.distance_from_clinic),
        )

        # 3. Side effects (Notifications & Risk Prediction)
        try:
            from appointments.notifications import send_appointment_confirmation
            send_appointment_confirmation(appointment)
        except Exception:
            pass

        try:
            from chatbot.tools import predict_noshow_risk
            predict_noshow_risk.invoke({"appointment_id": appointment.id})
        except Exception:
            pass

        doctor_name = doctor.user.get_full_name() or doctor.user.username
        return BookingResponse(
            success=True,
            message=(
                f"Appointment booked successfully.\n\n"
                f"Appointment ID : {appointment.id}\n"
                f"Doctor : Dr. {doctor_name}\n"
                f"Department : {doctor.department.department_name}\n"
                f"Date : {booking_date}\n"
                f"Time : {booking_time.strftime('%I:%M %p')}\n"
                f"Status : Pending"
            ),
            appointment=appointment,
        )
    @staticmethod
    def find_doctor_by_name(name):
        return (
            Doctor.objects.select_related("user", "department")
            .filter(user__first_name__icontains=name, is_active=True)
            .first()
        )

    @staticmethod
    def find_department_doctors(department):
        return Doctor.objects.select_related(
            "user",
            "department"
        ).filter(
            department__department_name__icontains=department,
            is_active=True
        )
