# ==============================================================
# ml/anomaly_detector.py — Unsupervised Anomaly Detection
# ==============================================================
"""
Implements semi-supervised anomaly detection:
1. Isolation Forest on summary tabular features.
2. PyTorch LSTM Autoencoder on 3D sensor sequence windows.

Rules Enforced:
- Trained ONLY on healthy windows of TRAIN engines (first 50% of life).
- Threshold set on healthy windows of VALIDATION engines (98th percentile).
- Evaluated on late-life degraded windows (>80% life) and test engines.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Tuple

import joblib
import numpy as np
import torch
import torch.nn as nn
from sklearn.ensemble import IsolationForest
from torch.utils.data import DataLoader, TensorDataset

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MODELS_DIR = PROJECT_ROOT / "data" / "models"
MODELS_DIR.mkdir(parents=True, exist_ok=True)

IFOREST_PATH = MODELS_DIR / "isolation_forest.pkl"
AUTOENCODER_PATH = MODELS_DIR / "lstm_autoencoder.pt"
CONFIG_PATH = MODELS_DIR / "anomaly_config.json"


# ── PyTorch LSTM Autoencoder ──────────────────────────────────────────

class LSTMAutoencoder(nn.Module):
    """
    Sequence-to-sequence autoencoder for multidimensional sensor telemetry.
    Input shape: (batch_size, seq_len=30, n_features=14)
    Reconstructs healthy temporal trajectories.
    """

    def __init__(self, n_features: int = 14, hidden_dim: int = 32, seq_len: int = 30):
        super().__init__()
        self.seq_len = seq_len
        self.n_features = n_features
        self.hidden_dim = hidden_dim

        # Encoder
        self.encoder = nn.LSTM(
            input_size=n_features,
            hidden_size=hidden_dim,
            batch_first=True,
        )

        # Decoder
        self.decoder = nn.LSTM(
            input_size=hidden_dim,
            hidden_size=hidden_dim,
            batch_first=True,
        )
        self.output_layer = nn.Linear(hidden_dim, n_features)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        batch_size = x.size(0)

        # Encode: get context representation at final step
        _, (h_n, _) = self.encoder(x)  # h_n shape: (1, batch, hidden_dim)
        context = h_n.squeeze(0)       # shape: (batch, hidden_dim)

        # Repeat context across all time steps
        repeated = context.unsqueeze(1).repeat(1, self.seq_len, 1)  # (batch, seq_len, hidden_dim)

        # Decode
        dec_out, _ = self.decoder(repeated)  # (batch, seq_len, hidden_dim)
        recon = self.output_layer(dec_out)   # (batch, seq_len, n_features)
        return recon


# ── Isolation Forest Training ─────────────────────────────────────────

def train_isolation_forest(
    X_train_healthy_tab: np.ndarray,
    X_val_healthy_tab: np.ndarray,
    seed: int = 42,
) -> Tuple[IsolationForest, float]:
    """
    Trains Isolation Forest on healthy tabular features only.
    Sets anomaly score threshold using the 98th percentile on healthy validation.
    """
    print("\n🌲 [Training Isolation Forest Anomaly Detector]...")
    print(f"   Healthy train windows shape : {X_train_healthy_tab.shape}")

    # contamination='auto' fits baseline density
    model = IsolationForest(
        n_estimators=150,
        contamination=0.02,
        random_state=seed,
        n_jobs=-1,
    )
    model.fit(X_train_healthy_tab)

    # In sklearn, score_samples returns the opposite of anomaly score (higher = more normal)
    # We define anomaly_score = -score_samples so higher means more anomalous.
    val_raw_scores = -model.score_samples(X_val_healthy_tab)
    threshold = float(np.percentile(val_raw_scores, 98))

    joblib.dump(model, IFOREST_PATH)
    print(f"✅ Isolation Forest saved to {IFOREST_PATH.name} (Threshold: {threshold:.4f})")
    return model, threshold


# ── LSTM Autoencoder Training ─────────────────────────────────────────

def train_lstm_autoencoder(
    X_train_healthy_seq: np.ndarray,
    X_val_healthy_seq: np.ndarray,
    epochs: int = 35,
    batch_size: int = 64,
    lr: float = 0.002,
) -> Tuple[LSTMAutoencoder, float]:
    """
    Trains LSTM Autoencoder to reconstruct healthy temporal windows.
    Threshold is calibrated at 98th percentile of reconstruction error on healthy Val windows.
    """
    print("\n🧠 [Training LSTM Autoencoder Anomaly Detector]...")
    print(f"   Healthy train seqs shape : {X_train_healthy_seq.shape}")

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = LSTMAutoencoder(
        n_features=X_train_healthy_seq.shape[2],
        seq_len=X_train_healthy_seq.shape[1],
    ).to(device)

    train_tensor = torch.from_numpy(X_train_healthy_seq)
    val_tensor = torch.from_numpy(X_val_healthy_seq)

    loader = DataLoader(TensorDataset(train_tensor), batch_size=batch_size, shuffle=True)
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    criterion = nn.MSELoss()

    for epoch in range(1, epochs + 1):
        model.train()
        total_loss = 0.0
        for (batch_x,) in loader:
            batch_x = batch_x.to(device)
            optimizer.zero_grad()
            recon = model(batch_x)
            loss = criterion(recon, batch_x)
            loss.backward()
            optimizer.step()
            total_loss += loss.item() * len(batch_x)

        avg_loss = total_loss / len(train_tensor)
        if epoch % 10 == 0 or epoch == 1:
            print(f"   Epoch {epoch:2d}/{epochs} | Train Recon MSE: {avg_loss:.5f}")

    # Compute reconstruction errors on validation healthy data
    model.eval()
    val_errors = []
    with torch.no_grad():
        val_loader = DataLoader(TensorDataset(val_tensor), batch_size=batch_size, shuffle=False)
        for (batch_x,) in val_loader:
            batch_x = batch_x.to(device)
            recon = model(batch_x)
            # Per-sample mean squared reconstruction error across time and sensors
            mse = torch.mean((recon - batch_x) ** 2, dim=(1, 2)).cpu().numpy()
            val_errors.extend(mse)

    val_errors = np.array(val_errors)
    threshold = float(np.percentile(val_errors, 98))

    torch.save(model.state_dict(), AUTOENCODER_PATH)
    print(f"✅ LSTM Autoencoder saved to {AUTOENCODER_PATH.name} (Threshold: {threshold:.5f})")
    return model, threshold


def evaluate_anomaly_detection(
    iforest: IsolationForest,
    iforest_thresh: float,
    autoencoder: LSTMAutoencoder,
    ae_thresh: float,
    X_healthy_tab: np.ndarray,
    X_degraded_tab: np.ndarray,
    X_healthy_seq: np.ndarray,
    X_degraded_seq: np.ndarray,
) -> Dict[str, float]:
    """
    Evaluates anomaly detectors on healthy vs degraded windows.
    Degraded windows should have a significantly higher anomaly detection rate.
    """
    # 1. Isolation Forest
    if_healthy_scores = -iforest.score_samples(X_healthy_tab)
    if_degraded_scores = -iforest.score_samples(X_degraded_tab)
    if_fpr = float(np.mean(if_healthy_scores >= iforest_thresh))
    if_tpr = float(np.mean(if_degraded_scores >= iforest_thresh))

    # 2. LSTM Autoencoder
    device = next(autoencoder.parameters()).device
    autoencoder.eval()
    with torch.no_grad():
        h_recon = autoencoder(torch.from_numpy(X_healthy_seq).to(device))
        h_mse = torch.mean((h_recon - torch.from_numpy(X_healthy_seq).to(device)) ** 2, dim=(1, 2)).cpu().numpy()

        d_recon = autoencoder(torch.from_numpy(X_degraded_seq).to(device))
        d_mse = torch.mean((d_recon - torch.from_numpy(X_degraded_seq).to(device)) ** 2, dim=(1, 2)).cpu().numpy()

    ae_fpr = float(np.mean(h_mse >= ae_thresh))
    ae_tpr = float(np.mean(d_mse >= ae_thresh))

    print("\n📊 [Anomaly Detection Evaluation]:")
    print(f"   Isolation Forest -> False Alarm Rate (Healthy): {if_fpr*100:.1f}% | Anomaly Recall (Degraded): {if_tpr*100:.1f}%")
    print(f"   Autoencoder      -> False Alarm Rate (Healthy): {ae_fpr*100:.1f}% | Anomaly Recall (Degraded): {ae_tpr*100:.1f}%")

    config = {
        "iforest_threshold": iforest_thresh,
        "iforest_fpr": if_fpr,
        "iforest_tpr": if_tpr,
        "autoencoder_threshold": ae_thresh,
        "autoencoder_fpr": ae_fpr,
        "autoencoder_tpr": ae_tpr,
    }
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)

    return config

