from django.urls import path

from . import views


urlpatterns=[

    path(
        "",
        views.payment_list,
        name="payment_list"
    ),

    path(
        "<int:pk>/",
        views.payment_detail,
        name="payment_detail"
    ),

    path(
        "create/<int:bill_id>/",
        views.payment_create,
        name="payment_create"
    ),

    path(
        "<int:pk>/edit/",
        views.payment_update,
        name="payment_update"
    ),

    path(
        "<int:pk>/delete/",
        views.payment_delete,
        name="payment_delete"
    ),

    path(
        "my-payments/",
        views.my_payments,
        name="my_payments"
    ),

    path(
        "<int:pk>/receipt/",
        views.download_receipt,
        name="download_receipt"
    ),

]