from django.contrib.auth.decorators import login_required
from django.shortcuts import render,redirect,get_object_or_404
from django.contrib import messages
from django.db.models import Sum
from django.http import HttpResponse
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
import uuid
from django.contrib import messages
from django.utils import timezone
from .models import Payment
from .forms import PaymentForm
from billing.models import Bill
from django.db.models import Sum, Q

@login_required
def payment_list(request):

    if request.user.role == "ADMIN":

        payments = Payment.objects.select_related(
            "bill",
            "bill__appointment",
            "bill__appointment__patient__user",
            "bill__appointment__doctor__user",
            "bill__appointment__doctor__department",
        )

    elif request.user.role == "PATIENT":

        payments = Payment.objects.select_related(
            "bill",
            "bill__appointment",
            "bill__appointment__doctor__user",
            "bill__appointment__doctor__department",
        ).filter(
            bill__appointment__patient=request.user.patient_profile
        )

    else:

        return redirect("dashboard")

    # -----------------------------
    # Search
    # -----------------------------

    search = request.GET.get("search")

    if search:

        payments = payments.filter(
            Q(transaction_id__icontains=search)
            |
            Q(receipt_number__icontains=search)
        )

    # -----------------------------
    # Method Filter
    # -----------------------------

    method = request.GET.get("method")

    if method:

        payments = payments.filter(
            payment_method=method
        )

    # -----------------------------
    # Status Filter
    # -----------------------------

    status = request.GET.get("status")

    if status:

        payments = payments.filter(
            payment_status=status
        )

    payments = payments.order_by("-payment_date")

    # -----------------------------
    # Dashboard Cards
    # -----------------------------

    total_payments = payments.count()

    successful_payments = payments.filter(
        payment_status="Success"
    ).count()

    total_amount = (
        payments.filter(
            payment_status="Success"
        ).aggregate(
            total=Sum("amount")
        )["total"] or 0
    )

    today = timezone.localdate()

    today_payments = payments.filter(
        payment_date__date=today
    ).count()

    return render(
        request,
        "payments/payment_list.html",
        {
            "payments": payments,

            "total_payments": total_payments,

            "successful_payments": successful_payments,

            "total_amount": total_amount,

            "today_payments": today_payments,

            "search": search,

            "method": method,

            "status": status,
        }
    )
@login_required
def payment_detail(request,pk):

    payment=get_object_or_404(
        Payment.objects.select_related(
            "bill",
            "bill__appointment",
            "bill__appointment__patient__user",
            "bill__appointment__doctor__user",
            "bill__appointment__doctor__department",
        ),
        pk=pk
    )

    if request.user.role=="PATIENT":

        if payment.bill.appointment.patient!=request.user.patient_profile:

            messages.error(
                request,
                "Access Denied."
            )

            return redirect(
                "payment_list"
            )

    elif request.user.role!="ADMIN":

        messages.error(
            request,
            "Access Denied."
        )

        return redirect(
            "dashboard"
        )

    return render(
        request,
        "payments/payment_detail.html",
        {
            "payment":payment,
            "bill":payment.bill,
            "appointment":payment.bill.appointment,
            "doctor":payment.bill.appointment.doctor,
            "patient":payment.bill.appointment.patient,
        }
    )
@login_required
def payment_create(request, bill_id):

    if request.user.role not in ["ADMIN", "PATIENT"]:

        messages.error(
            request,
            "Access Denied."
        )

        return redirect("dashboard")

    bill = get_object_or_404(
        Bill.objects.select_related(
            "appointment",
            "appointment__patient__user",
            "appointment__doctor__user",
            "appointment__doctor__department",
        ),
        pk=bill_id
    )

    # Patient can pay only his own bill
    if request.user.role == "PATIENT":

        if bill.appointment.patient != request.user.patient_profile:

            messages.error(
                request,
                "Access Denied."
            )

            return redirect("bill_list")

    # One Bill -> One Payment
    if hasattr(bill, "payment"):

        messages.warning(
            request,
            "Payment already exists."
        )

        if request.user.role == "PATIENT":
            return redirect("my_payments")

        return redirect(
            "payment_detail",
            pk=bill.payment.id
        )

    if request.method == "POST":

        form = PaymentForm(request.POST)

        if form.is_valid():

            payment = form.save(commit=False)

            payment.bill = bill
            payment.amount = bill.total_amount
            payment.transaction_id = uuid.uuid4().hex[:12].upper()
            payment.receipt_number = f"RCPT-{bill.id:05d}"

            payment.received_by = (
                request.user.get_full_name()
                or request.user.username
            )

            payment.save()

            # Update Bill Status
            if payment.payment_status == "Success":
                bill.payment_status = "Paid"
            else:
                bill.payment_status = "Pending"

            bill.save(update_fields=["payment_status"])

            # Send Email
            try:

                from django.core.mail import send_mail

                send_mail(

                    subject="Payment Successful",

                    message=f"""
Dear {bill.appointment.patient.user.get_full_name()},

Your payment has been completed successfully.

---------------------------------------

Receipt No :
{payment.receipt_number}

Transaction ID :
{payment.transaction_id}

Amount :
₹ {payment.amount}

Payment Method :
{payment.payment_method}

Status :
{payment.payment_status}

---------------------------------------

Thank you.

AI Hospital
Doctor Appointment Scheduler
""",

                    from_email=None,

                    recipient_list=[
                        bill.appointment.patient.user.email
                    ],

                    fail_silently=True,

                )

            except Exception:
                pass

            messages.success(
                request,
                "Payment Created Successfully."
            )

            # Redirect
            if request.user.role == "PATIENT":
                return redirect("my_payments")

            return redirect(
                "payment_detail",
                pk=payment.id
            )

    else:

        form = PaymentForm(
            initial={
                "payment_status": "Success",
            }
        )

    return render(
        request,
        "payments/payment_form.html",
        {
            "form": form,
            "bill": bill,
            "is_update": False,
        }
    )
@login_required
def payment_update(request, pk):

    if request.user.role != "ADMIN":

        messages.error(
            request,
            "Only Admin can update payment."
        )

        return redirect("dashboard")

    payment = get_object_or_404(
        Payment.objects.select_related(
            "bill",
            "bill__appointment",
            "bill__appointment__patient__user",
            "bill__appointment__doctor__user",
            "bill__appointment__doctor__department",
        ),
        pk=pk
    )

    bill = payment.bill

    if request.method == "POST":

        form = PaymentForm(
            request.POST,
            instance=payment
        )

        if form.is_valid():

            payment = form.save(commit=False)

            if payment.payment_status == "Success":

                bill.payment_status = "Paid"

            else:

                bill.payment_status = "Pending"

            bill.save()

            payment.save()

            messages.success(
                request,
                "Payment Updated Successfully."
            )

            return redirect(
                "payment_detail",
                pk=payment.id
            )

    else:

        form = PaymentForm(
            instance=payment
        )

    return render(
        request,
        "payments/payment_form.html",
        {
            "form": form,
            "payment": payment,
            "bill": bill,
            "is_update": True,
        }
    )
@login_required
def payment_delete(request,pk):

    if request.user.role!="ADMIN":

        messages.error(
            request,
            "Only Admin can delete payment."
        )

        return redirect(
            "dashboard"
        )

    payment=get_object_or_404(
        Payment.objects.select_related(
            "bill",
            "bill__appointment",
            "bill__appointment__patient__user",
            "bill__appointment__doctor__user",
        ),
        pk=pk
    )

    bill=payment.bill

    if request.method=="POST":

        payment.delete()

        bill.payment_status = "Pending"

        bill.save(
            update_fields=[
                "payment_status"
            ]
        )

        messages.success(
            request,
            "Payment Deleted Successfully."
        )

        return redirect(
            "payment_list"
        )

    return render(
        request,
        "payments/payment_confirm_delete.html",
        {
            "payment":payment,
            "bill":bill,
        }
    )
@login_required
def my_payments(request):

    if request.user.role != "PATIENT":

        messages.error(
            request,
            "Access Denied."
        )

        return redirect(
            "dashboard"
        )

    patient = request.user.patient_profile

    payments = (
        Payment.objects
        .select_related(
            "bill",
            "bill__appointment",
            "bill__appointment__doctor__user",
            "bill__appointment__doctor__department",
        )
        .filter(
            bill__appointment__patient=patient
        )
        .order_by("-payment_date")
    )

    search = request.GET.get("search")

    if search:

        payments = payments.filter(
            transaction_id__icontains=search
        )

    method = request.GET.get("method")

    if method:

        payments = payments.filter(
            payment_method=method
        )

    status = request.GET.get("status")

    if status:

        payments = payments.filter(
            payment_status=status
        )

    total_paid = payments.filter(
        payment_status="Success"
    ).aggregate(
        total=Sum("amount")
    )["total"] or 0

    return render(
        request,
        "payments/my_payments.html",
        {
            "payments": payments,
            "total_paid": total_paid,
            "search": search,
            "method": method,
            "status": status,
        }
    )
@login_required
def download_receipt(request, pk):

    payment = get_object_or_404(
        Payment.objects.select_related(
            "bill",
            "bill__appointment",
            "bill__appointment__patient__user",
            "bill__appointment__doctor__user",
            "bill__appointment__doctor__department",
        ),
        pk=pk
    )

    if request.user.role == "PATIENT":

        if payment.bill.appointment.patient != request.user.patient_profile:

            messages.error(
                request,
                "Access Denied."
            )

            return redirect("dashboard")

    elif request.user.role != "ADMIN":

        messages.error(
            request,
            "Access Denied."
        )

        return redirect("dashboard")

    response = HttpResponse(
        content_type="application/pdf"
    )

    response["Content-Disposition"] = (
        f'attachment; filename="Receipt_{payment.id}.pdf"'
    )

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
        180,
        y,
        "AI HOSPITAL"
    )

    y -= 25

    pdf.setFont(
        "Helvetica",
        11
    )
    pdf.drawString(
        135,
        y,
        "Doctor Appointment Scheduler"
    )

    y -= 30

    pdf.line(
        40,
        y,
        560,
        y
    )

    y -= 25

    pdf.setFont(
        "Helvetica-Bold",
        13
    )
    pdf.drawString(
        40,
        y,
        "PAYMENT RECEIPT"
    )

    y -= 30

    pdf.setFont(
        "Helvetica",
        11
    )

    pdf.drawString(
        40,
        y,
        f"Receipt No : {payment.receipt_number}"
    )

    y -= 20

    pdf.drawString(
        40,
        y,
        f"Transaction ID : {payment.transaction_id}"
    )

    y -= 20

    pdf.drawString(
        40,
        y,
        f"Patient : {payment.bill.appointment.patient.user.get_full_name()
or
payment.bill.appointment.patient.user.username}"
    )

    y -= 20

    pdf.drawString(
        40,
        y,
        f"Doctor : Dr. {payment.bill.appointment.doctor.user.get_full_name()
or
payment.bill.appointment.doctor.user.username}"
    )

    y -= 20

    pdf.drawString(
        40,
        y,
        f"Department : {payment.bill.appointment.doctor.department.department_name}"
    )

    y -= 20

    pdf.drawString(
        40,
        y,
        f"Bill Amount : ₹ {payment.bill.total_amount}"
    )

    y -= 20

    pdf.drawString(
        40,
        y,
        f"Paid Amount : ₹ {payment.amount}"
    )

    y -= 20

    pdf.drawString(
        40,
        y,
        f"Payment Method : {payment.payment_method}"
    )

    y -= 20

    pdf.drawString(
        40,
        y,
        f"Payment Status : {payment.payment_status}"
    )

    y -= 20

    pdf.drawString(
        40,
        y,
        f"Payment Date : {payment.payment_date.strftime('%d-%m-%Y %I:%M %p')}"
    )

    y -= 20

    pdf.drawString(
        40,
        y,
        f"Received By : {payment.received_by}"
    )

    y -= 20

    pdf.drawString(
        40,
        y,
        f"Remarks : {payment.remarks or '-'}"
    )

    y -= 70

    pdf.line(
        360,
        y,
        520,
        y
    )

    y -= 15

    pdf.drawString(
        385,
        y,
        "Authorized Signature"
    )

    pdf.showPage()

    pdf.save()

    return response