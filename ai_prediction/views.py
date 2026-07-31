from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from appointments.models import Appointment


@login_required
def risk_dashboard(request):
    high_risk = Appointment.objects.filter(
        risk_level="HIGH", status__in=["Pending", "Confirmed"]
    ).select_related("patient", "doctor__user")

    all_scored = Appointment.objects.exclude(risk_level="").select_related(
        "patient", "doctor__user"
    )

    return render(request, "ai_prediction/risk_dashboard.html", {
        "high_risk": high_risk,
        "all_scored": all_scored,
    })