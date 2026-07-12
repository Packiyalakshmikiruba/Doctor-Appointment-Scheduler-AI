from django.contrib import admin
from .models import Department, Doctor, DoctorAvailability


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = (
        "department_name",
        "room_number",
    )

    search_fields = (
        "department_name",
    )


@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "department",
        "specialization",
        "consultation_fee",
        "is_active",
    )

    list_filter = (
        "department",
        "is_active",
    )

    search_fields = (
        "user__first_name",
        "user__last_name",
        "license_number",
    )


@admin.register(DoctorAvailability)
class DoctorAvailabilityAdmin(admin.ModelAdmin):
    list_display = (
        "doctor",
        "day_of_week",
        "start_time",
        "end_time",
        "is_available",
    )

    list_filter = (
        "day_of_week",
        "is_available",
    )