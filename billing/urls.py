from django.urls import path
from . import views

urlpatterns = [
    path("billing/", views.bill_list, name="bill_list"),
    path("billing/add/", views.bill_create, name="bill_create"),
    path("billing/<int:pk>/mark-paid/", views.mark_paid, name="mark_paid"),
    path("api/appointment/<int:pk>/fee/", views.get_consultation_fee, name="get_consultation_fee"),
]