from django.shortcuts import render, redirect, get_object_or_404

from .models import MedicalRecord
from .forms import MedicalRecordForm


def medical_record_list(request):

    records = MedicalRecord.objects.select_related(
        "appointment",
        "appointment__patient__user",
        "appointment__doctor__user"
    )

    return render(
        request,
        "medical_records/medical_record_list.html",
        {
            "records": records
        }
    )


def medical_record_create(request):

    if request.method == "POST":

        form = MedicalRecordForm(request.POST)

        if form.is_valid():

            form.save()

            return redirect("medical_record_list")

    else:

        form = MedicalRecordForm()

    return render(
        request,
        "medical_records/medical_record_form.html",
        {
            "form": form
        }
    )


def medical_record_update(request, pk):

    record = get_object_or_404(
        MedicalRecord,
        pk=pk
    )

    if request.method == "POST":

        form = MedicalRecordForm(
            request.POST,
            instance=record
        )

        if form.is_valid():

            form.save()

            return redirect("medical_record_list")

    else:

        form = MedicalRecordForm(
            instance=record
        )

    return render(
        request,
        "medical_records/medical_record_form.html",
        {
            "form": form
        }
    )


def medical_record_delete(request, pk):

    record = get_object_or_404(
        MedicalRecord,
        pk=pk
    )

    if request.method == "POST":

        record.delete()

        return redirect("medical_record_list")

    return render(
        request,
        "medical_records/medical_record_confirm_delete.html",
        {
            "record": record
        }
    )