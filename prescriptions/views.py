from django.shortcuts import render, redirect, get_object_or_404
from medical_records.models import MedicalRecord
from .forms import PrescriptionFormSet


def prescription_create(request, record_id):
    record = get_object_or_404(MedicalRecord, pk=record_id)

    if request.method == "POST":
        formset = PrescriptionFormSet(request.POST, instance=record)
        if formset.is_valid():
            formset.save()
            return redirect("medical_record_list")
    else:
        formset = PrescriptionFormSet(instance=record)

    return render(
        request,
        "prescriptions/prescription_form.html",
        {"formset": formset, "record": record}
    )