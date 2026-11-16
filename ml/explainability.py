# ==============================================================
# ml/explainability.py — Model Explainability (SHAP & Saliency)
# ==============================================================
"""
Provides model interpretability:
1. SHAP TreeExplainer for XGBoost RUL & failure models.
   - Global feature ranking plots (summary beeswarm & bar).
   - Local per-prediction feature attribution (for Digital Twin & Factory GPT).
2. Saliency maps (gradient-based attribution) for PyTorch 1D-CNN & LSTM.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List

import numpy as np

# Set Matplotlib cache dir before import to prevent Windows permission issues
PROJECT_ROOT = Path(__file__).resolve().parent.parent
os.environ["MPLCONFIGDIR"] = str(PROJECT_ROOT / "data")

import matplotlib
matplotlib.use("Agg")  # headless backend for server & scripts
import matplotlib.pyplot as plt
import shap
import torch
import torch.nn as nn

MODELS_DIR = PROJECT_ROOT / "data" / "models"
MODELS_DIR.mkdir(parents=True, exist_ok=True)


# ── SHAP for XGBoost ──────────────────────────────────────────────────

class XGBSHAPExplainer:
    """
    Computes global and local SHAP explanations for tree-based models.
    """

    def __init__(self, model: Any, feature_names: List[str]):
        self.model = model
        self.feature_names = feature_names
        self.explainer = shap.TreeExplainer(model)

    def generate_global_plots(self, X_sample: np.ndarray, max_display: int = 15) -> None:
        """
        Generates and saves SHAP summary beeswarm and bar importance plots.
        """
        print("🔍 [SHAP] Computing TreeExplainer shap_values on sample...")
        shap_values = self.explainer(X_sample)
        shap_values.feature_names = self.feature_names

        # 1. Beeswarm summary plot
        plt.figure(figsize=(10, 6))
        shap.plots.beeswarm(shap_values, max_display=max_display, show=False)
        plt.tight_layout()
        summary_path = MODELS_DIR / "shap_summary_rul.png"
        plt.savefig(summary_path, dpi=200, bbox_inches="tight")
        plt.close("all")
        print(f"📊 Saved SHAP summary plot to {summary_path.name}")

        # 2. Bar importance plot
        plt.figure(figsize=(10, 6))
        shap.plots.bar(shap_values, max_display=max_display, show=False)
        plt.tight_layout()
        bar_path = MODELS_DIR / "shap_bar_rul.png"
        plt.savefig(bar_path, dpi=200, bbox_inches="tight")
        plt.close("all")
        print(f"📊 Saved SHAP bar importance plot to {bar_path.name}")

    def explain_single_prediction(self, x_single: np.ndarray) -> Dict[str, Any]:
        """
        Explains one machine state (single row of 56 engineered features).
        Returns top positive and negative contributors in JSON-serialisable format
        for use by the Digital Twin UI and Factory GPT.
        """
        if x_single.ndim == 1:
            x_single = x_single.reshape(1, -1)

        shap_vals = self.explainer.shap_values(x_single)[0]
        base_val = float(self.explainer.expected_value)
        feature_vals = x_single[0]

        # Pair each feature with its attribution
        impacts = []
        for name, s_val, f_val in zip(self.feature_names, shap_vals, feature_vals):
            impacts.append({
                "feature": name,
                "shap_value": float(s_val),
                "feature_value": float(f_val),
                "direction": "increases_rul" if s_val > 0 else "decreases_rul",
            })

        # Sort by absolute SHAP magnitude
        impacts.sort(key=lambda item: abs(item["shap_value"]), reverse=True)

        return {
            "base_value": base_val,
            "prediction": float(base_val + np.sum(shap_vals)),
            "top_drivers": impacts[:6],
        }


# ── Neural Saliency for PyTorch ───────────────────────────────────────

def compute_neural_saliency(
    model: nn.Module,
    X_samples: np.ndarray,
    sensor_names: List[str],
) -> Dict[str, float]:
    """
    Computes input gradient saliency |d(output)/d(input)| for 1D-CNN or LSTM.
    Averages gradient magnitudes across time steps and batches to quantify
    which physical sensors most strongly affect predictions.
    """
    print(f"🔍 [Saliency] Computing neural saliency across {len(X_samples)} samples...")
    model.eval()
    device = next(model.parameters()).device

    x_tensor = torch.from_numpy(X_samples).float().to(device)
    x_tensor.requires_grad_(True)

    preds = model(x_tensor)
    # Target gradient of sum of predictions
    preds.sum().backward()

    # Gradients shape: (batch, seq_len=30, n_sensors=14)
    grads = x_tensor.grad.detach().cpu().numpy()
    # Magnitude: average absolute gradient across samples and time steps
    importance = np.mean(np.abs(grads), axis=(0, 1))

    # Normalize to 0-100%
    total = np.sum(importance) + 1e-8
    rel_importance = {name: float((val / total) * 100) for name, val in zip(sensor_names, importance)}

    # Plot
    plt.figure(figsize=(9, 4.5))
    sorted_items = sorted(rel_importance.items(), key=lambda x: x[1], reverse=True)
    names = [k for k, _ in sorted_items]
    vals = [v for _, v in sorted_items]

    plt.bar(names, vals, color="#3b82f6", edgecolor="#1d4ed8")
    plt.ylabel("Relative Saliency (%)")
    plt.title("Sensor Importance via Neural Gradient Saliency")
    plt.xticks(rotation=45)
    plt.tight_layout()

    saliency_path = MODELS_DIR / "saliency_neural.png"
    plt.savefig(saliency_path, dpi=200, bbox_inches="tight")
    plt.close("all")
    print(f"📊 Saved Neural Saliency plot to {saliency_path.name}")

    return rel_importance

