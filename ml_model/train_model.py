import json
import warnings
import joblib
import numpy as np
import pandas as pd

from sklearn.model_selection import (
    train_test_split,
    RandomizedSearchCV,
)

from sklearn.preprocessing import LabelEncoder

from sklearn.linear_model import LogisticRegression

from sklearn.ensemble import RandomForestClassifier

from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    confusion_matrix,
    classification_report,
)

warnings.filterwarnings("ignore")

try:
    from imblearn.over_sampling import SMOTE
    HAS_SMOTE = True
except ImportError:
    HAS_SMOTE = False

try:
    from xgboost import XGBClassifier
    HAS_XGB = True
except ImportError:
    HAS_XGB = False


DATA_PATH = "data/appointments_dataset_v4.csv"

MODEL_PATH = "noshow_model.pkl"

ENCODER_PATH = "encoders.pkl"

METRICS_PATH = "model_metrics.json"

THRESHOLD = 0.35


ID_COLUMN = "patient_id"

TARGET_COLUMN = "no_show"


CATEGORICAL_COLUMNS = [

    "gender",

    "department",

    "appointment_weekday",

    "appointment_time",

]


FEATURE_COLUMNS = [

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
def load_dataset():

    print("Loading Dataset...")

    df = pd.read_csv(DATA_PATH)

    print(df.head())

    print(df.shape)

    print(df.info())

    return df
def preprocess(df):

    if ID_COLUMN in df.columns:

        df = df.drop(columns=[ID_COLUMN])

    df = df.drop_duplicates()

    df = df.dropna()

    encoders = {}

    for column in CATEGORICAL_COLUMNS:

        encoder = LabelEncoder()

        df[column] = encoder.fit_transform(

            df[column].astype(str)

        )

        encoders[column] = encoder

    X = df[FEATURE_COLUMNS]

    y = df[TARGET_COLUMN]

    return X, y, encoders
def split_dataset(X, y):

    X_train, X_test, y_train, y_test = train_test_split(

        X,

        y,

        test_size=0.20,

        random_state=42,

        stratify=y

    )

    print()

    print("Training Records :", len(X_train))

    print("Testing Records :", len(X_test))

    return X_train, X_test, y_train, y_test
def balance_dataset(

    X_train,

    y_train,

):

    if HAS_SMOTE:

        print()

        print("Applying SMOTE...")

        smote = SMOTE(

            random_state=42

        )

        X_train, y_train = smote.fit_resample(

            X_train,

            y_train

        )

        print(pd.Series(y_train).value_counts())

    return X_train, y_train
def train_logistic(

    X_train,

    y_train,

):

    print()

    print("Training Logistic Regression...")

    model = LogisticRegression(

        max_iter=1000

    )

    model.fit(

        X_train,

        y_train

    )

    return model
RF_PARAMETERS = {

    "n_estimators": [

        100,

        200,

        300,

        400,

    ],

    "max_depth": [

        4,

        6,

        8,

        10,

        None,

    ],

    "min_samples_split": [

        2,

        5,

        10,

    ],

    "min_samples_leaf": [

        1,

        2,

        4,

    ],

    "max_features": [

        "sqrt",

        "log2",

    ],

}
RF_PARAMETERS = {

    "n_estimators": [

        100,

        200,

        300,

        400,

    ],

    "max_depth": [

        4,

        6,

        8,

        10,

        None,

    ],

    "min_samples_split": [

        2,

        5,

        10,

    ],

    "min_samples_leaf": [

        1,

        2,

        4,

    ],

    "max_features": [

        "sqrt",

        "log2",

    ],

}
def train_random_forest(

    X_train,

    y_train,

):

    print()

    print("Training Random Forest...")

    search = RandomizedSearchCV(

        estimator=RandomForestClassifier(

            random_state=42

        ),

        param_distributions=RF_PARAMETERS,

        n_iter=20,

        cv=5,

        scoring="roc_auc",

        random_state=42,

        n_jobs=-1,

    )

    search.fit(

        X_train,

        y_train

    )

    print()

    print(search.best_params_)

    return search.best_estimator_
def train_xgboost(

    X_train,

    y_train,

):

    if not HAS_XGB:

        return None

    parameters = {

        "n_estimators": [

            100,

            200,

            300,

            400,

        ],

        "learning_rate": [

            0.01,

            0.05,

            0.1,

            0.2,

        ],

        "max_depth": [

            3,

            4,

            5,

            6,

        ],

        "subsample": [

            0.8,

            1.0,

        ],

        "colsample_bytree": [

            0.8,

            1.0,

        ],

    }

    search = RandomizedSearchCV(

        estimator=XGBClassifier(

            random_state=42,

            eval_metric="logloss",

        ),

        param_distributions=parameters,

        n_iter=20,

        cv=5,

        scoring="roc_auc",

        random_state=42,

        n_jobs=-1,

    )

    search.fit(

        X_train,

        y_train

    )

    print()

    print(search.best_params_)

    return search.best_estimator_
def evaluate_model(
    model,
    X_test,
    y_test,
    model_name,
):
    y_probability = model.predict_proba(X_test)[:, 1]

    roc_auc = roc_auc_score(
        y_test,
        y_probability,
    )

    y_prediction = (
        y_probability >= THRESHOLD
    ).astype(int)

    accuracy = accuracy_score(
        y_test,
        y_prediction,
    )

    precision = precision_score(
        y_test,
        y_prediction,
        zero_division=0,
    )

    recall = recall_score(
        y_test,
        y_prediction,
        zero_division=0,
    )

    f1 = f1_score(
        y_test,
        y_prediction,
        zero_division=0,
    )

    confusion = confusion_matrix(
        y_test,
        y_prediction,
    )

    print()
    print("=" * 60)
    print(model_name)
    print("=" * 60)
    print(f"ROC AUC   : {roc_auc:.4f}")
    print(f"Accuracy  : {accuracy:.4f}")
    print(f"Precision : {precision:.4f}")
    print(f"Recall    : {recall:.4f}")
    print(f"F1 Score  : {f1:.4f}")

    print()
    print("Confusion Matrix")
    print(confusion)

    print()
    print("Classification Report")
    print(
        classification_report(
            y_test,
            y_prediction,
            zero_division=0,
        )
    )

    return {
        "model": model_name,
        "roc_auc": round(roc_auc, 4),
        "accuracy": round(accuracy, 4),
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1_score": round(f1, 4),
        "confusion_matrix": confusion.tolist(),
    }

def save_model(

    model,

    encoders,

    metrics,

):

    joblib.dump(

        model,

        MODEL_PATH,

    )

    joblib.dump(

        encoders,

        ENCODER_PATH,

    )

    with open(

        METRICS_PATH,

        "w",

    ) as file:

        json.dump(

            metrics,

            file,

            indent=4,

        )

    print()

    print("Saved Model")

    print("Saved Encoders")

    print("Saved Metrics")
def main():

    dataset = load_dataset()

    X, y, encoders = preprocess(dataset)

    X_train, X_test, y_train, y_test = split_dataset(X, y)

    X_train, y_train = balance_dataset(X_train, y_train)

    # ---------------- Logistic Regression ----------------

    logistic = train_logistic(
        X_train,
        y_train,
    )

    # ---------------- Random Forest ----------------

    random_forest = train_random_forest(
        X_train,
        y_train,
    )

    # ---------------- XGBoost ----------------

    xgboost_model = None

    if HAS_XGB:
        xgboost_model = train_xgboost(
            X_train,
            y_train,
        )

    # ---------------- Evaluation ----------------

   # ---------------- Evaluation ----------------

    results = []

    logistic_metrics = evaluate_model(
        logistic,
        X_test,
        y_test,
        "Logistic Regression",
    )
    results.append(logistic_metrics)

    rf_metrics = evaluate_model(
        random_forest,
        X_test,
        y_test,
        "Random Forest",
    )
    results.append(rf_metrics)

    candidates = [
        (logistic, logistic_metrics),
        (random_forest, rf_metrics),
    ]

    if xgboost_model is not None:

        xgb_metrics = evaluate_model(
            xgboost_model,
            X_test,
            y_test,
            "XGBoost",
        )

        results.append(xgb_metrics)
        candidates.append((xgboost_model, xgb_metrics))

    # Select by RECALL (spec priority: "capturing maximum no-shows")
    best_model, best_metrics = max(candidates, key=lambda c: c[1]["recall"])

    print()
    print(f">>> Selected model: {best_metrics['model']} "
          f"(Recall={best_metrics['recall']}, ROC-AUC={best_metrics['roc_auc']})")

    # ---------------- Save ----------------

    save_model(
        best_model,
        encoders,
        {
            "best_model": type(best_model).__name__,
            "threshold": THRESHOLD,
            "feature_order": FEATURE_COLUMNS,
            "results": results,
        },
    )


if __name__ == "__main__":
    main()