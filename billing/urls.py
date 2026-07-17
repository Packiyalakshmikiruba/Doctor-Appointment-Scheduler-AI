from django.urls import path
from . import views

urlpatterns = [

    path("", views.bill_list, name="bill_list"),

    path("create/", views.bill_create, name="bill_create"),

    path(
        "appointment/<int:appointment_id>/create/",
        views.bill_create_for_appointment,
        name="bill_create_for_appointment",
    ),

    path(
        "<int:bill_id>/add-payment/",
        views.add_payment,
        name="add_payment",
    ),

    path(
        "<int:pk>/mark-paid/",
        views.mark_paid,
        name="mark_paid",
    ),

    path(
        "<int:pk>/download/",
        views.bill_download,
        name="bill_download",
    ),

    path(
        "api/appointment/<int:pk>/fee/",
        views.get_consultation_fee,
        name="get_consultation_fee",
    ),

]