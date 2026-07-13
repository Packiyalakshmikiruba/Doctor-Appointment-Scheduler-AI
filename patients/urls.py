from django.urls import path
from . import views

urlpatterns = [

    path(
        "patient/add/",
        views.patient_create,
        name="patient_create"
    ),

    path(
        "patients/",
        views.patient_list,
        name="patient_list"
    ),
    path(
    "patient/update/<int:pk>/",
    views.patient_update,
    name="patient_update"
),
path(
    "patient/delete/<int:pk>/",
    views.patient_delete,
    name="patient_delete"
),

]