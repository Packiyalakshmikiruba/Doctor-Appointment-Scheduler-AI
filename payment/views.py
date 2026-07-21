from django.contrib.auth.decorators import login_required
from django.shortcuts import render,redirect
from .models import Payment
from django.contrib.auth.decorators import login_required
from django.shortcuts import render,get_object_or_404,redirect
from django.contrib import messages

@login_required
def payment_list(request):

    if request.user.role=="ADMIN":

        payments=Payment.objects.select_related(
            "bill",
            "bill__appointment",
            "bill__appointment__patient__user",
            "bill__appointment__doctor__user",
        ).order_by("-payment_date")

    elif request.user.role=="PATIENT":

        payments=Payment.objects.select_related(
            "bill",
            "bill__appointment",
            "bill__appointment__doctor__user",
        ).filter(
            bill__appointment__patient=request.user.patient_profile
        ).order_by("-payment_date")

    else:

        return redirect("dashboard")

    total_amount=sum(
        payment.amount
        for payment in payments
        if payment.payment_status=="Success"
    )

    return render(
        request,
        "payments/payment_list.html",
        {
            "payments":payments,
            "total_amount":total_amount,
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

            return redirect("payment_list")

    elif request.user.role!="ADMIN":

        messages.error(
            request,
            "Access Denied."
        )

        return redirect("dashboard")

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