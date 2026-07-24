from decimal import Decimal

from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from appointments.models import Appointment
from .forms import BillForm
from .models import Bill


def bill_create_for_appointment(request, appointment_id):

    appointment = get_object_or_404(
        Appointment.objects.select_related(
            "doctor",
            "doctor__user",
            "doctor__department",
            "patient",
            "patient__user",
        ),
        pk=appointment_id,
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
            "bill_detail",
            pk=bill.id
        )

    if request.method == "POST":

        form = BillForm(request.POST)

        if form.is_valid():

            bill = form.save(commit=False)

            bill.appointment = appointment

            bill.consultation_fee = (
                appointment.doctor.consultation_fee
            )

            bill.save()

            messages.success(
                request,
                "Bill Generated Successfully."
            )

            return redirect(
                "bill_detail",
                pk=bill.id
            )

    else:

        form = BillForm(
            initial={
                "appointment": appointment,
                "consultation_fee": appointment.doctor.consultation_fee,
                "medicine_cost": Decimal("0.00"),
                "lab_test_cost": Decimal("0.00"),
                "discount": Decimal("0.00"),
                "gst": Decimal("0.00"),
                "payment_status": "Pending",
            }
        )

    return render(
        request,
        "billing/bill_form.html",
        {
            "form": form,
            "appointment": appointment,
            "is_update": False,
        },
    )


@login_required
def bill_list(request):

    bills = (
        Bill.objects.select_related(
            "appointment",
            "appointment__patient__user",
            "appointment__doctor__user",
            "appointment__doctor__department",
        )
        .order_by("-created_at")
    )

    if request.user.role == "PATIENT":

        bills = bills.filter(
            appointment__patient=request.user.patient_profile
        )

    search = request.GET.get("search")

    if search:

        bills = bills.filter(

            Q(
                appointment__patient__user__first_name__icontains=search
            )

            |

            Q(
                appointment__doctor__user__first_name__icontains=search
            )

            |

            Q(
                payment_status__icontains=search
            )

        )

    return render(
        request,
        "billing/bill_list.html",
        {
            "bills": bills,
            "search": search,
        }
    )
def bill_detail(request, pk):

    bill = get_object_or_404(
        Bill.objects.select_related(
            "appointment",
            "appointment__patient__user",
            "appointment__doctor__user",
            "appointment__doctor__department",
        ),
        pk=pk,
    )

    return render(
        request,
        "billing/bill_detail.html",
        {
            "bill": bill,
            "appointment": bill.appointment,
            "doctor": bill.appointment.doctor,
            "patient": bill.appointment.patient,
        },
    )
def bill_update(request, pk):

    bill = get_object_or_404(
        Bill,
        pk=pk
    )

    if request.method == "POST":

        form = BillForm(
            request.POST,
            instance=bill
        )

        if form.is_valid():

            form.save()

            messages.success(
                request,
                "Bill Updated Successfully."
            )

            return redirect(
                "bill_detail",
                pk=bill.id
            )

    else:

        form = BillForm(
            instance=bill
        )

    return render(
        request,
        "billing/bill_form.html",
        {
            "form": form,
            "bill": bill,
            "is_update": True,
        }
    )


def bill_delete(request, pk):

    bill = get_object_or_404(
        Bill,
        pk=pk
    )

    if request.method == "POST":

        bill.delete()

        messages.success(
            request,
            "Bill Deleted Successfully."
        )

        return redirect(
            "bill_list"
        )

    return render(
        request,
        "billing/bill_confirm_delete.html",
        {
            "bill": bill
        }
    )


def get_consultation_fee(request, pk):

    appointment = get_object_or_404(
        Appointment.objects.select_related(
            "doctor__user",
            "doctor__department",
            "patient__user",
        ),
        pk=pk
    )

    data = {

        "fee": float(
            appointment.doctor.consultation_fee
        ),

        "patient_name":
            appointment.patient.user.get_full_name()
            or
            appointment.patient.user.username,

        "doctor_name":
            appointment.doctor.user.get_full_name()
            or
            appointment.doctor.user.username,

        "department":
            appointment.doctor.department.department_name,

        "appointment_date":
            appointment.appointment_date.strftime(
                "%d-%m-%Y"
            ),

    }

    return JsonResponse(data)
@login_required
def download_bill_pdf(request, pk):

    bill = get_object_or_404(
        Bill.objects.select_related(
            "appointment",
            "appointment__patient__user",
            "appointment__doctor__user",
            "appointment__doctor__department",
        ),
        pk=pk,
    )

    appointment = bill.appointment

    response = HttpResponse(
        content_type="application/pdf"
    )

    response["Content-Disposition"] = (
        f'attachment; filename="Bill_{bill.id}.pdf"'
    )

    pdf = canvas.Canvas(
        response,
        pagesize=A4
    )

    width, height = A4

    y = height - 50

    pdf.setFont("Helvetica-Bold", 20)
    pdf.drawCentredString(width / 2, y, "AI HOSPITAL")

    y -= 25
    pdf.setFont("Helvetica", 12)
    pdf.drawCentredString(width / 2, y, "Doctor Appointment Scheduler")

    y -= 20
    pdf.line(40, y, 555, y)

    y -= 30

    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(50, y, "Bill Number :")

    pdf.setFont("Helvetica")
    pdf.drawString(150, y, str(bill.id))

    pdf.drawRightString(
        540,
        y,
        bill.created_at.strftime("%d-%m-%Y")
    )

    y -= 30

    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(50, y, "Patient")

    pdf.setFont("Helvetica")
    pdf.drawString(
        150,
        y,
        appointment.patient.user.get_full_name()
        or appointment.patient.user.username
    )

    y -= 22

    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(50, y, "Doctor")

    pdf.setFont("Helvetica")
    pdf.drawString(
        150,
        y,
        f"Dr. {appointment.doctor.user.get_full_name()}"
    )

    y -= 22

    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(50, y, "Department")

    pdf.setFont("Helvetica")
    pdf.drawString(
        150,
        y,
        appointment.doctor.department.department_name
    )

    y -= 22

    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(50, y, "Appointment Date")

    pdf.setFont("Helvetica")
    pdf.drawString(
        150,
        y,
        appointment.appointment_date.strftime("%d-%m-%Y")
    )

    y -= 35

    pdf.line(40, y, 555, y)

    y -= 25

    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(60, y, "Description")

    pdf.drawRightString(520, y, "Amount")

    y -= 20

    pdf.line(40, y, 555, y)

    pdf.setFont("Helvetica", 11)

    y -= 25

    pdf.drawString(60, y, "Consultation Fee")
    pdf.drawRightString(520, y, f"Rs. {bill.consultation_fee}")

    y -= 22

    pdf.drawString(60, y, "Medicine Cost")
    pdf.drawRightString(520, y, f"Rs. {bill.medicine_cost}")

    y -= 22

    pdf.drawString(60, y, "Lab Test Cost")
    pdf.drawRightString(520, y, f"Rs. {bill.lab_test_cost}")

    y -= 22

    pdf.drawString(60, y, "GST")
    pdf.drawRightString(520, y, f"Rs. {bill.gst}")

    y -= 22

    pdf.drawString(60, y, "Discount")
    pdf.drawRightString(520, y, f"- Rs. {bill.discount}")

    y -= 25

    pdf.line(40, y, 555, y)

    y -= 30

    pdf.setFont("Helvetica-Bold", 14)

    pdf.drawString(60, y, "Total Amount")

    pdf.drawRightString(
        520,
        y,
        f"Rs. {bill.total_amount}"
    )

    y -= 30

    pdf.drawString(
        60,
        y,
        f"Payment Status : {bill.payment_status}"
    )

    y -= 80

    pdf.line(350, y, 520, y)

    y -= 15

    pdf.drawString(
        390,
        y,
        "Authorized Signature"
    )

    pdf.showPage()

    pdf.save()

    return response
def bill_create(request):

    if request.method == "POST":

        form = BillForm(request.POST)

        if form.is_valid():

            bill = form.save()

            messages.success(
                request,
                "Bill Created Successfully."
            )

            return redirect(
                "bill_detail",
                pk=bill.id
            )

    else:

        form = BillForm()

    return render(
        request,
        "billing/bill_form.html",
        {
            "form": form,
            "is_update": False,
        }
    )
@login_required
def my_bills(request):

    patient = getattr(
        request.user,
        "patient_profile",
        None
    )

    if not patient:

        messages.error(
            request,
            "Only patients can access this page."
        )

        return redirect("dashboard")

    bills = (
        Bill.objects.select_related(
            "appointment",
            "appointment__doctor__user",
            "appointment__doctor__department",
        )
        .filter(
            appointment__patient=patient
        )
        .order_by("-created_at")
    )

    search = request.GET.get("search")

    if search:

        bills = bills.filter(

            Q(
                appointment__doctor__user__first_name__icontains=search
            )

            |

            Q(
                appointment__doctor__user__last_name__icontains=search
            )

            |

            Q(
                payment_status__icontains=search
            )

        )

    return render(

        request,

        "billing/my_bills.html",

        {

            "bills": bills,

            "search": search,

        },

    )

@login_required
def bill_detail(request, pk):

    bill = get_object_or_404(

        Bill.objects.select_related(

            "appointment",

            "appointment__patient__user",

            "appointment__doctor__user",

            "appointment__doctor__department",

        ),

        pk=pk,

    )

    if (

        request.user.role == "PATIENT"

        and

        bill.appointment.patient != request.user.patient_profile

    ):

        messages.error(

            request,

            "Access Denied."

        )

        return redirect("my_bills")

    return render(

        request,

        "billing/bill_detail.html",

        {

            "bill": bill,

            "appointment": bill.appointment,

            "doctor": bill.appointment.doctor,

            "patient": bill.appointment.patient,

        },

    )