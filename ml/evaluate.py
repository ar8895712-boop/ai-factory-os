# ==============================================================
# ml/evaluate.py — Full ML Pipeline Runner & Evaluation Table
# ==============================================================
"""
Master script for Phase 1 ML Pipeline:
1. Loads C-MAPSS and executes leakage-checked 70/15/15 engine split.
2. Fits MinMaxScaler strictly on TRAIN engines.
3. Generates 30-cycle sliding windows and tabular summary features.
4. Trains & evaluates RUL models (XGBoost, 1D-CNN, LSTM).
5. Trains & evaluates AI4I Failure Classifier (XGBoost).
6. Trains & evaluates Anomaly Detectors (Isolation Forest, LSTM Autoencoder).
7. Generates SHAP global plots and Neural Saliency maps.
8. Outputs the official Evaluation Table:
   Columns: Model | Dataset | Split | RMSE | NASA Score | F1 | PR-AUC
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List

import numpy as np
import pandas as pd

# Set Matplotlib cache dir before import
PROJECT_ROOT = Path(__file__).resolve().parent.parent
os.environ["MPLCONFIGDIR"] = str(PROJECT_ROOT / "data")

from ml.anomaly_detector import (
    evaluate_anomaly_detection,
    train_isolation_forest,
    train_lstm_autoencoder,
)
from ml.data_loader import USEFUL_SENSORS, get_cmapss_splits
from ml.explainability import XGBSHAPExplainer, compute_neural_saliency
from ml.failure_classifier import train_failure_classifier
from ml.leakage_check import check_engine_leakage
from ml.preprocessing import CMapssPreprocessor
from ml.rul_models import (
    CNN1DRegressor,
    LSTMRegressor,
    compute_nasa_score,
    compute_rmse,
    train_pytorch_model,
    train_xgboost,
)

EVAL_TABLE_PATH = PROJECT_ROOT / "data" / "evaluation_table.csv"
EVAL_MD_PATH = PROJECT_ROOT / "data" / "evaluation_table.md"


def run_full_ml_pipeline() -> pd.DataFrame:
    print("=" * 70)
    print("  🏭 AI Factory OS — Phase 1 ML Training & Evaluation Pipeline")
    print("=" * 70)

    # ──────────────────────────────────────────────────────────────────
    # Step 1: Load C-MAPSS FD001 and apply Engine-Level Splits
    # ──────────────────────────────────────────────────────────────────
    print("\n[Step 1/7] Loading C-MAPSS and splitting by Engine ID (70/15/15)...")
    train_df, val_df, demo_df, test_df, rul_df = get_cmapss_splits()

    # Assert zero leakage among the 100 train engines (70 Train, 15 Val, 15 Demo)
    check_engine_leakage(
        train_df["engine_id"].unique(),
        val_df["engine_id"].unique(),
        demo_df["engine_id"].unique(),
    )

    # ──────────────────────────────────────────────────────────────────
    # Step 2: Fit Scaler on TRAIN ONLY & Generate Sliding Windows
    # ──────────────────────────────────────────────────────────────────
    print("\n[Step 2/7] Normalising sensors and building sliding windows (size=30)...")
    preprocessor = CMapssPreprocessor(window_size=30, feature_cols=USEFUL_SENSORS)
    preprocessor.fit(train_df)

    train_scaled = preprocessor.transform_df(train_df)
    val_scaled = preprocessor.transform_df(val_df)
    test_scaled = preprocessor.transform_df(test_df)

    # Create sequence windows for deep learning
    X_train_seq, y_train, _ = preprocessor.create_sequence_windows(train_scaled)
    X_val_seq, y_val, _ = preprocessor.create_sequence_windows(val_scaled)
    # For test evaluation: strictly extract the LAST window of each test engine
    X_test_last_seq, test_engine_ids = preprocessor.extract_test_last_windows(test_scaled)
    y_test_true = rul_df["true_rul"].values.astype(np.float32)

    # Create tabular summary features for XGBoost
    X_train_tab, tab_names = preprocessor.extract_tabular_features(X_train_seq, USEFUL_SENSORS)
    X_val_tab, _ = preprocessor.extract_tabular_features(X_val_seq, USEFUL_SENSORS)
    X_test_last_tab, _ = preprocessor.extract_tabular_features(X_test_last_seq, USEFUL_SENSORS)

    print(f"📐 [Processed Window Shapes]:")
    print(f"   X_train_seq  : {X_train_seq.shape} | y_train : {y_train.shape}")
    print(f"   X_val_seq    : {X_val_seq.shape}   | y_val   : {y_val.shape}")
    print(f"   X_test_last  : {X_test_last_seq.shape} (100 test engines) | y_test: {y_test_true.shape}")
    print(f"   X_train_tab  : {X_train_tab.shape} (56 engineered features)")

    # ──────────────────────────────────────────────────────────────────
    # Step 3: Train RUL Regression Models (XGBoost, 1D-CNN, LSTM)
    # ──────────────────────────────────────────────────────────────────
    print("\n[Step 3/7] Training RUL Regression Models...")
    eval_rows: List[Dict[str, Any]] = []

    # Model 1: XGBoost Regressor
    xgb_model = train_xgboost(X_train_tab, y_train, X_val_tab, y_val)
    xgb_val_preds = xgb_model.predict(X_val_tab)
    xgb_test_preds = xgb_model.predict(X_test_last_tab)

    xgb_val_rmse = compute_rmse(y_val, xgb_val_preds)
    xgb_val_nasa = compute_nasa_score(y_val, xgb_val_preds)
    xgb_test_rmse = compute_rmse(y_test_true, xgb_test_preds)
    xgb_test_nasa = compute_nasa_score(y_test_true, xgb_test_preds)

    eval_rows.append({
        "Model": "XGBoost (Window Feats)",
        "Dataset": "C-MAPSS FD001",
        "Split": "Validation",
        "RMSE": f"{xgb_val_rmse:.2f}",
        "NASA Score": f"{xgb_val_nasa:.1f}",
        "F1": "-",
        "PR-AUC": "-",
    })
    eval_rows.append({
        "Model": "XGBoost (Window Feats)",
        "Dataset": "C-MAPSS FD001",
        "Split": "Test",
        "RMSE": f"{xgb_test_rmse:.2f}",
        "NASA Score": f"{xgb_test_nasa:.1f}",
        "F1": "-",
        "PR-AUC": "-",
    })

    # Model 2: PyTorch 1D-CNN
    n_features = X_train_seq.shape[2]
    cnn_model = CNN1DRegressor(in_channels=n_features, seq_len=30)
    cnn_model = train_pytorch_model(
        cnn_model, "CNN1D", X_train_seq, y_train, X_val_seq, y_val, epochs=25
    )
    cnn_model.eval()
    import torch
    with torch.no_grad():
        cnn_val_preds = cnn_model(torch.from_numpy(X_val_seq)).cpu().numpy()
        cnn_test_preds = cnn_model(torch.from_numpy(X_test_last_seq)).cpu().numpy()

    cnn_val_rmse = compute_rmse(y_val, cnn_val_preds)
    cnn_val_nasa = compute_nasa_score(y_val, cnn_val_preds)
    cnn_test_rmse = compute_rmse(y_test_true, cnn_test_preds)
    cnn_test_nasa = compute_nasa_score(y_test_true, cnn_test_preds)

    eval_rows.append({
        "Model": "1D-CNN",
        "Dataset": "C-MAPSS FD001",
        "Split": "Validation",
        "RMSE": f"{cnn_val_rmse:.2f}",
        "NASA Score": f"{cnn_val_nasa:.1f}",
        "F1": "-",
        "PR-AUC": "-",
    })
    eval_rows.append({
        "Model": "1D-CNN",
        "Dataset": "C-MAPSS FD001",
        "Split": "Test",
        "RMSE": f"{cnn_test_rmse:.2f}",
        "NASA Score": f"{cnn_test_nasa:.1f}",
        "F1": "-",
        "PR-AUC": "-",
    })

    # Model 3: PyTorch LSTM
    lstm_model = LSTMRegressor(input_size=n_features, hidden_size=64, num_layers=2)
    lstm_model = train_pytorch_model(
        lstm_model, "LSTM", X_train_seq, y_train, X_val_seq, y_val, epochs=25
    )
    lstm_model.eval()
    with torch.no_grad():
        lstm_val_preds = lstm_model(torch.from_numpy(X_val_seq)).cpu().numpy()
        lstm_test_preds = lstm_model(torch.from_numpy(X_test_last_seq)).cpu().numpy()

    lstm_val_rmse = compute_rmse(y_val, lstm_val_preds)
    lstm_val_nasa = compute_nasa_score(y_val, lstm_val_preds)
    lstm_test_rmse = compute_rmse(y_test_true, lstm_test_preds)
    lstm_test_nasa = compute_nasa_score(y_test_true, lstm_test_preds)

    eval_rows.append({
        "Model": "LSTM (2-Layer)",
        "Dataset": "C-MAPSS FD001",
        "Split": "Validation",
        "RMSE": f"{lstm_val_rmse:.2f}",
        "NASA Score": f"{lstm_val_nasa:.1f}",
        "F1": "-",
        "PR-AUC": "-",
    })
    eval_rows.append({
        "Model": "LSTM (2-Layer)",
        "Dataset": "C-MAPSS FD001",
        "Split": "Test",
        "RMSE": f"{lstm_test_rmse:.2f}",
        "NASA Score": f"{lstm_test_nasa:.1f}",
        "F1": "-",
        "PR-AUC": "-",
    })

    # ──────────────────────────────────────────────────────────────────
    # Step 4: AI4I 2020 Failure Classification
    # ──────────────────────────────────────────────────────────────────
    print("\n[Step 4/7] Training AI4I 2020 Failure Classification Model...")
    ai4i_res = train_failure_classifier()

    eval_rows.append({
        "Model": "XGBoost Classifier",
        "Dataset": "AI4I 2020",
        "Split": "Validation",
        "RMSE": "-",
        "NASA Score": "-",
        "F1": f"{ai4i_res['val_f1']:.4f}",
        "PR-AUC": "-",
    })
    eval_rows.append({
        "Model": "XGBoost Classifier",
        "Dataset": "AI4I 2020",
        "Split": "Test",
        "RMSE": "-",
        "NASA Score": "-",
        "F1": f"{ai4i_res['test_f1']:.4f}",
        "PR-AUC": f"{ai4i_res['test_pr_auc']:.4f}",
    })

    # ──────────────────────────────────────────────────────────────────
    # Step 5: Semi-supervised Anomaly Detection
    # ──────────────────────────────────────────────────────────────────
    print("\n[Step 5/7] Training Anomaly Detectors on healthy windows only...")
    # Extract healthy windows: cycle <= 50% of engine max_cycle (represented by y_train >= 60 in clipped RUL)
    healthy_train_mask = y_train >= 90
    healthy_val_mask = y_val >= 90
    degraded_val_mask = y_val <= 20

    X_train_healthy_tab = X_train_tab[healthy_train_mask]
    X_val_healthy_tab = X_val_tab[healthy_val_mask]
    X_val_degraded_tab = X_val_tab[degraded_val_mask]

    X_train_healthy_seq = X_train_seq[healthy_train_mask]
    X_val_healthy_seq = X_val_seq[healthy_val_mask]
    X_val_degraded_seq = X_val_seq[degraded_val_mask]

    iforest, if_thresh = train_isolation_forest(X_train_healthy_tab, X_val_healthy_tab)
    autoencoder, ae_thresh = train_lstm_autoencoder(X_train_healthy_seq, X_val_healthy_seq, epochs=20)

    evaluate_anomaly_detection(
        iforest,
        if_thresh,
        autoencoder,
        ae_thresh,
        X_val_healthy_tab,
        X_val_degraded_tab,
        X_val_healthy_seq,
        X_val_degraded_seq,
    )

    # ──────────────────────────────────────────────────────────────────
    # Step 6: SHAP & Neural Saliency Explainability
    # ──────────────────────────────────────────────────────────────────
    print("\n[Step 6/7] Computing SHAP attributions and Neural Saliency...")
    shap_explainer = XGBSHAPExplainer(xgb_model, tab_names)
    # Sample 150 rows from val set for global SHAP plot
    sample_indices = np.random.RandomState(42).choice(len(X_val_tab), size=150, replace=False)
    shap_explainer.generate_global_plots(X_val_tab[sample_indices])

    # Compute saliency on 1D-CNN
    compute_neural_saliency(cnn_model, X_val_seq[:100], USEFUL_SENSORS)

    # ──────────────────────────────────────────────────────────────────
    # Step 7: Build & Export the Official Evaluation Table
    # ──────────────────────────────────────────────────────────────────
    print("\n[Step 7/7] Generating Official Evaluation Table...")
    eval_df = pd.DataFrame(eval_rows)

    eval_df.to_csv(EVAL_TABLE_PATH, index=False)

    # Format Markdown table without requiring tabulate package
    headers = list(eval_df.columns)
    col_count = len(headers)
    md_lines = [
        "# Model Evaluation Table\n",
        "| " + " | ".join(headers) + " |",
        "|" + "|".join(["---"] * col_count) + "|",
    ]
    for _, row in eval_df.iterrows():
        md_lines.append("| " + " | ".join(str(row[h]) for h in headers) + " |")

    with open(EVAL_MD_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines) + "\n")

    print("\n" + "=" * 70)
    print("🏆 OFFICIAL PHASE 1 MODEL EVALUATION TABLE")
    print("=" * 70)
    print(eval_df.to_string(index=False))
    print("=" * 70)
    print(f"💾 Saved evaluation table to:\n   - {EVAL_TABLE_PATH}\n   - {EVAL_MD_PATH}")

    return eval_df


if __name__ == "__main__":
    run_full_ml_pipeline()
