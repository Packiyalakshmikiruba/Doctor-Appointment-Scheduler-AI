from django.urls import path
from . import views

urlpatterns = [

    path(
        "",
        views.bill_list,
        name="bill_list"
    ),

    path(
        "create/",
        views.bill_create,
        name="bill_create"
    ),

    path(
        "appointment/<int:appointment_id>/",
        views.bill_create_for_appointment,
        name="bill_create_for_appointment"
    ),

    path(
        "my-bills/",
        views.my_bills,
        name="my_bills"
    ),

    path(
        "view/<int:pk>/",
        views.bill_detail,
        name="bill_detail"
    ),

    path(
        "update/<int:pk>/",
        views.bill_update,
        name="bill_update"
    ),

    path(
        "delete/<int:pk>/",
        views.bill_delete,
        name="bill_delete"
    ),

    path(
        "download/<int:pk>/",
        views.download_bill_pdf,
        name="download_bill_pdf"
    ),

    path(
        "consultation-fee/<int:pk>/",
        views.get_consultation_fee,
        name="get_consultation_fee"
    ),
]