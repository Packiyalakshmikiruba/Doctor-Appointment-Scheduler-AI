from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import HttpResponse
from reportlab.pdfgen import canvas
from .models import Prescription
from .forms import PrescriptionForm
from medical_records.models import MedicalRecord
from django.contrib.auth.decorators import login_required

@login_required
def download_prescription_pdf(request,pk):

    prescription=get_object_or_404(
        Prescription.objects.select_related(
            "medical_record",
            "medical_record__appointment",
            "medical_record__appointment__patient__user",
            "medical_record__appointment__doctor__user",
            "medical_record__appointment__doctor__department",
        ),
        pk=pk
    )

    record=prescription.medical_record
    appointment=record.appointment

    response=HttpResponse(content_type="application/pdf")
    response["Content-Disposition"]=f'attachment; filename="Prescription_{prescription.id}.pdf"'

    pdf=canvas.Canvas(response)

    y=800

    pdf.setFont("Helvetica-Bold",18)
    pdf.drawString(150,y,"AI HOSPITAL")

    y-=25
    pdf.setFont("Helvetica",11)
    pdf.drawString(120,y,"Doctor Appointment Scheduler")

    y-=35
    pdf.line(40,y,560,y)

    y-=25

    pdf.setFont("Helvetica-Bold",11)
    pdf.drawString(40,y,"Patient :")
    pdf.setFont("Helvetica",11)
    pdf.drawString(120,y,appointment.patient.user.get_full_name())

    y-=18

    pdf.setFont("Helvetica-Bold",11)
    pdf.drawString(40,y,"Doctor :")
    pdf.setFont("Helvetica",11)
    pdf.drawString(
        120,
        y,
        f"Dr. {appointment.doctor.user.get_full_name()}"
    )

    y-=18

    pdf.setFont("Helvetica-Bold",11)
    pdf.drawString(40,y,"Department :")
    pdf.setFont("Helvetica",11)
    pdf.drawString(
        120,
        y,
        appointment.doctor.department.department_name
    )

    y-=18

    pdf.setFont("Helvetica-Bold",11)
    pdf.drawString(40,y,"Date :")
    pdf.setFont("Helvetica",11)
    pdf.drawString(
        120,
        y,
        appointment.appointment_date.strftime("%d %b %Y")
    )

    y-=30

    pdf.line(40,y,560,y)

    y-=25

    pdf.setFont("Helvetica-Bold",12)
    pdf.drawString(40,y,"Medicine")

    pdf.drawString(180,y,"Dosage")

    pdf.drawString(280,y,"Frequency")

    pdf.drawString(390,y,"Duration")

    y-=15

    pdf.line(40,y,560,y)

    medicines=record.prescriptions.all()

    for medicine in medicines:

        y-=22

        pdf.setFont("Helvetica",10)

        pdf.drawString(
            40,
            y,
            medicine.medicine_name
        )

        pdf.drawString(
            180,
            y,
            medicine.dosage
        )

        pdf.drawString(
            280,
            y,
            medicine.frequency
        )

        pdf.drawString(
            390,
            y,
            f"{medicine.duration} Days"
        )

        y-=15

        pdf.drawString(
            60,
            y,
            f"{medicine.before_after_food} | {medicine.instructions or '-'}"
        )

        if y<120:
            pdf.showPage()
            y=800

    y-=40

    pdf.drawString(
        380,
        y,
        "Doctor Signature"
    )

    pdf.line(
        360,
        y-5,
        530,
        y-5
    )

    pdf.save()

    return response
@login_required
def prescription_list(request):

    prescriptions=Prescription.objects.select_related(
        "medical_record",
        "medical_record__appointment",
        "medical_record__appointment__patient__user",
        "medical_record__appointment__doctor__user",
        "medical_record__appointment__doctor__department",
    ).order_by("-created_at")

    if hasattr(request.user,"doctor_profile"):

        prescriptions=prescriptions.filter(
            medical_record__appointment__doctor=request.user.doctor_profile
        )

    elif hasattr(request.user,"patient_profile"):

        prescriptions=prescriptions.filter(
            medical_record__appointment__patient=request.user.patient_profile
        )

    return render(
        request,
        "prescriptions/prescription_list.html",
        {
            "prescriptions":prescriptions
        }
    )
@login_required
def prescription_create(request,record_id):

    doctor=getattr(request.user,"doctor_profile",None)

    if not doctor:
        messages.error(request,"Only doctors can create prescriptions.")
        return redirect("prescription_list")

    record=get_object_or_404(
        MedicalRecord.objects.select_related(
            "appointment",
            "appointment__doctor",
            "appointment__patient__user"
        ),
        pk=record_id
    )

    if record.appointment.doctor!=doctor:
        messages.error(request,"You cannot access another doctor's medical record.")
        return redirect("medical_record_list")

    prescriptions=Prescription.objects.filter(
        medical_record=record
    ).order_by("medicine_name")

    if request.method=="POST":

        if "finish" in request.POST:

            if not prescriptions.exists():
                messages.error(
                    request,
                    "Please add at least one medicine before finishing consultation."
                )
                return redirect(
                    "prescription_create",
                    record_id=record.id
                )

            messages.success(
                request,
                "Prescription Completed Successfully."
            )

            return redirect(
                "bill_create_for_appointment",
                appointment_id=record.appointment.id
            )

        form=PrescriptionForm(request.POST)

        if form.is_valid():

            medicine=form.cleaned_data["medicine_name"]

            if Prescription.objects.filter(
                medical_record=record,
                medicine_name__iexact=medicine
            ).exists():

                messages.warning(
                    request,
                    f"{medicine} is already added."
                )

            else:

                prescription=form.save(commit=False)

                prescription.medical_record=record

                prescription.save()

                messages.success(
                    request,
                    "Medicine Added Successfully."
                )

            return redirect(
                "prescription_create",
                record_id=record.id
            )

    else:

        form=PrescriptionForm()

    return render(
        request,
        "prescriptions/prescription_form.html",
        {
            "form":form,
            "record":record,
            "existing":prescriptions,
            "appointment":record.appointment,
            "doctor":record.appointment.doctor,
            "patient":record.appointment.patient,
        }
    )
@login_required
def prescription_update(request,pk):

    doctor=getattr(request.user,"doctor_profile",None)

    if not doctor:
        messages.error(request,"Only doctors can update prescriptions.")
        return redirect("prescription_list")

    prescription=get_object_or_404(
        Prescription.objects.select_related(
            "medical_record",
            "medical_record__appointment",
            "medical_record__appointment__doctor",
            "medical_record__appointment__patient__user"
        ),
        pk=pk
    )

    if prescription.medical_record.appointment.doctor!=doctor:
        messages.error(
            request,
            "You cannot edit another doctor's prescription."
        )
        return redirect("prescription_list")

    if request.method=="POST":

        form=PrescriptionForm(
            request.POST,
            instance=prescription
        )

        if form.is_valid():

            medicine=form.cleaned_data["medicine_name"]

            exists=Prescription.objects.filter(
                medical_record=prescription.medical_record,
                medicine_name__iexact=medicine
            ).exclude(pk=prescription.pk).exists()

            if exists:

                messages.warning(
                    request,
                    f"{medicine} already exists."
                )

            else:

                form.save()

                messages.success(
                    request,
                    "Prescription Updated Successfully."
                )

                return redirect(
                    "prescription_create",
                    record_id=prescription.medical_record.id
                )

    else:

        form=PrescriptionForm(
            instance=prescription
        )

    return render(
        request,
        "prescriptions/prescription_form.html",
        {
            "form":form,
            "record":prescription.medical_record,
            "editing":True,
            "prescription":prescription,
            "existing":Prescription.objects.filter(
                medical_record=prescription.medical_record
            ).order_by("medicine_name"),
        }
    )
@login_required
def prescription_delete(request,pk):

    doctor=getattr(request.user,"doctor_profile",None)

    if not doctor:
        messages.error(
            request,
            "Only doctors can delete prescriptions."
        )
        return redirect("prescription_list")

    prescription=get_object_or_404(
        Prescription.objects.select_related(
            "medical_record",
            "medical_record__appointment",
            "medical_record__appointment__doctor",
            "medical_record__appointment__patient__user"
        ),
        pk=pk
    )

    if prescription.medical_record.appointment.doctor!=doctor:
        messages.error(
            request,
            "You cannot delete another doctor's prescription."
        )
        return redirect("prescription_list")

    record=prescription.medical_record

    if request.method=="POST":

        medicine=prescription.medicine_name

        prescription.delete()

        messages.success(
            request,
            f"{medicine} deleted successfully."
        )

        return redirect(
            "prescription_create",
            record_id=record.id
        )

    return render(
        request,
        "prescriptions/prescription_confirm_delete.html",
        {
            "prescription":prescription,
            "record":record,
        }
    )
@login_required
def my_prescriptions(request):

    patient=getattr(request.user,"patient_profile",None)

    if not patient:
        messages.error(
            request,
            "Only patients can access this page."
        )
        return redirect("dashboard")

    prescriptions=Prescription.objects.select_related(
        "medical_record",
        "medical_record__appointment",
        "medical_record__appointment__doctor__user",
        "medical_record__appointment__doctor__department"
    ).filter(
        medical_record__appointment__patient=patient
    ).order_by(
        "-created_at"
    )

    search=request.GET.get("search")

    if search:

        prescriptions=prescriptions.filter(
            medicine_name__icontains=search
        )

    return render(
        request,
        "prescriptions/my_prescriptions.html",
        {
            "prescriptions":prescriptions,
            "search":search,
        }
    )