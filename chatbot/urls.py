from django.urls import path
from . import views

urlpatterns = [
    path("chat/", views.chat_widget, name="chat_widget"),
    path("api/chat/", views.chat_api, name="chat_api"),
    path("api/chat/upload-file/", views.upload_medical_file, name="upload_medical_file"),
]
