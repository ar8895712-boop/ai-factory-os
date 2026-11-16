# ==============================================================
# ml/failure_classifier.py — AI4I 2020 Failure Classification
# ==============================================================
"""
Binary failure classification for predictive maintenance using UCI AI4I 2020.

Rules Enforced:
1. Drop UDI, Product ID, and failure sub-type flags (TWF, HDF, PWF, OSF, RNF)
   to prevent catastrophic label leakage.
2. Stratified 70/15/15 split on 'Machine failure'.
3. Fit scaler and OneHotEncoder on TRAIN only.
4. Address extreme class imbalance (~3.4% failure rate) via scale_pos_weight.
5. Decision threshold tuned on VALIDATION split to maximize F1 score.
6. Evaluation reporting on TEST: F1, Precision, Recall, PR-AUC, Confusion Matrix.
   (Never reports raw Accuracy as primary metric due to class imbalance).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Tuple

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.metrics import (
    auc,
    confusion_matrix,
    f1_score,
    precision_recall_curve,
    precision_score,
    recall_score,
)
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder, StandardScaler
import xgboost as xgb

from ml.data_loader import load_ai4i

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MODELS_DIR = PROJECT_ROOT / "data" / "models"
MODELS_DIR.mkdir(parents=True, exist_ok=True)

MODEL_PATH = MODELS_DIR / "failure_model.pkl"
PREPROCESSOR_PATH = MODELS_DIR / "failure_preprocessor.pkl"
CONFIG_PATH = MODELS_DIR / "failure_config.json"

LEAKAGE_COLS = ["UDI", "Product ID", "TWF", "HDF", "PWF", "OSF", "RNF"]
NUMERIC_FEATURES = [
    "Air temperature [K]",
    "Process temperature [K]",
    "Rotational speed [rpm]",
    "Torque [Nm]",
    "Tool wear [min]",
]
CATEGORICAL_FEATURES = ["Type"]
TARGET_COL = "Machine failure"


def prepare_ai4i_data() -> Tuple[
    np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, ColumnTransformer
]:
    """
    Splits AI4I 2020 stratified into Train (70%), Val (15%), Test (15%).
    Fits ColumnTransformer on TRAIN only.
    """
    df = load_ai4i()

    # Drop leakage columns
    cols_to_drop = [c for c in LEAKAGE_COLS if c in df.columns]
    clean_df = df.drop(columns=cols_to_drop)

    X = clean_df.drop(columns=[TARGET_COL])
    y = clean_df[TARGET_COL].values.astype(int)

    failure_rate = float(np.mean(y) * 100)
    print(f"📊 [AI4I 2020] Cleaned features: {list(X.columns)}")
    print(f"   Total samples: {len(df)} | Failure rate: {failure_rate:.2f}% (imbalanced)")

    # 1. First split: 70% Train, 30% Temp (Val + Test)
    X_train_raw, X_temp, y_train, y_temp = train_test_split(
        X, y, test_size=0.30, stratify=y, random_state=42
    )

    # 2. Second split: 15% Val, 15% Test
    X_val_raw, X_test_raw, y_val, y_test = train_test_split(
        X_temp, y_temp, test_size=0.50, stratify=y_temp, random_state=42
    )

    # Fit preprocessor ONLY on training set
    preprocessor = ColumnTransformer(
        transformers=[
            ("num", StandardScaler(), NUMERIC_FEATURES),
            ("cat", OneHotEncoder(drop="first", sparse_output=False), CATEGORICAL_FEATURES),
        ]
    )
    preprocessor.fit(X_train_raw)

    # Transform splits
    X_train = preprocessor.transform(X_train_raw)
    X_val = preprocessor.transform(X_val_raw)
    X_test = preprocessor.transform(X_test_raw)

    print(f"📐 [AI4I Preprocessed Splits]:")
    print(f"   X_train : {X_train.shape} (failures: {int(np.sum(y_train))})")
    print(f"   X_val   : {X_val.shape}   (failures: {int(np.sum(y_val))})")
    print(f"   X_test  : {X_test.shape}  (failures: {int(np.sum(y_test))})")

    # Save fitted preprocessor
    joblib.dump(preprocessor, PREPROCESSOR_PATH)
    return X_train, y_train, X_val, y_val, X_test, y_test, preprocessor


def tune_decision_threshold(
    model: xgb.XGBClassifier, X_val: np.ndarray, y_val: np.ndarray
) -> Tuple[float, float]:
    """
    Sweeps decision threshold on VALIDATION set to find threshold that maximizes F1.
    """
    probs = model.predict_proba(X_val)[:, 1]
    precisions, recalls, thresholds = precision_recall_curve(y_val, probs)

    best_f1 = 0.0
    best_thresh = 0.50

    for thresh in thresholds:
        preds = (probs >= thresh).astype(int)
        score = f1_score(y_val, preds, zero_division=0)
        if score > best_f1:
            best_f1 = float(score)
            best_thresh = float(thresh)

    print(f"🎯 [Threshold Tuning on Val]: Best Threshold = {best_thresh:.3f} (Val F1 = {best_f1:.4f})")
    return best_thresh, best_f1


def train_failure_classifier() -> Dict[str, float]:
    """
    Full training pipeline for failure classifier with threshold tuning.
    """
    X_train, y_train, X_val, y_val, X_test, y_test, preprocessor = prepare_ai4i_data()

    # Calculate scale_pos_weight to counteract imbalance: negative_samples / positive_samples
    neg_count = int(np.sum(y_train == 0))
    pos_count = int(np.sum(y_train == 1))
    scale_pos_weight = neg_count / max(1, pos_count)
    print(f"⚖️ scale_pos_weight = {scale_pos_weight:.2f} ({neg_count} neg / {pos_count} pos)")

    model = xgb.XGBClassifier(
        n_estimators=250,
        max_depth=4,
        learning_rate=0.05,
        scale_pos_weight=scale_pos_weight,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
        eval_metric="logloss",
        early_stopping_rounds=20,
    )

    model.fit(
        X_train,
        y_train,
        eval_set=[(X_val, y_val)],
        verbose=False,
    )

    # Tune threshold on validation set
    optimal_thresh, val_f1 = tune_decision_threshold(model, X_val, y_val)

    # Evaluate on TEST set with optimal threshold
    test_probs = model.predict_proba(X_test)[:, 1]
    test_preds = (test_probs >= optimal_thresh).astype(int)

    precision, recall, _ = precision_recall_curve(y_test, test_probs)
    pr_auc = float(auc(recall, precision))
    f1 = float(f1_score(y_test, test_preds, zero_division=0))
    prec = float(precision_score(y_test, test_preds, zero_division=0))
    rec = float(recall_score(y_test, test_preds, zero_division=0))
    cm = confusion_matrix(y_test, test_preds).tolist()

    print("\n📊 [Test Set Evaluation Results - Failure Classifier]:")
    print(f"   F1 Score   : {f1:.4f}")
    print(f"   Precision  : {prec:.4f}")
    print(f"   Recall     : {rec:.4f}")
    print(f"   PR-AUC     : {pr_auc:.4f}")
    print(f"   Confusion Matrix: TN={cm[0][0]}, FP={cm[0][1]}, FN={cm[1][0]}, TP={cm[1][1]}")

    # Save artifacts
    joblib.dump(model, MODEL_PATH)

    config = {
        "optimal_threshold": optimal_thresh,
        "val_f1": val_f1,
        "test_f1": f1,
        "test_precision": prec,
        "test_recall": rec,
        "test_pr_auc": pr_auc,
        "confusion_matrix": cm,
    }
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)

    print(f"💾 Model and config saved to {MODEL_PATH.name} and {CONFIG_PATH.name}")
    return config

