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

CATEGORICAL_COLUMNS = ["gender", "department", "appointment_weekday", "appointment_time"]


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

    probability = MODEL.predict_proba(df)[0][1]

    if probability >= 0.60:
        level = "HIGH"
    elif probability >= THRESHOLD:
        level = "MEDIUM"
    else:
        level = "LOW"

    return round(float(probability), 4), level