from django.contrib import admin
from .models import MedicalRecord


@admin.register(MedicalRecord)
class MedicalRecordAdmin(admin.ModelAdmin):

    list_display = (
        "appointment",
        "follow_up_date",
        "created_at",
    )

    search_fields = (
        "appointment__patient__user__username",
        "appointment__doctor__user__username",
    )