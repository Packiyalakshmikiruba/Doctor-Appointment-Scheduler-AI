from django.urls import path
from . import views

urlpatterns = [

    path(
        "",
        views.prescription_list,
        name="prescription_list"
    ),

    path(
        "medical-records/<int:record_id>/prescription/",
        views.prescription_create,
        name="prescription_create"
    ),

    path(
        "update/<int:pk>/",
        views.prescription_update,
        name="prescription_update"
    ),

    path(
        "delete/<int:pk>/",
        views.prescription_delete,
        name="prescription_delete"
    ),

]