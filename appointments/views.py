from django.shortcuts import render, redirect, get_object_or_404
from .forms import AppointmentForm
from .models import Appointment
import joblib
import os
from django.conf import settings


MODEL_PATH = os.path.join(settings.BASE_DIR, 'ml_model', 'noshow_model.pkl')
model = joblib.load(MODEL_PATH)

def appointment_create(request):

    if request.method == "POST":

        form = AppointmentForm(request.POST)

        if form.is_valid():

            form.save()

            return redirect("appointment_list")

    else:

        form = AppointmentForm()

    return render(
        request,
        "appointments/appointment_form.html",
        {
            "form": form
        }
    )
def appointment_list(request):

    appointments = Appointment.objects.select_related(
        "patient__user",
        "doctor__user"
    ).all().order_by("-appointment_date", "-appointment_time")

    return render(
        request,
        "appointments/appointment_list.html",
        {
            "appointments": appointments
        }
    )
def appointment_update(request, pk):

    appointment = get_object_or_404(Appointment, pk=pk)

    if request.method == "POST":

        form = AppointmentForm(request.POST, instance=appointment)

        if form.is_valid():
            form.save()
            return redirect("appointment_list")

    else:

        form = AppointmentForm(instance=appointment)

    return render(
        request,
        "appointments/appointment_form.html",
        {
            "form": form
        }
    )
def appointment_delete(request, pk):

    appointment = get_object_or_404(appointment, pk=pk)

    if request.method == "POST":
        appointment.delete()
        return redirect("Appointment_list")

    return render(
        request,
        "appointments/appointment_confirm_delete.html",
        {
            "appointment": appointment
        }
    )