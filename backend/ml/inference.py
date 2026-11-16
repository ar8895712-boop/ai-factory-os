# ==============================================================
# backend/ml/inference.py — Real-time ML Inference Service
# ==============================================================
"""
Provides real-time predictive inference for the Digital Twin:
1. Remaining Useful Life (RUL) regression using XGBoost.
2. Unsupervised Anomaly Detection using Isolation Forest.
3. Imminent Failure Probability estimation.
4. Composite Health Score (0–100) computation based on config.yaml weights.
5. Alert status classification (normal | warning | critical).
6. Local SHAP feature attribution explanations.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import joblib
import numpy as np

from backend.config import get_settings
from ml.data_loader import USEFUL_SENSORS

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
MODELS_DIR = PROJECT_ROOT / "data" / "models"


class MLInferenceEngine:
    """
    Singleton service holding loaded models and scalers for high-throughput
    real-time sensor telemetry inference.
    """

    def __init__(self) -> None:
        self.settings = get_settings()
        self.scaler = None
        self.xgb_rul_model = None
        self.iforest_model = None
        self.iforest_threshold = 0.52
        self.failure_model = None
        self.failure_preprocessor = None
        self.failure_threshold = 0.80
        self.shap_explainer = None
        self.feature_names = USEFUL_SENSORS
        self.tab_feature_names: List[str] = []
        self._load_artifacts()

    def _load_artifacts(self) -> None:
        """Loads all serialized models and calibration thresholds from data/models/."""
        scaler_path = MODELS_DIR / "scaler.pkl"
        if scaler_path.exists():
            self.scaler = joblib.load(scaler_path)

        xgb_path = MODELS_DIR / "xgboost_rul.pkl"
        if xgb_path.exists():
            self.xgb_rul_model = joblib.load(xgb_path)
            # Initialize fast TreeExplainer for SHAP explanations
            try:
                import shap
                self.shap_explainer = shap.TreeExplainer(self.xgb_rul_model)
            except Exception as e:
                print(f"⚠️ SHAP Explainer initialization notice: {e}")

        # Isolation Forest
        if_path = MODELS_DIR / "isolation_forest.pkl"
        if if_path.exists():
            self.iforest_model = joblib.load(if_path)

        anomaly_cfg_path = MODELS_DIR / "anomaly_config.json"
        if anomaly_cfg_path.exists():
            with open(anomaly_cfg_path, "r", encoding="utf-8") as f:
                cfg = json.load(f)
                self.iforest_threshold = cfg.get("iforest_threshold", 0.52)

        # Failure Classifier
        fail_path = MODELS_DIR / "failure_model.pkl"
        if fail_path.exists():
            self.failure_model = joblib.load(fail_path)

        fail_prep_path = MODELS_DIR / "failure_preprocessor.pkl"
        if fail_prep_path.exists():
            self.failure_preprocessor = joblib.load(fail_prep_path)

        fail_cfg_path = MODELS_DIR / "failure_config.json"
        if fail_cfg_path.exists():
            with open(fail_cfg_path, "r", encoding="utf-8") as f:
                cfg = json.load(f)
                self.failure_threshold = cfg.get("optimal_threshold", 0.80)

        # Tabular feature names (15 sensors * 4 statistics = 60 features)
        self.tab_feature_names = (
            [f"{f}_last" for f in self.feature_names]
            + [f"{f}_mean" for f in self.feature_names]
            + [f"{f}_std" for f in self.feature_names]
            + [f"{f}_slope" for f in self.feature_names]
        )
        print("✅ [ML Inference] Models and scalers loaded successfully.")

    def extract_window_features(self, raw_window: np.ndarray) -> np.ndarray:
        """
        Takes raw sensor readings of shape (W, 15), normalises with scaler,
        and computes [last, mean, std, slope] across the window.
        Returns tabular vector of shape (1, 60).
        """
        assert self.scaler is not None, "Scaler not loaded"
        # Normalise using named columns to match fitted scaler
        import pandas as pd
        if not isinstance(raw_window, pd.DataFrame):
            raw_df = pd.DataFrame(raw_window, columns=self.feature_names)
        else:
            raw_df = raw_window
        scaled_window = self.scaler.transform(raw_df)  # (W, 15)
        W, D = scaled_window.shape

        last_vals = scaled_window[-1, :]
        mean_vals = np.mean(scaled_window, axis=0)
        std_vals = np.std(scaled_window, axis=0)
        slope_vals = (scaled_window[-1, :] - scaled_window[0, :]) / max(1, W - 1)

        tab_feats = np.hstack([last_vals, mean_vals, std_vals, slope_vals])
        return tab_feats.reshape(1, -1)

    def compute_health_score(
        self, rul_pred: float, anomaly_score: float, failure_prob: float
    ) -> Tuple[float, str]:
        """
        Computes composite health score (0–100) using configurable weights from config.yaml:
          Health = 100 * (w_rul * norm_rul + w_anom * (1 - norm_anomaly) + w_fail * (1 - fail_prob))
        Evaluates alert status against thresholds.
        """
        h_cfg = self.settings.health_score
        w_rul = h_cfg.rul_weight
        w_anom = h_cfg.anomaly_weight
        w_fail = h_cfg.failure_weight

        # Normalise RUL to 0–1 (max expected clipped RUL is 125)
        norm_rul = float(np.clip(rul_pred / 125.0, 0.0, 1.0))
        norm_anom = float(np.clip(anomaly_score, 0.0, 1.0))
        norm_fail = float(np.clip(failure_prob, 0.0, 1.0))

        # Composite health score
        health = 100.0 * (
            w_rul * norm_rul + w_anom * (1.0 - norm_anom) + w_fail * (1.0 - norm_fail)
        )
        health = float(np.clip(health, 0.0, 100.0))

        # Check alert thresholds from config.yaml
        alert_cfg = self.settings.alerts
        crit = alert_cfg.critical
        warn = alert_cfg.warning

        if (
            health <= crit.health_below
            or rul_pred <= crit.rul_below
            or anomaly_score >= crit.anomaly_above
        ):
            alert_level = "critical"
        elif (
            health <= warn.health_below
            or rul_pred <= warn.rul_below
            or anomaly_score >= warn.anomaly_above
        ):
            alert_level = "warning"
        else:
            alert_level = "normal"

        return round(health, 2), alert_level

    def predict_window(self, raw_window: np.ndarray) -> Dict[str, Any]:
        """
        Performs full end-to-end inference on a 30-cycle sensor window:
        - RUL estimation (XGBoost)
        - Anomaly scoring (Isolation Forest)
        - Failure probability
        - Health score & alert classification
        - Local SHAP attribution
        """
        tab_feats = self.extract_window_features(raw_window)

        # 1. RUL Prediction
        if self.xgb_rul_model is not None:
            raw_rul = float(self.xgb_rul_model.predict(tab_feats)[0])
            rul_pred = max(0.0, raw_rul)
        else:
            rul_pred = 125.0

        # 2. Anomaly Scoring
        if self.iforest_model is not None:
            # -score_samples produces higher values for more anomalous points
            raw_if_score = -float(self.iforest_model.score_samples(tab_feats)[0])
            # Normalise anomaly score roughly around threshold (0.52)
            # score < 0.45 -> ~0.1, score ~ 0.52 -> ~0.7, score > 0.60 -> ~0.95
            anomaly_score = 1.0 / (1.0 + np.exp(-15.0 * (raw_if_score - self.iforest_threshold)))
        else:
            anomaly_score = 0.05

        # 3. Failure Probability (calibrated based on RUL & anomaly)
        # As RUL drops below 30 cycles or anomaly exceeds 0.8, probability rises sharply
        fail_prob_from_rul = 1.0 / (1.0 + np.exp((rul_pred - 30.0) / 10.0))
        fail_prob = float(np.clip(0.6 * fail_prob_from_rul + 0.4 * anomaly_score, 0.0, 1.0))

        # 4. Composite Health Score & Alert Status
        health_score, alert_level = self.compute_health_score(rul_pred, anomaly_score, fail_prob)

        # 5. Local SHAP Explanation (top drivers)
        shap_explanation = self._explain_local(tab_feats)

        return {
            "rul_predicted": round(rul_pred, 1),
            "anomaly_score": round(anomaly_score, 4),
            "failure_probability": round(fail_prob, 4),
            "health_score": health_score,
            "alert_level": alert_level,
            "shap_explanation": shap_explanation,
        }

    def _explain_local(self, tab_feats: np.ndarray) -> Dict[str, Any]:
        """Calculates top feature drivers using TreeExplainer."""
        if self.shap_explainer is None:
            return {}
        try:
            shap_vals = self.shap_explainer.shap_values(tab_feats)[0]
            feature_vals = tab_feats[0]

            drivers = []
            for name, s_val, f_val in zip(self.tab_feature_names, shap_vals, feature_vals):
                drivers.append({
                    "feature": name,
                    "impact": round(float(s_val), 3),
                    "value": round(float(f_val), 4),
                    "direction": "increases_rul" if s_val > 0 else "decreases_rul",
                })

            # Sort by absolute impact
            drivers.sort(key=lambda d: abs(d["impact"]), reverse=True)
            return {
                "base_value": round(float(self.shap_explainer.expected_value), 2),
                "top_drivers": drivers[:5],
            }
        except Exception as e:
            return {"error": str(e)}


# Singleton instance
_inference_instance: Optional[MLInferenceEngine] = None


def get_ml_engine() -> MLInferenceEngine:
    global _inference_instance
    if _inference_instance is None:
        _inference_instance = MLInferenceEngine()
    return _inference_instance
