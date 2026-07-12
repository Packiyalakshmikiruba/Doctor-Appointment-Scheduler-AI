from django.shortcuts import render, redirect, get_object_or_404
from .forms import DepartmentForm
from .models import Department

def department_create(request):

    if request.method == "POST":
        form = DepartmentForm(request.POST)

        if form.is_valid():
            form.save()
            return redirect("department_list")

    else:
        form = DepartmentForm()

    return render(
        request,
        "hospital/department_form.html",
        {"form": form}
    )
def department_list(request):

    departments = Department.objects.all()

    context = {
        "departments": departments
    }

    return render(
        request,
        "hospital/department_list.html",
        context
    )
def department_update(request, pk):

    department = get_object_or_404(Department, pk=pk)

    if request.method == "POST":
        form = DepartmentForm(request.POST, instance=department)

        if form.is_valid():
            form.save()
            return redirect("department_list")

    else:
        form = DepartmentForm(instance=department)

    return render(
        request,
        "hospital/department_form.html",
        {"form": form}
    )
def department_delete(request, pk):

    department = get_object_or_404(Department, pk=pk)

    if request.method == "POST":
        department.delete()
        return redirect("department_list")

    return render(
        request,
        "hospital/department_confirm_delete.html",
        {"department": department}
    )