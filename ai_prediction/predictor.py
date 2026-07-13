import joblib
import pandas as pd
import os
from django.conf import settings

MODEL = joblib.load(
    os.path.join(settings.BASE_DIR, "ml_model", "noshow_model.pkl")
)

ENCODERS = joblib.load(
    os.path.join(settings.BASE_DIR, "ml_model", "encoders.pkl")
)

THRESHOLD = 0.70


def predict_no_show(data):

    df = pd.DataFrame([data])

    for col in [
        "gender",
        "department",
        "appointment_weekday",
        "appointment_time",
    ]:

        df[col] = ENCODERS[col].transform(df[col])

    probability = MODEL.predict_proba(df)[0][1]

    if probability >= THRESHOLD:
        level = "HIGH"

    elif probability >= 0.40:
        level = "MEDIUM"

    else:
        level = "LOW"

    return probability, level