from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Patient
from .forms import PatientForm


@login_required
def complete_profile(request):

    if hasattr(request.user, "patient_profile"):
        messages.info(request, "Your profile is already complete.")
        return redirect("dashboard")

    if request.method == "POST":
        form = PatientForm(request.POST)

        if form.is_valid():
            patient = form.save(commit=False)
            patient.user = request.user
            patient.save()
            messages.success(request, "Profile completed successfully!")
            return redirect("dashboard")

    else:
        form = PatientForm()

    return render(
        request,
        "patients/complete_profile.html",
        {"form": form}
    )


@login_required
def edit_profile(request):

    try:
        patient = request.user.patient_profile
    except Patient.DoesNotExist:
        return redirect("complete_profile")

    if request.method == "POST":
        form = PatientForm(request.POST, instance=patient)

        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully!")
            return redirect("dashboard")

    else:
        form = PatientForm(instance=patient)

    return render(
        request,
        "patients/complete_profile.html",
        {"form": form, "editing": True}
    )


# ---------------- Admin-side CRUD (Hospital staff manage all patients) ----------------

def patient_list(request):
    patients = Patient.objects.select_related("user").all()
    return render(
        request,
        "patients/patient_list.html",
        {"patients": patients}
    )


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


def patient_update(request, pk):
    patient = Patient.objects.get(pk=pk)

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
        {"form": form}
    )


def patient_delete(request, pk):
    patient = Patient.objects.get(pk=pk)

    if request.method == "POST":
        patient.delete()
        return redirect("patient_list")

    return render(
        request,
        "patients/patient_confirm_delete.html",
        {"patient": patient}
    )
@login_required
def dashboard(request):

    if request.user.role == "PATIENT" and not hasattr(request.user, "patient_profile"):
        messages.info(request, "Please complete your profile to continue.")
        return redirect("complete_profile")

    return render(request, "accounts/dashboard.html")