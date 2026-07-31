from django.urls import path
from . import views

urlpatterns = [

    path(
        "",
        views.notification_list,
        name="notification_list",
    ),

    path(
        "<int:pk>/",
        views.notification_detail,
        name="notification_detail",
    ),

    path(
        "<int:pk>/delete/",
        views.notification_delete,
        name="notification_delete",
    ),

    path(
        "mark-all-read/",
        views.mark_all_read,
        name="mark_all_read",
    ),

]