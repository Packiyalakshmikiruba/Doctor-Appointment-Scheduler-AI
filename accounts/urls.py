from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path("register/", views.register_view, name="register"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),

    path("dashboard/", views.dashboard_redirect, name="dashboard"),
    path("dashboard/patient/", views.patient_dashboard_view, name="patient_dashboard"),
    path("dashboard/doctor/", views.doctor_dashboard_view, name="doctor_dashboard"),
    path("dashboard/admin/", views.admin_dashboard_view, name="admin_dashboard"),

    path(
        "change-password/",
        auth_views.PasswordChangeView.as_view(
            template_name="accounts/change_password.html",
            success_url="/change-password/done/",
        ),
        name="change_password",
    ),
    path(
        "change-password/done/",
        auth_views.PasswordChangeDoneView.as_view(
            template_name="accounts/change_password_done.html"
        ),
        name="password_change_done",
    ),
]