from django.urls import path
from . import views

urlpatterns = [
    path("medical-records/<int:pk>/view/", views.medical_record_detail, name="medical_record_detail"),
    path("medical-records/", views.medical_record_list, name="medical_record_list"),
    path("medical-records/add/", views.medical_record_create, name="medical_record_create"),
    path("medical-records/<int:pk>/edit/", views.medical_record_update, name="medical_record_update"),
    path("medical-records/<int:pk>/delete/", views.medical_record_delete, name="medical_record_delete"),
    path("api/appointment/<int:pk>/details/", views.get_appointment_details, name="get_appointment_details"),
]