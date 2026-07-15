from django.db.models.signals import pre_save
from django.dispatch import receiver
from .models import Appointment
from ai_prediction.predictor import predict_no_show


@receiver(pre_save, sender=Appointment)
def compute_risk(sender, instance, **kwargs):
    if instance.status not in ("Pending", "Confirmed"):
        return

    patient = instance.patient
    prior_qs = patient.appointments.exclude(pk=instance.pk)
    prior_visits = prior_qs.count()
    prior_noshows = prior_qs.filter(status="No Show").count()
    history_ratio = round(prior_noshows / prior_visits, 3) if prior_visits > 0 else 0.0
    distance = float(patient.distance_from_clinic)

    # Persist onto the model fields (now real DB columns)
    instance.prior_visits = prior_visits
    instance.prior_noshows = prior_noshows
    instance.history_noshow_ratio = history_ratio
    instance.distance_from_clinic = distance

    data = {
        "age": patient.age,
        "gender": patient.gender,
        "department": instance.doctor.department.department_name,
        "lead_time_days": instance.lead_time_days,
        "appointment_weekday": instance.appointment_date.weekday(),
        "appointment_time": instance.time_bucket,
        "sms_reminder_sent": int(instance.sms_reminder_sent),
        "prior_visits": prior_visits,
        "prior_noshows": prior_noshows,
        "history_noshow_ratio": history_ratio,
        "distance_from_clinic": distance,
    }

    try:
        score, level = predict_no_show(data)
        instance.risk_score = score
        instance.risk_level = level
    except Exception as e:
        print("Risk prediction failed:", e)