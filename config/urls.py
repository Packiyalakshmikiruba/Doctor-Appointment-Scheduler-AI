from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
urlpatterns = [
    path("admin/", admin.site.urls),
   path(
    "notifications/",
    include("notifications.urls"),
),
    path("", include("accounts.urls")),
    path("", include("hospital.urls")),
    path("", include("patients.urls")),
    path("", include("appointments.urls")),
    path("", include("medical_records.urls")),
    path("", include("prescriptions.urls")),
    path("", include("billing.urls")),
    path("", include("payment.urls")),
    path("", include("chatbot.urls")),
    path("", include("ai_prediction.urls")),
    path('messaging/', include('messaging.urls'))

]
if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )

    urlpatterns += static(
        settings.STATIC_URL,
        document_root=settings.STATIC_ROOT
    )