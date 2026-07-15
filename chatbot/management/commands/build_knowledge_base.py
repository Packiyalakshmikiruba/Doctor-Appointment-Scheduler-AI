"""
chatbot/management/commands/build_knowledge_base.py

Extracts hospital data (departments, doctors, availability) from the DB
into plain text documents, ready for RAG embedding.

Run:
    python manage.py build_knowledge_base
"""

import os
from django.conf import settings
from django.core.management.base import BaseCommand

from hospital.models import Doctor, DoctorAvailability, Department


class Command(BaseCommand):
    help = "Build hospital_knowledge.txt from current DB data for the RAG pipeline"

    def handle(self, *args, **kwargs):
        documents = []

        for dept in Department.objects.all():
            documents.append(
                f"Department: {dept.department_name}. Room: {dept.room_number}. "
                f"Description: {dept.description or 'General consultations available.'}"
            )

        for doctor in Doctor.objects.filter(is_active=True).select_related("user", "department"):
            name = doctor.user.get_full_name() or doctor.user.username
            slots = DoctorAvailability.objects.filter(doctor=doctor, is_available=True)
            slot_text = ", ".join(
                f"{s.day_of_week} {s.start_time.strftime('%I:%M %p')}-{s.end_time.strftime('%I:%M %p')}"
                for s in slots
            ) or "No slots currently listed."

            documents.append(
                f"Doctor: Dr. {name}. Specialization: {doctor.specialization}. "
                f"Department: {doctor.department.department_name}. "
                f"Consultation Fee: Rs.{doctor.consultation_fee}. "
                f"Available: {slot_text}."
            )

        # General clinic FAQ / policy text — edit this to match your actual clinic.
        documents.append(
            "Clinic General Info: OPD hours are Monday to Saturday, 9 AM to 6 PM. "
            "Patients are advised to arrive 15 minutes before their appointment. "
            "SMS reminders are sent 24 hours before scheduled appointments."
        )
        documents.append(
            "Cancellation Policy: Appointments can be cancelled or rescheduled up to "
            "2 hours before the scheduled time through the patient dashboard."
        )

        data_dir = os.path.join(settings.BASE_DIR, "chatbot", "data")
        os.makedirs(data_dir, exist_ok=True)
        out_path = os.path.join(data_dir, "hospital_knowledge.txt")

        with open(out_path, "w", encoding="utf-8") as f:
            f.write("\n\n".join(documents))

        self.stdout.write(
            self.style.SUCCESS(f"Wrote {len(documents)} documents -> {out_path}")
        )
