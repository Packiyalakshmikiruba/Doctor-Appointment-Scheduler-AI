from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from accounts.decorators import role_required


@login_required
@role_required(["ADMIN"])
def admin_dashboard(request):

    return render(
        request,
        "dashboard/admin_dashboard.html"
    )


@login_required
@role_required(["DOCTOR"])
def doctor_dashboard(request):

    return render(
        request,
        "dashboard/doctor_dashboard.html"
    )


@login_required
@role_required(["PATIENT"])
def patient_dashboard(request):

    return render(
        request,
        "dashboard/patient_dashboard.html"
    )
