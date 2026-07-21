import os
import joblib
import pandas as pd
from django.conf import settings

MODEL = joblib.load(
    os.path.join(settings.BASE_DIR, "ml_model", "noshow_model.pkl")
)

ENCODERS = joblib.load(
    os.path.join(settings.BASE_DIR, "ml_model", "encoders.pkl")
)

THRESHOLD = 0.35

# FIX: "appointment_weekday" was listed here, but it is a plain integer
# (0-6 from .weekday()), not a categorical string -- train_model.py never
# created a LabelEncoder for it. ENCODERS["appointment_weekday"] does not
# exist, so every call used to raise KeyError, which appointments/signals.py
# silently swallowed -- meaning risk_score/risk_level were NEVER set via
# the signal path (only BookingService's separate, correct prediction call
# happened to mask this). Only truly categorical (string) columns belong here.
CATEGORICAL_COLUMNS = ["gender", "department", "appointment_time"]

# Must match the exact column order used in train_model.py's FEATURE_COLS.
FEATURE_ORDER = [
    "age",
    "gender",
    "department",
    "lead_time_days",
    "appointment_weekday",
    "appointment_time",
    "sms_reminder_sent",
    "prior_visits",
    "prior_noshows",
    "history_noshow_ratio",
    "distance_from_clinic",
]


def safe_encode(column, value):
    encoder = ENCODERS[column]
    value = str(value)
    if value in encoder.classes_:
        return encoder.transform([value])[0]
    print(f"WARNING: unseen value '{value}' for column '{column}', using fallback")
    return encoder.transform([encoder.classes_[0]])[0]


def predict_no_show(data):
    df = pd.DataFrame([data])

    for col in CATEGORICAL_COLUMNS:
        df[col] = df[col].apply(lambda v: safe_encode(col, v))

    # FIX: enforce the exact column order the model was trained on --
    # a plain dict->DataFrame does not guarantee this, and a silently
    # wrong column order gives silently wrong predictions.
    df = df[FEATURE_ORDER]

    probability = MODEL.predict_proba(df)[0][1]

    if probability >= 0.60:
        level = "HIGH"
    elif probability >= THRESHOLD:
        level = "MEDIUM"
    else:
        level = "LOW"

    return round(float(probability), 4), level
