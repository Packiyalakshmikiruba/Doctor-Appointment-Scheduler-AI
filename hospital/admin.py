from django.contrib import admin
from .models import Department, Doctor, DoctorAvailability


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "department_name",
        "room_number",
        "created_at",
    )

    search_fields = (
        "department_name",
    )

    ordering = (
        "department_name",
    )


@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "user",
        "department",
        "specialization",
        "consultation_fee",
        "license_number",
        "is_active",
    )

    search_fields = (
        "user__username",
        "license_number",
        "specialization",
    )

    list_filter = (
        "department",
        "is_active",
    )


@admin.register(DoctorAvailability)
class DoctorAvailabilityAdmin(admin.ModelAdmin):

    list_display = (
        "id",
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