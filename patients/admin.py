from django.contrib import admin
from .models import Patient


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "user",
        "gender",
        "blood_group",
        "phone_number",
    )

    list_filter = (
        "gender",
        "blood_group",
    )

    search_fields = (
        "user__username",
        "user__first_name",
        "phone_number",
    )

    ordering = (
        "user",
    )

    list_per_page = 20