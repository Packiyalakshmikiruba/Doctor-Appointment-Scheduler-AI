"""
appointments/risk.py
AI Prediction step — called right after an appointment is booked.
"""

import os

import joblib
from django.conf import settings

ML_MODEL_PATH = os.path.join(settings.BASE_DIR, "ml_model", "noshow_model.pkl")
ENCODERS_PATH = os.path.join(settings.BASE_DIR, "ml_model", "encoders.pkl")
OPERATING_THRESHOLD = 0.70  # must match train_model.py

_model = joblib.load(ML_MODEL_PATH)
_encoders = joblib.load(ENCODERS_PATH)


def _safe_encode(column: str, value: str) -> int:
    le = _encoders[column]
    try:
        return int(le.transform([str(value)])[0])
    except ValueError:
        return 0


def predict_and_save_risk(appointment) -> str:
    patient = appointment.patient
    doctor = appointment.doctor  # hospital.models.Doctor instance

    features = [
        patient.age,
        _safe_encode("gender", patient.gender),
        _safe_encode("department", doctor.department.department_name),
        appointment.lead_time_days,
        appointment.appointment_date.weekday(),
        _safe_encode("appointment_time", appointment.time_bucket),
        int(appointment.sms_reminder_sent),
        appointment.prior_visits,
        appointment.prior_noshows,
        appointment.history_noshow_ratio,
        appointment.distance_from_clinic,
    ]

    risk_prob = _model.predict_proba([features])[0][1]

    if risk_prob >= OPERATING_THRESHOLD:
        risk_level = "HIGH"
    elif risk_prob >= 0.4:
        risk_level = "MEDIUM"
    else:
        risk_level = "LOW"

    appointment.risk_score = round(float(risk_prob), 4)
    appointment.risk_level = risk_level
    appointment.save(update_fields=["risk_score", "risk_level"])

    return risk_level
