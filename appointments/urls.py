from django.urls import path
from . import views

urlpatterns = [
    path("appointment/add/", views.appointment_create, name="appointment_create"),
    path("appointments/", views.appointment_list, name="appointment_list"),
    path("appointment/update/<int:pk>/", views.appointment_update, name="appointment_update"),
    path("appointment/delete/<int:pk>/", views.appointment_delete, name="appointment_delete"),
    path("patient/<int:patient_id>/history/", views.patient_history_view, name="patient_history"),
    path("appointment/<int:pk>/confirm/", views.mark_confirmed, name="mark_confirmed"),
    path("appointment/<int:pk>/cancel/", views.mark_cancelled, name="mark_cancelled"),
    path("appointment/<int:pk>/no-show/", views.mark_noshow, name="mark_noshow"),
    path("appointment/<int:pk>/patient-cancel/", views.patient_cancel_appointment, name="patient_cancel_appointment"),
    path("voice-booking/", views.voice_booking_page, name="voice_booking_page"),
    path("api/department/<int:department_id>/doctors/", views.get_doctors_by_department, name="get_doctors_by_department"),
]