from django.contrib import admin
from .models import Appointment


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "patient",
        "doctor",
        "appointment_date",
        "appointment_time",
        "status",
        "consultation_mode",
    )

    list_filter = (
        "status",
        "appointment_date",
        "consultation_mode",
    )

    search_fields = (
        "patient__user__username",
        "doctor__user__username",
    )

    ordering = (
        "-appointment_date",
    )

    list_per_page = 20