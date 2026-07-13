from django.shortcuts import render, redirect, get_object_or_404
from .forms import PatientForm
from .models import Patient

def patient_create(request):

    if request.method == "POST":

        form = PatientForm(request.POST)

        if form.is_valid():
            form.save()
            return redirect("patient_list")

    else:
        form = PatientForm()

    return render(
        request,
        "patients/patient_form.html",
        {"form": form}
    )

def patient_list(request):

    patients = Patient.objects.select_related("user").all()

    return render(
        request,
        "patients/patient_list.html",
        {
            "patients": patients
        }
    )
def patient_update(request, pk):

    patient = get_object_or_404(Patient, pk=pk)

    if request.method == "POST":

        form = PatientForm(request.POST, instance=patient)

        if form.is_valid():
            form.save()
            return redirect("patient_list")

    else:

        form = PatientForm(instance=patient)

    return render(
        request,
        "patients/patient_form.html",
        {
            "form": form
        }
    )
def patient_delete(request, pk):

    patient = get_object_or_404(Patient, pk=pk)

    if request.method == "POST":
        patient.delete()
        return redirect("patient_list")

    return render(
        request,
        "patients/patient_confirm_delete.html",
        {
            "patient": patient
        }
    )