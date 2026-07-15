"""
Regenerates the training dataset using the EXACT departments
that exist in the Django hospital.Department table.
"""

import numpy as np
import pandas as pd

np.random.seed(42)
N = 1500

DEPARTMENTS = ["Cardiology", "Dermatology", "General Medicine", "Neurology", "Orthopedics"]
DEPT_WEIGHTS = [0.22, 0.18, 0.28, 0.16, 0.16]

age = np.random.randint(1, 90, N)
gender = np.random.choice(["Male", "Female"], N, p=[0.48, 0.52])
department = np.random.choice(DEPARTMENTS, N, p=DEPT_WEIGHTS)

lead_time_days = np.clip(np.random.exponential(8, N).astype(int), 0, 60)
appointment_weekday = np.random.randint(0, 7, N)
appointment_time = np.random.choice(["Morning", "Afternoon", "Evening"], N, p=[0.4, 0.4, 0.2])

sms_reminder_sent = np.random.choice([0, 1], N, p=[0.3, 0.7])
distance_from_clinic = np.round(np.random.exponential(6, N), 1)

prior_visits = np.random.poisson(3, N)
prior_noshows = np.array([np.random.binomial(v, 0.15) if v > 0 else 0 for v in prior_visits])
history_noshow_ratio = np.where(prior_visits > 0, np.round(prior_noshows / np.maximum(prior_visits, 1), 3), 0.0)

logit = (
    -1.6
    + 0.045 * lead_time_days
    - 0.9 * sms_reminder_sent
    + 1.8 * history_noshow_ratio
    - 0.015 * age
    + 0.35 * (appointment_weekday >= 5).astype(int)
    + 0.02 * distance_from_clinic
    + np.random.normal(0, 0.5, N)
)
prob = 1 / (1 + np.exp(-logit))
no_show = np.random.binomial(1, prob)

df = pd.DataFrame({
    "patient_id": [f"P{100000+i}" for i in range(N)],
    "age": age,
    "gender": gender,
    "department": department,
    "lead_time_days": lead_time_days,
    "appointment_weekday": appointment_weekday,
    "appointment_time": appointment_time,
    "sms_reminder_sent": sms_reminder_sent,
    "prior_visits": prior_visits,
    "prior_noshows": prior_noshows,
    "history_noshow_ratio": history_noshow_ratio,
    "distance_from_clinic": distance_from_clinic,
    "no_show": no_show,
})

df.to_csv("data/appointments_dataset_v4.csv", index=False)
print(f"Generated {len(df)} rows with departments: {DEPARTMENTS}")
print(f"No-show rate: {df['no_show'].mean():.2%}")