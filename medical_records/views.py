from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib import messages

from .models import MedicalRecord
from .forms import MedicalRecordForm
from appointments.models import Appointment
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.contrib.auth.decorators import login_required

@login_required
def medical_record_list(request):

    records=MedicalRecord.objects.select_related(
        "appointment",
        "appointment__doctor__user",
        "appointment__patient__user",
    ).prefetch_related(
        "prescriptions"
    ).order_by("-created_at")

    if hasattr(request.user,"doctor_profile"):
        records=records.filter(
            appointment__doctor=request.user.doctor_profile
        )

    elif hasattr(request.user,"patient_profile"):
        records=records.filter(
            appointment__patient=request.user.patient_profile
        )

    return render(
        request,
        "medical_records/medical_record_list.html",
        {
            "records":records
        }
    )
@login_required
def medical_record_create(request):

    doctor=getattr(request.user,"doctor_profile",None)

    if not doctor:
        messages.error(request,"Only doctors can create medical records.")
        return redirect("medical_record_list")

    if request.method=="POST":

        form=MedicalRecordForm(request.POST,doctor=doctor)

        if form.is_valid():

            appointment=form.cleaned_data["appointment"]

            if appointment.doctor!=doctor:
                messages.error(request,"You cannot create records for another doctor's appointment.")
                return redirect("medical_record_create")

            if appointment.status!="Confirmed":
                messages.error(request,"Only confirmed appointments can have medical records.")
                return redirect("medical_record_create")

            if MedicalRecord.objects.filter(appointment=appointment).exists():
                messages.error(request,"Medical Record already exists.")
                return redirect("medical_record_create")

            record=form.save(commit=False)
            record.save()

            appointment.patient_checked_in=True
            appointment.status="Completed"
            appointment.consultation_completed_at=timezone.now()

            appointment.save(update_fields=[
                "patient_checked_in",
                "status",
                "consultation_completed_at"
            ])

            messages.success(
                request,
                f"Medical Record created successfully for {appointment.patient.user.get_full_name()}."
            )

            return redirect(
                "prescription_create",
                record_id=record.id
            )

    else:

        appointment_id=request.GET.get("appointment")

        if appointment_id:

            form=MedicalRecordForm(
                initial={
                    "appointment":appointment_id
                },
                doctor=doctor
            )

        else:

            form=MedicalRecordForm(
                doctor=doctor
            )

    return render(
        request,
        "medical_records/medical_record_form.html",
        {
            "form":form,
            "is_update":False,
        }
    )
@login_required
def medical_record_update(request,pk):

    doctor=getattr(request.user,"doctor_profile",None)

    if not doctor:
        messages.error(request,"Only doctors can update medical records.")
        return redirect("medical_record_list")

    record=get_object_or_404(
        MedicalRecord.objects.select_related(
            "appointment",
            "appointment__doctor__user",
            "appointment__patient__user"
        ),
        pk=pk
    )

    if record.appointment.doctor!=doctor:
        messages.error(request,"You cannot edit another doctor's medical record.")
        return redirect("medical_record_list")

    if request.method=="POST":

        form=MedicalRecordForm(
            request.POST,
            instance=record,
            doctor=doctor
        )

        if form.is_valid():

            record=form.save()

            appointment=record.appointment

            appointment.patient_checked_in=True
            appointment.status="Completed"

            if not appointment.consultation_completed_at:
                appointment.consultation_completed_at=timezone.now()

            appointment.save(update_fields=[
                "patient_checked_in",
                "status",
                "consultation_completed_at"
            ])

            messages.success(
                request,
                "Medical Record Updated Successfully."
            )

            return redirect("medical_record_detail",pk=record.pk)

    else:

        form=MedicalRecordForm(
            instance=record,
            doctor=doctor
        )

    return render(
        request,
        "medical_records/medical_record_form.html",
        {
            "form":form,
            "record":record,
            "is_update":True,
        }
    )
@login_required
def medical_record_delete(request,pk):

    doctor=getattr(request.user,"doctor_profile",None)

    if not doctor:
        messages.error(request,"Only doctors can delete medical records.")
        return redirect("medical_record_list")

    record=get_object_or_404(
        MedicalRecord.objects.select_related(
            "appointment",
            "appointment__doctor"
        ),
        pk=pk
    )

    if record.appointment.doctor!=doctor:
        messages.error(request,"You cannot delete another doctor's medical record.")
        return redirect("medical_record_list")

    if request.method=="POST":

        appointment=record.appointment

        appointment.status="Confirmed"
        appointment.patient_checked_in=False
        appointment.consultation_completed_at=None

        appointment.save(update_fields=[
            "status",
            "patient_checked_in",
            "consultation_completed_at"
        ])

        record.delete()

        messages.success(
            request,
            "Medical Record Deleted Successfully."
        )

        return redirect("medical_record_list")

    return render(
        request,
        "medical_records/medical_record_confirm_delete.html",
        {
            "record":record
        }
    )
@login_required
def medical_record_detail(request,pk):

    record=get_object_or_404(
        MedicalRecord.objects.select_related(
            "appointment",
            "appointment__doctor__user",
            "appointment__doctor__department",
            "appointment__patient__user"
        ).prefetch_related(
            "prescriptions"
        ),
        pk=pk
    )

    if hasattr(request.user,"doctor_profile"):
        if record.appointment.doctor!=request.user.doctor_profile:
            messages.error(request,"Access Denied.")
            return redirect("medical_record_list")

    elif hasattr(request.user,"patient_profile"):
        if record.appointment.patient!=request.user.patient_profile:
            messages.error(request,"Access Denied.")
            return redirect("medical_record_list")

    prescriptions=record.prescriptions.all()

    return render(
        request,
        "medical_records/medical_record_detail.html",
        {
            "record":record,
            "prescriptions":prescriptions,
            "appointment":record.appointment,
            "doctor":record.appointment.doctor,
            "patient":record.appointment.patient,
        }
    )
@login_required
def get_appointment_details(request,pk):

    appointment=get_object_or_404(
        Appointment.objects.select_related(
            "doctor__user",
            "doctor__department",
            "patient__user"
        ),
        pk=pk
    )

    if hasattr(request.user,"doctor_profile"):
        if appointment.doctor!=request.user.doctor_profile:
            return JsonResponse(
                {"error":"Access Denied"},
                status=403
            )

    elif hasattr(request.user,"patient_profile"):
        if appointment.patient!=request.user.patient_profile:
            return JsonResponse(
                {"error":"Access Denied"},
                status=403
            )

    data={

        "appointment_id":appointment.id,

        "doctor_name":
        f"Dr. {appointment.doctor.user.get_full_name() or appointment.doctor.user.username}",

        "department":
        appointment.doctor.department.department_name,

        "patient_name":
        appointment.patient.user.get_full_name() or appointment.patient.user.username,

        "appointment_date":
        appointment.appointment_date.strftime("%d %b %Y"),

        "appointment_time":
        appointment.appointment_time.strftime("%I:%M %p"),

        "status":
        appointment.status,

        "reason":
        appointment.reason,

        "risk_level":
        appointment.risk_level,

        "risk_score":
        appointment.risk_score,

        "checked_in":
        appointment.patient_checked_in,

        "consultation_completed":
        appointment.consultation_completed_at.strftime("%d %b %Y %I:%M %p")
        if appointment.consultation_completed_at
        else None,

        "sms_reminder":
        appointment.sms_reminder_sent,

    }

    return JsonResponse(data)