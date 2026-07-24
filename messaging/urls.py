from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static
urlpatterns = [
    path("contacts/", views.contacts_list, name="contacts_list"),
    path("send/", views.send_message, name="send_message"),
    path("data/<int:user_id>/", views.get_messages_data, name="get_messages"),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)