from dataclasses import dataclass


@dataclass
class BookingMemory:

    patient_id: int | None = None

    doctor_id: int | None = None

    doctor_name: str | None = None

    department: str | None = None

    appointment_date: str | None = None

    appointment_time: str | None = None

    reason: str | None = None


BOOKING_MEMORY = {}


def get_booking(session):

    if session not in BOOKING_MEMORY:

        BOOKING_MEMORY[session] = BookingMemory()

    return BOOKING_MEMORY[session]


def clear_booking(session):

    BOOKING_MEMORY.pop(session, None)