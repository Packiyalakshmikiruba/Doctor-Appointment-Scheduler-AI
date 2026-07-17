from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from .models import Bill, Payment
from .forms import BillForm, PaymentForm
from appointments.models import Appointment
from django.http import HttpResponse
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from django.contrib import messages
from reportlab.lib import colors
from reportlab.pdfbase.pdfmetrics import stringWidth
from decimal import Decimal
from django.contrib import messages

def bill_create_for_appointment(request, appointment_id):

    appointment = get_object_or_404(
        Appointment,
        pk=appointment_id
    )

    if Bill.objects.filter(
        appointment=appointment
    ).exists():

        bill = Bill.objects.get(
            appointment=appointment
        )

        messages.info(
            request,
            "Bill already generated."
        )

        return redirect(
            "bill_download",
            pk=bill.id
        )

    if request.method == "POST":

        form = BillForm(request.POST)

        if form.is_valid():

            bill = form.save(commit=False)

            bill.appointment = appointment

            bill.consultation_fee = appointment.doctor.consultation_fee

            bill.save()

            messages.success(
                request,
                "Bill Generated Successfully."
            )

            return redirect(
                "bill_download",
                pk=bill.id
            )

    else:

        form = BillForm(initial={

            "appointment": appointment,

            "consultation_fee":
            appointment.doctor.consultation_fee,

            "medicine_cost": Decimal("0"),

            "lab_test_cost": Decimal("0"),

            "discount": Decimal("0"),

            "gst": Decimal("0"),

            "payment_status": "Pending",

        })

    return render(

        request,

        "billing/bill_form.html",

        {

            "form": form,

            "appointment": appointment,

        },

    )

def get_consultation_fee(request, pk):

    appointment = get_object_or_404(Appointment, pk=pk)

    return JsonResponse({

        "fee": float(appointment.doctor.consultation_fee),

        "patient_name":
        appointment.patient.user.get_full_name(),

        "doctor_name":
        appointment.doctor.user.get_full_name(),

        "department_name":
        appointment.doctor.department.department_name,

        "appointment_date":
        appointment.appointment_date.strftime("%d-%m-%Y"),

    })

def bill_list(request):
    bills = Bill.objects.select_related("appointment__patient", "appointment__doctor__user")
    return render(request, "billing/bill_list.html", {"bills": bills})


def mark_paid(request, pk):
    bill = get_object_or_404(Bill, pk=pk)
    bill.payment_status = "Paid"    # ← Fix: "PAID" இல்ல, "Paid" (Meta choices-ஓடு exact match)
    bill.save()
    return redirect("bill_list")


def add_payment(request, bill_id):
    bill = get_object_or_404(Bill, pk=bill_id)

    if request.method == "POST":
        form = PaymentForm(request.POST)

        if form.is_valid():
            payment = form.save(commit=False)
            payment.bill = bill
            payment.save()

            if bill.balance_due <= 0:
                bill.payment_status = "Paid"
                bill.save()

            return redirect("bill_list")

    else:
        form = PaymentForm()

    return render(request, "billing/payment_form.html", {
        "form": form,
        "bill": bill,
    })

def bill_download(request, pk):

    bill = get_object_or_404(Bill, pk=pk)

    appointment = bill.appointment

    response = HttpResponse(
        content_type="application/pdf"
    )

    response[
        "Content-Disposition"
    ] = f'attachment; filename="Bill_{bill.id}.pdf"'

    pdf = canvas.Canvas(
        response,
        pagesize=A4
    )

    width, height = A4

    y = height - 50

    pdf.setFont(
        "Helvetica-Bold",
        18
    )

    pdf.drawString(
        50,
        y,
        "HOSPITAL BILL"
    )

    y -= 40

    pdf.setFont(
        "Helvetica",
        11
    )

    pdf.drawString(
        50,
        y,
        f"Bill No : {bill.id}"
    )

    y -= 20

    pdf.drawString(
        50,
        y,
        f"Patient : {appointment.patient.user.get_full_name()}"
    )

    y -= 20

    pdf.drawString(
        50,
        y,
        f"Doctor : Dr. {appointment.doctor.user.get_full_name()}"
    )

    y -= 20

    pdf.drawString(
        50,
        y,
        f"Department : {appointment.doctor.department.department_name}"
    )

    y -= 20

    pdf.drawString(
        50,
        y,
        f"Appointment Date : {appointment.appointment_date}"
    )

    y -= 40

    pdf.line(40, y, 550, y)

    y -= 20

    pdf.drawString(
        60,
        y,
        "Consultation Fee"
    )

    pdf.drawRightString(
        520,
        y,
        f"Rs. {bill.consultation_fee}"
    )

    y -= 20

    pdf.drawString(
        60,
        y,
        "Medicine Cost"
    )

    pdf.drawRightString(
        520,
        y,
        f"Rs. {bill.medicine_cost}"
    )

    y -= 20

    pdf.drawString(
        60,
        y,
        "Lab Test"
    )

    pdf.drawRightString(
        520,
        y,
        f"Rs. {bill.lab_test_cost}"
    )

    y -= 20

    pdf.drawString(
        60,
        y,
        "GST"
    )

    pdf.drawRightString(
        520,
        y,
        f"Rs. {bill.gst}"
    )

    y -= 20

    pdf.drawString(
        60,
        y,
        "Discount"
    )

    pdf.drawRightString(
        520,
        y,
        f"- Rs. {bill.discount}"
    )

    y -= 20

    pdf.line(40, y, 550, y)

    y -= 25

    pdf.setFont(
        "Helvetica-Bold",
        13
    )

    pdf.drawString(
        60,
        y,
        "TOTAL"
    )

    pdf.drawRightString(
        520,
        y,
        f"Rs. {bill.total_amount}"
    )

    y -= 40

    pdf.drawString(
        60,
        y,
        f"Payment Status : {bill.payment_status}"
    )

    pdf.showPage()

    pdf.save()

    return response
def bill_create(request):
    if request.method == "POST":
        form = BillForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("bill_list")
    else:
        form = BillForm()

    return render(request, "billing/bill_form.html", {
        "form": form
    })