from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),

    path("", include("accounts.urls")),
    path("", include("hospital.urls")),
    path("", include("patients.urls")),
    path("", include("appointments.urls")),
    path("", include("medical_records.urls")),
    path("", include("prescriptions.urls")),
    path("", include("billing.urls")),
    path("", include("chatbot.urls")),
    path("", include("ai_prediction.urls")),
    path("", include("support.urls")),

]