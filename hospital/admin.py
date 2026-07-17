from django.contrib import admin
from .models import Department, Doctor, DoctorAvailability
from .models import DoctorAttendance
from .models import DoctorStatus
from .models import DoctorLeave

admin.site.register(DoctorAttendance)

admin.site.register(DoctorStatus)
admin.site.register(DoctorLeave)

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
        "phone_number",
        "is_active",
    )

    list
    _filter = (
        "department",
        "is_active",
    )

    search_fields = (
        "user__username",
        "user__first_name",
        "specialization",
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

    search_fields = (
        "doctor__user__username",
        "doctor__user__first_name",
    )
