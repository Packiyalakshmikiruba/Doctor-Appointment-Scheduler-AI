from django.urls import path
from . import views

urlpatterns = [

    path(
        "",
        views.medical_record_list,
        name="medical_record_list"
    ),

    path(
        "add/",
        views.medical_record_create,
        name="medical_record_create"
    ),

    path(
        "update/<int:pk>/",
        views.medical_record_update,
        name="medical_record_update"
    ),

    path(
        "delete/<int:pk>/",
        views.medical_record_delete,
        name="medical_record_delete"
    ),

]