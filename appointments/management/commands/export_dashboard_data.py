"""
appointments/management/commands/export_dashboard_data.py

Exports appointment + risk data to CSV, ready to import into Power BI
or Tableau for the analytics dashboard.

Run:
    python manage.py export_dashboard_data

Output: exports/appointments_export_<date>.csv in the project root.
"""

import csv
import os
from datetime import datetime

from django.conf import settings
from django.core.management.base import BaseCommand

from appointments.models import Appointment


class Command(BaseCommand):
    help = "Export appointment data (with risk scores) to CSV for Power BI/Tableau"

    def handle(self, *args, **kwargs):
        export_dir = os.path.join(settings.BASE_DIR, "exports")
        os.makedirs(export_dir, exist_ok=True)

        filename = f"appointments_export_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
        filepath = os.path.join(export_dir, filename)

        appointments = Appointment.objects.select_related(
            "patient__user", "doctor__user", "doctor__department"
        ).all()

        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "appointment_id",
                "patient_name",
                "patient_age",
                "patient_gender",
                "doctor_name",
                "department",
                "appointment_date",
                "appointment_weekday",
                "appointment_time",
                "lead_time_days",
                "sms_reminder_sent",
                "prior_visits",
                "prior_noshows",
                "history_noshow_ratio",
                "distance_from_clinic",
                "status",
                "risk_score",
                "risk_level",
            ])

            for a in appointments:
                writer.writerow([
                    a.id,
                    str(a.patient),
                    getattr(a.patient, "age", ""),
                    a.patient.gender,
                    str(a.doctor),
                    a.doctor.department.department_name,
                    a.appointment_date,
                    a.appointment_weekday,
                    a.appointment_time,
                    a.lead_time_days,
                    int(a.sms_reminder_sent),
                    a.prior_visits,
                    a.prior_noshows,
                    a.history_noshow_ratio,
                    a.distance_from_clinic,
                    a.status,
                    a.risk_score if a.risk_score is not None else "",
                    a.risk_level,
                ])

        self.stdout.write(self.style.SUCCESS(f"Exported {appointments.count()} appointments -> {filepath}"))
