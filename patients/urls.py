from django.urls import path
from . import views

urlpatterns = [
    path("patient/complete-profile/", views.complete_profile, name="complete_profile"),
    path("patient/edit-profile/", views.edit_profile, name="edit_profile"),

    # உங்க existing admin-side CRUD paths (இருந்தா அப்படியே வைத்துக்கோங்க)
    path("patient/add/", views.patient_create, name="patient_create"),
    path("patients/", views.patient_list, name="patient_list"),
    path("patient/update/<int:pk>/", views.patient_update, name="patient_update"),
    path("patient/delete/<int:pk>/", views.patient_delete, name="patient_delete"),
]