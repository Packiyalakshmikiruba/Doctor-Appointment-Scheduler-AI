from django.shortcuts import render, redirect, get_object_or_404
from .forms import DepartmentForm
from .models import Department
from .forms import DoctorForm
from .models import Doctor
from .forms import DoctorAvailabilityForm
from .models import DoctorAvailability

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
def doctor_create(request):

    if request.method == "POST":

        form = DoctorForm(request.POST)

        if form.is_valid():
            form.save()
            return redirect("doctor_list")

    else:

        form = DoctorForm()

    return render(
        request,
        "hospital/doctor_form.html",
        {"form": form}
    )
def doctor_list(request):

    doctors = Doctor.objects.select_related(
        "user",
        "department"
    ).all()

    context = {
        "doctors": doctors
    }

    return render(
        request,
        "hospital/doctor_list.html",
        context
    )

def doctor_update(request, pk):

    doctor = get_object_or_404(Doctor, pk=pk)

    if request.method == "POST":

        form = DoctorForm(request.POST, instance=doctor)

        if form.is_valid():
            form.save()
            return redirect("doctor_list")

    else:

        form = DoctorForm(instance=doctor)

    return render(
        request,
        "hospital/doctor_form.html",
        {"form": form}
    )
def doctor_delete(request, pk):

    doctor = get_object_or_404(Doctor, pk=pk)

    if request.method == "POST":
        doctor.delete()
        return redirect("doctor_list")

    return render(
        request,
        "hospital/doctor_confirm_delete.html",
        {"doctor": doctor}
    )
def availability_create(request):

    if request.method == "POST":

        form = DoctorAvailabilityForm(request.POST)

        if form.is_valid():
            form.save()
            return redirect("availability_list")

    else:
        form = DoctorAvailabilityForm()

    return render(
        request,
        "hospital/availability_form.html",
        {"form": form}
    )


def availability_list(request):

    availabilities = DoctorAvailability.objects.select_related(
        "doctor",
        "doctor__user"
    ).all()

    return render(
        request,
        "hospital/availability_list.html",
        {
            "availabilities": availabilities
        }
    )


def doctor_dashboard(request):

    return render(
        request,
        "hospital/doctor_dashboard.html"
    )