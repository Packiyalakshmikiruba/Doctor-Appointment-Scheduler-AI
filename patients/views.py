from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Patient
from .forms import PatientForm
from django.contrib.admin.views.decorators import staff_member_required
from .forms import PatientForm, AdminPatientForm
from datetime import timedelta
from django.utils import timezone
from medical_records.models import MedicalRecord
from appointments.models import Appointment
from prescriptions.models import Prescription
from django.http import HttpResponse
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet

from prescriptions.models import Prescription
from reportlab.platypus import SimpleDocTemplate
from reportlab.platypus import Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from appointments.booking_service import book_appointment_full, handle_cancellation, BookingError
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


@login_required
def patient_cancel_appointment(request, pk):
    appt = get_object_or_404(Appointment, pk=pk)

    patient = getattr(request.user, "patient_profile", None)
    if patient is None or appt.patient_id != patient.id:
        messages.error(request, "You can only cancel your own appointments.")
        return redirect("dashboard")

    if appt.status in ("Cancelled", "Completed", "No Show"):
        messages.error(request, "This appointment can no longer be cancelled.")
        return redirect("dashboard")

    naive_dt = timezone.datetime.combine(appt.appointment_date, appt.appointment_time)
    appt_dt = timezone.make_aware(naive_dt) if timezone.is_naive(naive_dt) else naive_dt

    if appt_dt - timezone.now() < timedelta(hours=2):
        messages.error(request, "Appointments can only be cancelled at least 2 hours in advance. Please call the front desk.")
        return redirect("dashboard")

    if request.method == "POST":
        appt.status = "Cancelled"
        appt.save(update_fields=["status"])

        try:
            handle_cancellation(appt)  # offers the freed slot to the waitlist
        except Exception:
            pass

        messages.success(request, "Your appointment has been cancelled.")
        return redirect("dashboard")

    return render(request, "appointments/patient_cancel_confirm.html", {"appointment": appt})
@login_required
def patient_medical_record(request, pk):

    patient = getattr(request.user, "patient_profile", None)

    record = get_object_or_404(

        MedicalRecord.objects.select_related(
            "appointment",
            "appointment__doctor__user",
            "appointment__doctor__department",
            "appointment__patient"
        ),

        pk=pk,

        appointment__patient=patient

    )

    prescriptions = Prescription.objects.filter(
        medical_record=record
    )

    return render(
        request,
        "patients/medical_record_detail.html",
        {
            "record": record,
            "prescriptions": prescriptions,
        }
    )
@login_required
def download_medical_report(request, pk):

    patient = request.user.patient_profile

    record = get_object_or_404(

        MedicalRecord,

        pk=pk,

        appointment__patient=patient

    )

    response = HttpResponse(

        content_type="application/pdf"

    )

    response["Content-Disposition"] = (
        f'attachment; filename="Medical_Report_{record.id}.pdf"'
    )

    doc = SimpleDocTemplate(response)

    styles = getSampleStyleSheet()

    elements = []

    elements.append(
        Paragraph("<b>Doctor Appointment Scheduler</b>", styles["Title"])
    )

    elements.append(
        Paragraph("<b>Medical Report</b>", styles["Heading2"])
    )

    elements.append(
        Paragraph(
            f"<b>Patient :</b> {record.appointment.patient}",
            styles["Normal"]
        )
    )

    elements.append(
        Paragraph(
            f"<b>Doctor :</b> Dr. {record.appointment.doctor.user.get_full_name()}",
            styles["Normal"]
        )
    )

    elements.append(
        Paragraph(
            f"<b>Department :</b> {record.appointment.doctor.department.department_name}",
            styles["Normal"]
        )
    )

    elements.append(
        Paragraph(
            f"<b>Date :</b> {record.appointment.appointment_date}",
            styles["Normal"]
        )
    )

    elements.append(
        Paragraph(
            "<br/><b>Symptoms</b>",
            styles["Heading3"]
        )
    )

    elements.append(
        Paragraph(
            record.symptoms,
            styles["Normal"]
        )
    )

    elements.append(
        Paragraph(
            "<br/><b>Diagnosis</b>",
            styles["Heading3"]
        )
    )

    elements.append(
        Paragraph(
            record.diagnosis,
            styles["Normal"]
        )
    )

    elements.append(
        Paragraph(
            "<br/><b>Notes</b>",
            styles["Heading3"]
        )
    )

    elements.append(
        Paragraph(
            record.notes or "-",
            styles["Normal"]
        )
    )

    elements.append(
        Paragraph(
            f"<br/><b>Follow Up :</b> {record.follow_up_date}",
            styles["Normal"]
        )
    )

    doc.build(elements)

    return response
@login_required
def patient_medical_history(request):

    patient = getattr(request.user, "patient_profile", None)

    if patient is None:
        messages.error(request, "Patient profile not found.")
        return redirect("dashboard")

    records = (
        MedicalRecord.objects
        .select_related(
            "appointment",
            "appointment__doctor__user",
            "appointment__doctor__department",
            "appointment__patient",
        )
        .filter(
            appointment__patient=patient
        )
        .order_by("-created_at")
    )

    return render(
        request,
        "patients/medical_history.html",
        {
            "records": records
        }
    )



@login_required
def download_prescription(request, pk):

    patient = request.user.patient_profile


    prescription = get_object_or_404(

        Prescription,

        pk=pk,

        medical_record__appointment__patient=patient

    )


    response = HttpResponse(
        content_type="application/pdf"
    )


    response["Content-Disposition"] = (
        f'attachment; filename="Prescription_{pk}.pdf"'
    )


    doc = SimpleDocTemplate(response)


    styles = getSampleStyleSheet()


    elements = []



    record = prescription.medical_record


    appointment = record.appointment



    elements.append(

        Paragraph(

            "<b>Doctor Appointment Scheduler</b>",

            styles["Title"]

        )

    )


    elements.append(

        Paragraph(

            "<b>Prescription</b>",

            styles["Heading2"]

        )

    )


    elements.append(

        Paragraph(

            f"""
            Patient :
            {appointment.patient.user.get_full_name()}
            """,

            styles["Normal"]

        )

    )


    elements.append(

        Paragraph(

            f"""
            Doctor :
            Dr.
            {appointment.doctor.user.get_full_name()}
            """,

            styles["Normal"]

        )

    )


    elements.append(

        Paragraph(

            f"""
            Date :
            {appointment.appointment_date}
            """,

            styles["Normal"]

        )

    )



    elements.append(

        Paragraph(

            "<br/>Medicine Details",

            styles["Heading3"]

        )

    )



    data=[

        [
            "Medicine",
            "Dosage",
            "Frequency",
            "Duration",
            "Food"
        ],

        [

            prescription.medicine_name,

            prescription.dosage,

            prescription.frequency,

            str(
                prescription.duration
            ),

            prescription.before_after_food

        ]

    ]



    table = Table(data)



    table.setStyle(

        TableStyle([

            (
                "GRID",
                (0,0),
                (-1,-1),
                1,
                colors.black
            )

        ])

    )


    elements.append(table)



    elements.append(

        Paragraph(

            f"""
            <br/>
            Instructions:
            {prescription.instructions or '-'}
            """,

            styles["Normal"]

        )

    )


    doc.build(elements)


    return response