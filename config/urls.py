"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),

    path("", include("accounts.urls")),
    path("", include("hospital.urls")),
    path("", include("patients.urls")),
    path("", include("appointments.urls")),
    path(
    "medical-records/",
    include("medical_records.urls")
),
    path("", include("prescriptions.urls")),   
    path("", include("billing.urls")),
    path("", include("chatbot.urls")),
    path("dashboard/", include("dashboard.urls")),

]
