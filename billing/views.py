from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from .models import Bill
from .forms import BillForm
from appointments.models import Appointment


def bill_create(request):
    if request.method == "POST":
        form = BillForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("bill_list")
    else:
        form = BillForm()

    return render(request, "billing/bill_form.html", {"form": form})


def get_consultation_fee(request, pk):
    appointment = get_object_or_404(Appointment, pk=pk)
    return JsonResponse({
        "fee": str(appointment.doctor.consultation_fee),
        "patient_name": str(appointment.patient),
        "doctor_name": f"Dr. {appointment.doctor.user.get_full_name() or appointment.doctor.user.username}",
    })


def bill_list(request):
    bills = Bill.objects.select_related("appointment__patient", "appointment__doctor__user")
    return render(request, "billing/bill_list.html", {"bills": bills})


def mark_paid(request, pk):
    bill = get_object_or_404(Bill, pk=pk)
    bill.payment_status = "PAID"
    bill.save()
    return redirect("bill_list")