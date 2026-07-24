from django.urls import path
from . import views

urlpatterns = [
    path("patient/complete-profile/", views.complete_profile, name="complete_profile"),
    path("patient/edit-profile/", views.edit_profile, name="edit_profile"),
    path(
        "cancel/<int:pk>/",
        views.patient_cancel_appointment,
        name="patient_cancel_appointment",
    ),
    path(
        "medical-history/",
        views.patient_medical_history,
        name="patient_medical_history"
    ),
    path(
    "medical-history/<int:pk>/download/",
    views.download_medical_report,
    name="download_medical_report"
),
path(
    "prescription/<int:pk>/download/",
    views.download_prescription,
    name="download_prescription"
),
path(
    "patient/profile/",
    views.patient_profile,
    name="patient_profile"
),

    path(
        "medical-history/<int:pk>/",
        views.patient_medical_record,
        name="patient_medical_record"
    ),
    path("patients/", views.patient_list, name="patient_list"),
    path("patient/add/", views.patient_create, name="patient_create"),
    path("patient/update/<int:pk>/", views.patient_update, name="patient_update"),
    path("patient/delete/<int:pk>/", views.patient_delete, name="patient_delete"),
]