from django.urls import path
from . import views

urlpatterns = [
    path("contacts/", views.contacts_list, name="contacts_list"),
    path("send/", views.send_message, name="send_message"),
    path("data/<int:user_id>/", views.get_messages, name="get_messages"),
]