from django.urls import path
from . import views

urlpatterns = [

   path(
        "appointment/add/",
        views.appointment_create,
        name="appointment_create"
    ),

    path(
        "appointments/",
        views.appointment_list,
        name="appointment_list"
    ),
    path(
    "appointment/update/<int:pk>/",
    views.appointment_update,
    name="appointment_update"
),
path(
    "appointment/delete/<int:pk>/",
    views.appointment_delete,
    name="appointment_delete"
),

]