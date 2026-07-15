from django.shortcuts import render, redirect, get_object_or_404

from .models import Prescription
from .forms import PrescriptionForm


def prescription_list(request):

    prescriptions = (
        Prescription.objects
        .select_related(
            "medical_record",
            "medical_record__appointment",
            "medical_record__appointment__patient__user",
            "medical_record__appointment__doctor__user",
        )
        .all()
    )

    return render(
        request,
        "prescriptions/prescription_list.html",
        {
            "prescriptions": prescriptions
        }
    )


def prescription_create(request, record_id):

    if request.method == "POST":

        form = PrescriptionForm(request.POST)

        if form.is_valid():

            prescription = form.save(commit=False)
            prescription.medical_record_id = record_id
            prescription.save()

            return redirect("prescription_list")

    else:

        form = PrescriptionForm()

    return render(
        request,
        "prescriptions/prescription_form.html",
        {
            "form": form
        }
    )


def prescription_update(request, pk):

    prescription = get_object_or_404(
        Prescription,
        pk=pk
    )

    if request.method == "POST":

        form = PrescriptionForm(
            request.POST,
            instance=prescription
        )

        if form.is_valid():

            form.save()

            return redirect("prescription_list")

    else:

        form = PrescriptionForm(
            instance=prescription
        )

    return render(
        request,
        "prescriptions/prescription_form.html",
        {
            "form": form
        }
    )


def prescription_delete(request, pk):

    prescription = get_object_or_404(
        Prescription,
        pk=pk
    )

    if request.method == "POST":

        prescription.delete()

        return redirect("prescription_list")

    return render(
        request,
        "prescriptions/prescription_confirm_delete.html",
        {
            "prescription": prescription
        }
    )