from django.urls import path
from . import views

urlpatterns = [

    path(
        "department/add/",
        views.department_create,
        name="department_create"
    ),
    path(
    "departments/",
    views.department_list,
    name="department_list"
),
path(
    "department/update/<int:pk>/",
    views.department_update,
    name="department_update"
),
path(
    "department/delete/<int:pk>/",
    views.department_delete,
    name="department_delete"
),
]