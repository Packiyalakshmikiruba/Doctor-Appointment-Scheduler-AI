from django.urls import path
from . import views

urlpatterns = [
    path("support/chat/", views.support_chat_page, name="support_chat_page"),
    path("support/send/", views.send_support_message, name="send_support_message"),
    path("support/messages/", views.get_support_messages, name="get_support_messages"),
    path("support/messages/<int:patient_id>/", views.get_support_messages, name="get_support_messages_admin"),
    path("support/inbox/", views.support_inbox, name="support_inbox"),
    path("support/conversation/<int:patient_id>/", views.support_conversation, name="support_conversation"),
]