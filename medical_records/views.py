from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from .models import MedicalRecord
from .forms import MedicalRecordForm
from appointments.models import Appointment


def medical_record_create(request):
    if request.method == "POST":
        form = MedicalRecordForm(request.POST)
        if form.is_valid():
            record = form.save()   # doctor/patient assign பண்ண தேவை இல்ல, property-ஆ derive ஆகும்

            record.appointment.status = "Completed"
            record.appointment.save()

            return redirect("prescription_create", record_id=record.id)
    else:
        form = MedicalRecordForm()

    return render(request, "medical_records/medical_record_form.html", {"form": form})


def get_appointment_details(request, pk):
    appointment = Appointment.objects.select_related(
        "doctor__user", "doctor__department", "patient"
    ).get(pk=pk)

    data = {
        "doctor_name": f"Dr. {appointment.doctor.user.get_full_name() or appointment.doctor.user.username}",
        "doctor_department": appointment.doctor.department.department_name,
        "patient_name": str(appointment.patient),
        "appointment_date": appointment.appointment_date.strftime("%d %b %Y"),
    }
    return JsonResponse(data)


def medical_record_list(request):
    records = MedicalRecord.objects.select_related(
        "appointment__patient", "appointment__doctor__user"
    )
    return render(request, "medical_records/medical_record_list.html", {"records": records})
def medical_record_update(request, pk):
    record = get_object_or_404(MedicalRecord, pk=pk)
    if request.method == "POST":
        form = MedicalRecordForm(request.POST, instance=record)
        if form.is_valid():
            form.save()
            return redirect("medical_record_list")
    else:
        form = MedicalRecordForm(instance=record)
    return render(request, "medical_records/medical_record_form.html", {"form": form, "record": record, "is_update": True})
def medical_record_delete(request, pk):
    record = get_object_or_404(MedicalRecord, pk=pk)

    if request.method == "POST":
        record.delete()
        return redirect("medical_record_list")

    return render(
        request,
        "medical_records/medical_record_confirm_delete.html",
        {"record": record},
    )