"""
train_model.py
No-Show Risk Predictor - Model Training Script
------------------------------------------------
Trains a binary classifier to predict patient appointment no-shows.

Pipeline:
1. Load dataset
2. Preprocess (encode categoricals, drop identifier column)
3. Train/test split
4. Handle class imbalance with SMOTE
5. Train Logistic Regression (baseline), Random Forest, and XGBoost
6. Hyperparameter tuning with RandomizedSearchCV (Random Forest + XGBoost)
7. Evaluate at multiple thresholds + report a chosen operating threshold
8. Save the best model + encoders + threshold as files for Django to load

Run:
    pip install pandas numpy scikit-learn imbalanced-learn xgboost joblib
    python train_model.py
"""

import json
import warnings

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import RandomizedSearchCV, train_test_split
from sklearn.preprocessing import LabelEncoder

warnings.filterwarnings("ignore")

try:
    from imblearn.over_sampling import SMOTE

    HAS_SMOTE = True
except ImportError:
    HAS_SMOTE = False
    print("[WARN] imbalanced-learn not installed. Run: pip install imbalanced-learn")
    print("       Falling back to class_weight='balanced' instead of SMOTE.\n")

try:
    from xgboost import XGBClassifier

    HAS_XGB = True
except ImportError:
    HAS_XGB = False
    print("[WARN] xgboost not installed. Run: pip install xgboost")
    print("       Skipping XGBoost model, will use Random Forest as final model.\n")


DATA_PATH = "data/appointments_dataset_v4.csv"
MODEL_OUT = "noshow_model.pkl"
ENCODERS_OUT = "encoders.pkl"
METRICS_OUT = "model_metrics.json"

# Chosen operating threshold (tuned for accuracy/recall balance — see README notes).
# 0.70 gives ~87% accuracy on this dataset.
OPERATING_THRESHOLD = 0.70

# patient_id is an identifier only — never used as a model feature.
ID_COL = "patient_id"
CATEGORICAL_COLS = ["gender", "department", "appointment_time"]
FEATURE_COLS = [
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
TARGET_COL = "no_show"


def load_and_preprocess(path):
    df = pd.read_csv(path)
    if ID_COL in df.columns:
        df = df.drop(columns=[ID_COL])
    df = df.drop_duplicates().dropna(subset=FEATURE_COLS + [TARGET_COL])

    encoders = {}
    for col in CATEGORICAL_COLS:
        le = LabelEncoder()
        df[col] = le.fit_transform(df[col].astype(str))
        encoders[col] = le

    X = df[FEATURE_COLS]
    y = df[TARGET_COL]
    return X, y, encoders


def evaluate_at_threshold(y_test, y_prob, threshold):
    y_pred = (y_prob >= threshold).astype(int)
    return {
        "threshold": threshold,
        "accuracy": round(accuracy_score(y_test, y_pred), 4),
        "precision": round(precision_score(y_test, y_pred, zero_division=0), 4),
        "recall": round(recall_score(y_test, y_pred, zero_division=0), 4),
        "f1_score": round(f1_score(y_test, y_pred, zero_division=0), 4),
        "confusion_matrix": confusion_matrix(y_test, y_pred).tolist(),
    }


def evaluate(model, X_test, y_test, name):
    y_prob = model.predict_proba(X_test)[:, 1]
    auc = round(roc_auc_score(y_test, y_prob), 4)

    threshold_scan = [
        evaluate_at_threshold(y_test, y_prob, round(t, 2))
        for t in np.arange(0.3, 0.85, 0.05)
    ]
    chosen = evaluate_at_threshold(y_test, y_prob, OPERATING_THRESHOLD)

    print(f"\n===== {name} =====")
    print(f"ROC-AUC (threshold-independent): {auc}")
    print("\nThreshold scan (Accuracy / Precision / Recall / F1):")
    for row in threshold_scan:
        print(
            f"  {row['threshold']:.2f} | acc={row['accuracy']:.3f} "
            f"prec={row['precision']:.3f} rec={row['recall']:.3f} f1={row['f1_score']:.3f}"
        )
    print(f"\n--> Operating threshold {OPERATING_THRESHOLD}: {chosen}")
    print("\nClassification Report at operating threshold:")
    y_pred_final = (y_prob >= OPERATING_THRESHOLD).astype(int)
    print(classification_report(y_test, y_pred_final, zero_division=0))

    return {
        "model": name,
        "roc_auc": auc,
        "threshold_scan": threshold_scan,
        "chosen_threshold_metrics": chosen,
    }


def main():
    print("Loading and preprocessing data...")
    X, y, encoders = load_and_preprocess(DATA_PATH)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    print(f"Train size: {len(X_train)} | Test size: {len(X_test)}")
    print(f"Train no-show rate: {round(y_train.mean() * 100, 2)}%")

    # ---- Handle class imbalance ----
    if HAS_SMOTE:
        print("\nApplying SMOTE to balance training data...")
        sm = SMOTE(random_state=42)
        X_train_bal, y_train_bal = sm.fit_resample(X_train, y_train)
        print(f"After SMOTE -> class distribution:\n{pd.Series(y_train_bal).value_counts()}")
    else:
        X_train_bal, y_train_bal = X_train, y_train

    all_metrics = []

    # ---- Baseline: Logistic Regression ----
    print("\nTraining baseline Logistic Regression...")
    log_reg = LogisticRegression(max_iter=1000, class_weight=None if HAS_SMOTE else "balanced")
    log_reg.fit(X_train_bal, y_train_bal)
    all_metrics.append(evaluate(log_reg, X_test, y_test, "Logistic Regression"))

    # ---- Random Forest + RandomizedSearchCV ----
    print("\nTuning Random Forest with RandomizedSearchCV...")
    rf_param_grid = {
        "n_estimators": [100, 200, 300, 400],
        "max_depth": [4, 6, 8, 10, None],
        "min_samples_split": [2, 5, 10],
        "min_samples_leaf": [1, 2, 4],
        "max_features": ["sqrt", "log2"],
    }
    rf_search = RandomizedSearchCV(
        RandomForestClassifier(
            random_state=42, class_weight=None if HAS_SMOTE else "balanced"
        ),
        param_distributions=rf_param_grid,
        n_iter=20,
        cv=5,
        scoring="roc_auc",
        random_state=42,
        n_jobs=-1,
    )
    rf_search.fit(X_train_bal, y_train_bal)
    best_rf = rf_search.best_estimator_
    print(f"Best RF params: {rf_search.best_params_}")
    rf_metrics = evaluate(best_rf, X_test, y_test, "Random Forest (tuned)")
    all_metrics.append(rf_metrics)

    best_model = best_rf
    best_name = "Random Forest (tuned)"
    best_score = rf_metrics["roc_auc"]

    # ---- XGBoost + RandomizedSearchCV ----
    if HAS_XGB:
        print("\nTuning XGBoost with RandomizedSearchCV...")
        xgb_param_grid = {
            "n_estimators": [100, 200, 300, 400],
            "max_depth": [3, 4, 5, 6, 8],
            "learning_rate": [0.01, 0.05, 0.1, 0.2],
            "subsample": [0.7, 0.8, 1.0],
            "colsample_bytree": [0.7, 0.8, 1.0],
        }
        xgb_search = RandomizedSearchCV(
            XGBClassifier(
                random_state=42, eval_metric="logloss", use_label_encoder=False
            ),
            param_distributions=xgb_param_grid,
            n_iter=20,
            cv=5,
            scoring="roc_auc",
            random_state=42,
            n_jobs=-1,
        )
        xgb_search.fit(X_train_bal, y_train_bal)
        best_xgb = xgb_search.best_estimator_
        print(f"Best XGB params: {xgb_search.best_params_}")
        xgb_metrics = evaluate(best_xgb, X_test, y_test, "XGBoost (tuned)")
        all_metrics.append(xgb_metrics)

        if xgb_metrics["roc_auc"] > best_score:
            best_model = best_xgb
            best_name = "XGBoost (tuned)"
            best_score = xgb_metrics["roc_auc"]

    # ---- Save best model ----
    print(f"\nBest model selected: {best_name} (ROC-AUC = {best_score})")
    joblib.dump(best_model, MODEL_OUT)
    joblib.dump(encoders, ENCODERS_OUT)

    with open(METRICS_OUT, "w") as f:
        json.dump(
            {
                "best_model": best_name,
                "operating_threshold": OPERATING_THRESHOLD,
                "feature_order": FEATURE_COLS,
                "results": all_metrics,
            },
            f,
            indent=2,
        )

    print(f"\nSaved model      -> {MODEL_OUT}")
    print(f"Saved encoders   -> {ENCODERS_OUT}")
    print(f"Saved metrics    -> {METRICS_OUT}")
    print(f"\nOperating threshold saved: {OPERATING_THRESHOLD}")
    print("Use this same threshold in the Django prediction API:")
    print("    risk_prob = model.predict_proba(features)[0][1]")
    print(f"    is_high_risk = risk_prob >= {OPERATING_THRESHOLD}")
    print("\nLoad in Django with:")
    print("    model = joblib.load('noshow_model.pkl')")
    print("    encoders = joblib.load('encoders.pkl')")


if __name__ == "__main__":
    main()
