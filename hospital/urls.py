from django.urls import path
from . import views

urlpatterns = [

    # Department URLs
    path("departments/", views.department_list, name="department_list"),
    path("departments/add/", views.department_create, name="department_create"),
    path("departments/<int:pk>/edit/", views.department_update, name="department_update"),
    path("departments/<int:pk>/delete/", views.department_delete, name="department_delete"),

    # Doctor URLs
    path("doctors/", views.doctor_list, name="doctor_list"),
    path("doctors/add/", views.doctor_create, name="doctor_create"),
    path("doctors/<int:pk>/edit/", views.doctor_update, name="doctor_update"),
    path("doctors/<int:pk>/delete/", views.doctor_delete, name="doctor_delete"),
    path(
    "doctor/dashboard/",
    views.doctor_dashboard,
    name="doctor_dashboard",
),
path(
    "contact-admin/",
    views.contact_admin,
    name="contact_admin",
),
path(
    "doctor/<int:doctor_id>/generate/",
    views.generate_week_schedule,
    name="generate_week_schedule",
),
path(
    "doctor-leaves/",
    views.doctor_leave_list,
    name="doctor_leave_list"
),

path(
    "doctor-leaves/add/",
    views.doctor_leave_create,
    name="doctor_leave_create"
),

path(
    "doctor-leaves/<int:pk>/delete/",
    views.doctor_leave_delete,
    name="doctor_leave_delete"
),
path("doctor/checkin/", views.doctor_checkin, name="doctor_checkin"),
path("doctor/checkout/", views.doctor_checkout, name="doctor_checkout"),
path("doctor/status/", views.update_doctor_status, name="update_doctor_status"),
path("doctor/leave/add/", views.doctor_leave_create, name="doctor_leave_create"),
    # Doctor Availability URLs
    path("availability/", views.availability_list, name="availability_list"),
    path("availability/add/", views.availability_create, name="availability_create"),

]