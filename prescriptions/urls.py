from django.urls import path
from . import views

urlpatterns = [
    path("medical-records/<int:record_id>/prescription/", views.prescription_create, name="prescription_create"),
]