from django.core.management.base import BaseCommand
from hospital.models import Doctor, DoctorAvailability
from datetime import time


class Command(BaseCommand):
    help = "Fills missing Monday-Saturday availability (9AM-5PM) for all doctors"

    def handle(self, *args, **kwargs):
        DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]

        for doc in Doctor.objects.all():
            existing_days = set(
                DoctorAvailability.objects.filter(doctor=doc, is_available=True)
                .values_list("day_of_week", flat=True)
            )
            missing_days = set(DAYS) - existing_days

            for day in missing_days:
                DoctorAvailability.objects.create(
                    doctor=doc,
                    day_of_week=day,
                    start_time=time(9, 0),
                    end_time=time(17, 0),
                    is_available=True,
                )

            if missing_days:
                self.stdout.write(self.style.SUCCESS(f"{doc}: added {sorted(missing_days)}"))
            else:
                self.stdout.write(f"{doc}: already had full availability")

        self.stdout.write(self.style.SUCCESS("Done."))