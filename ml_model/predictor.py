import os
import json
import joblib
import pandas as pd

from django.conf import settings


# -----------------------------
# Load Model
# -----------------------------

MODEL_PATH = os.path.join(
    settings.BASE_DIR,
    "ml_model",
    "noshow_model.pkl"
)

ENCODER_PATH = os.path.join(
    settings.BASE_DIR,
    "ml_model",
    "encoders.pkl"
)

METRICS_PATH = os.path.join(
    settings.BASE_DIR,
    "ml_model",
    "model_metrics.json"
)


model = joblib.load(MODEL_PATH)

encoders = joblib.load(ENCODER_PATH)

with open(METRICS_PATH, "r") as file:
    metrics = json.load(file)

THRESHOLD = metrics["threshold"]

FEATURE_ORDER = metrics["feature_order"]


# -----------------------------
# Prediction Function
# -----------------------------

def predict_no_show(data):

    sample = pd.DataFrame([data])

    # Encode categorical columns

    categorical_columns = [
        "gender",
        "department",
        "appointment_time",
    ]

    for column in categorical_columns:

        sample[column] = encoders[column].transform(
            sample[column].astype(str)
        )

    sample = sample[FEATURE_ORDER]

    probability = model.predict_proba(sample)[0][1]

    if probability >= THRESHOLD:

        level = "HIGH"

    elif probability >= 0.40:

        level = "MEDIUM"

    else:

        level = "LOW"

    return probability, level