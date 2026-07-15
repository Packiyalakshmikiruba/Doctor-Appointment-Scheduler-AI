import os
import pickle
import numpy as np
import pandas as pd
from django.conf import settings

# Load ML Model & Preprocessor
MODEL_PATH = os.path.join(settings.BASE_DIR, 'noshow_model.pkl')
PREPROCESSOR_PATH = os.path.join(settings.BASE_DIR, 'preprocessor.pkl')

def predict_noshow_risk(patient, doctor, appointment_date, sms_reminder=True):
    """
    Patient and Appointment details vechu XGBoost/ML Model moolama 
    No-Show Risk Score calculate panra function.
    """
    try:
        # Check if model files exist
        if os.path.exists(MODEL_PATH) and os.path.exists(PREPROCESSOR_PATH):
            with open(MODEL_PATH, 'rb') as f:
                model = pickle.load(f)
            with open(PREPROCESSOR_PATH, 'rb') as f:
                preprocessor = pickle.load(f)

            # Feature extraction from patient & appointment
            lead_time = (appointment_date - pd.Timestamp.now().date()).days
            lead_time = max(0, lead_time)
            
            # Create input DataFrame for ML model
            input_data = pd.DataFrame([{
                'age': getattr(patient, 'age', 30),
                'gender': getattr(patient, 'gender', 'M'),
                'department': getattr(doctor, 'department', 'General'),
                'lead_time': lead_time,
                'appointment_day': appointment_date.strftime('%A'),
                'sms_reminder': 1 if sms_reminder else 0,
                'prior_visits': getattr(patient, 'prior_visits', 1),
                'prior_noshows': getattr(patient, 'prior_noshows', 0),
                'history_noshow_ratio': getattr(patient, 'prior_noshows', 0) / max(1, getattr(patient, 'prior_visits', 1))
            }])

            # Preprocess & Predict Probability
            X_processed = preprocessor.transform(input_data)
            risk_proba = model.predict_proba(X_processed)[0][1] # Probability of No-Show (Class 1)
            risk_score = round(risk_proba * 100, 2)

            if risk_score > 60:
                risk_level = "HIGH"
            elif risk_score > 30:
                risk_level = "MEDIUM"
            else:
                risk_level = "LOW"

            return risk_score, risk_level

        else:
            # Model files ready-a illana Fallback Dummy Value
            return 25.0, "LOW"

    except Exception as e:
        print(f"ML Prediction Error: {e}")
        return 20.0, "LOW"