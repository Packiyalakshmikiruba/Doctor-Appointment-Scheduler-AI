from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Patient
from .forms import PatientForm
from django.contrib.admin.views.decorators import staff_member_required
from .forms import PatientForm, AdminPatientForm

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

    return render(request, "patients/complete_profile.html", {"form": form})


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

    return render(request, "patients/complete_profile.html", {"form": form, "editing": True})


@login_required
def patient_list(request):
    if request.user.role != "ADMIN":
        messages.error(request, "Access denied.")
        return redirect("dashboard")

    patients = Patient.objects.select_related("user").all()
    return render(request, "patients/patient_list.html", {"patients": patients})


@login_required
def patient_create(request):
    if request.user.role != "ADMIN":
        messages.error(request, "Access denied.")
        return redirect("dashboard")

    if request.method == "POST":
        form = AdminPatientForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Patient registered successfully.")
            return redirect("patient_list")
    else:
        form = AdminPatientForm()

    return render(request, "patients/patient_form.html", {"form": form})


@login_required
def patient_update(request, pk):
    if request.user.role != "ADMIN":
        messages.error(request, "Access denied.")
        return redirect("dashboard")

    patient = get_object_or_404(Patient, pk=pk)

    if request.method == "POST":
        form = PatientForm(request.POST, instance=patient)   # user மாற்ற தேவை இல்ல, edit-ல PatientForm போதும்
        if form.is_valid():
            form.save()
            messages.success(request, "Patient updated successfully.")
            return redirect("patient_list")
    else:
        form = PatientForm(instance=patient)

    return render(request, "patients/patient_form.html", {"form": form})


@login_required
def patient_delete(request, pk):
    if request.user.role != "ADMIN":
        messages.error(request, "Access denied.")
        return redirect("dashboard")

    patient = get_object_or_404(Patient, pk=pk)

    if request.method == "POST":
        patient.delete()
        messages.success(request, "Patient deleted.")
        return redirect("patient_list")

    return render(request, "patients/patient_confirm_delete.html", {"patient": patient})