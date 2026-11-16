# ==============================================================
# ml/rul_models.py — RUL Regression Models (XGBoost, 1D-CNN, LSTM)
# ==============================================================
"""
Implements Remaining Useful Life (RUL) estimation architectures:
1. NASA Scoring Function calculation.
2. XGBoost regressor baseline on 56 engineered window features.
3. PyTorch 1D-CNN sequence regressor with early stopping.
4. PyTorch LSTM / GRU sequence regressor with early stopping.
5. Strict evaluation on Validation and Test sets.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, List, Tuple

import joblib
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset
import xgboost as xgb

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MODELS_DIR = PROJECT_ROOT / "data" / "models"
MODELS_DIR.mkdir(parents=True, exist_ok=True)


# ── NASA Scoring Function ─────────────────────────────────────────────

def compute_nasa_score(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """
    Computes the asymmetric NASA Prognostics evaluation metric.
    Let d = y_pred - y_true:
      d < 0 (early prediction) : exp(-d / 13) - 1
      d >= 0 (late prediction) : exp(d / 10) - 1
    Total Score = sum(penalties)

    Why asymmetric?
    A late prediction is far more dangerous in industrial machinery
    (unexpected failure during operation) than an early prediction
    (scheduled maintenance performed slightly earlier than necessary).
    """
    d = y_pred - y_true
    penalties = np.where(d < 0, np.exp(-d / 13.0) - 1.0, np.exp(d / 10.0) - 1.0)
    return float(np.sum(penalties))


def compute_rmse(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Computes Root Mean Squared Error."""
    return float(np.sqrt(np.mean((y_pred - y_true) ** 2)))


# ── PyTorch Neural Network Architectures ──────────────────────────────

class CNN1DRegressor(nn.Module):
    """
    1D-Convolutional Neural Network for temporal sensor sequences.
    Input shape: (batch_size, in_channels=15, seq_len=30)
    """

    def __init__(self, in_channels: int = 15, seq_len: int = 30):
        super().__init__()
        self.in_channels = in_channels
        self.seq_len = seq_len
        self.features = nn.Sequential(
            nn.Conv1d(in_channels, 32, kernel_size=3, padding=1),
            nn.BatchNorm1d(32),
            nn.ReLU(),
            nn.MaxPool1d(kernel_size=2),  # (batch, 32, 15)

            nn.Conv1d(32, 64, kernel_size=3, padding=1),
            nn.BatchNorm1d(64),
            nn.ReLU(),
            nn.AdaptiveAvgPool1d(1),      # (batch, 64, 1)
        )
        self.regressor = nn.Sequential(
            nn.Flatten(),
            nn.Linear(64, 32),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(32, 1),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # If input is (batch, seq_len, channels), transpose to (batch, channels, seq_len)
        if x.dim() == 3 and x.shape[1] == self.seq_len:
            x = x.transpose(1, 2)
        feats = self.features(x)
        out = self.regressor(feats)
        return out.squeeze(-1)


class LSTMRegressor(nn.Module):
    """
    Stacked LSTM for sequential degradation patterns.
    Input shape: (batch_size, seq_len=30, input_size=15)
    """

    def __init__(self, input_size: int = 15, hidden_size: int = 64, num_layers: int = 2):
        super().__init__()
        self.lstm = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True,
            dropout=0.2 if num_layers > 1 else 0.0,
        )
        self.regressor = nn.Sequential(
            nn.Linear(hidden_size, 32),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(32, 1),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        lstm_out, _ = self.lstm(x)       # (batch, seq_len, hidden_size)
        last_step = lstm_out[:, -1, :]   # take final cycle representation
        out = self.regressor(last_step)
        return out.squeeze(-1)


# ── Training Helpers ──────────────────────────────────────────────────

def train_xgboost(
    X_train_tab: np.ndarray,
    y_train: np.ndarray,
    X_val_tab: np.ndarray,
    y_val: np.ndarray,
    seed: int = 42,
) -> xgb.XGBRegressor:
    """Trains an XGBoost Regressor baseline."""
    print("\n🌲 [Training XGBoost RUL Regressor]...")
    print(f"   X_train_tab shape : {X_train_tab.shape}")
    print(f"   X_val_tab shape   : {X_val_tab.shape}")

    model = xgb.XGBRegressor(
        n_estimators=300,
        max_depth=5,
        learning_rate=0.03,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=seed,
        n_jobs=-1,
        early_stopping_rounds=25,
        eval_metric="rmse",
    )
    model.fit(
        X_train_tab,
        y_train,
        eval_set=[(X_val_tab, y_val)],
        verbose=False,
    )
    # Save model
    save_path = MODELS_DIR / "xgboost_rul.pkl"
    joblib.dump(model, save_path)
    print(f"✅ XGBoost RUL model saved to {save_path.name}")
    return model


def train_pytorch_model(
    model: nn.Module,
    model_name: str,
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_val: np.ndarray,
    y_val: np.ndarray,
    epochs: int = 40,
    batch_size: int = 128,
    lr: float = 0.001,
    patience: int = 8,
) -> nn.Module:
    """
    Trains a PyTorch neural network with early stopping based on validation RMSE.
    """
    print(f"\n🧠 [Training PyTorch {model_name}]...")
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)

    train_dataset = TensorDataset(torch.from_numpy(X_train), torch.from_numpy(y_train))
    val_dataset = TensorDataset(torch.from_numpy(X_val), torch.from_numpy(y_val))

    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False)

    criterion = nn.MSELoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=lr, weight_decay=1e-4)

    best_val_rmse = float("inf")
    best_weights = None
    patience_counter = 0

    for epoch in range(1, epochs + 1):
        model.train()
        train_loss = 0.0
        for batch_x, batch_y in train_loader:
            batch_x, batch_y = batch_x.to(device), batch_y.to(device)
            optimizer.zero_grad()
            preds = model(batch_x)
            loss = criterion(preds, batch_y)
            loss.backward()
            optimizer.step()
            train_loss += loss.item() * len(batch_y)

        # Validation
        model.eval()
        val_loss = 0.0
        with torch.no_grad():
            for batch_x, batch_y in val_loader:
                batch_x, batch_y = batch_x.to(device), batch_y.to(device)
                preds = model(batch_x)
                loss = criterion(preds, batch_y)
                val_loss += loss.item() * len(batch_y)

        val_rmse = float(np.sqrt(val_loss / len(val_dataset)))

        if val_rmse < best_val_rmse:
            best_val_rmse = val_rmse
            best_weights = {k: v.cpu().clone() for k, v in model.state_dict().items()}
            patience_counter = 0
        else:
            patience_counter += 1

        if epoch % 5 == 0 or patience_counter == 0:
            print(f"   Epoch {epoch:2d}/{epochs} | Val RMSE: {val_rmse:.2f} (best: {best_val_rmse:.2f})")

        if patience_counter >= patience:
            print(f"   🛑 Early stopping at epoch {epoch}. Best Val RMSE: {best_val_rmse:.2f}")
            break

    if best_weights is not None:
        model.load_state_dict(best_weights)

    save_path = MODELS_DIR / f"{model_name.lower()}_rul.pt"
    torch.save(model.state_dict(), save_path)
    print(f"✅ Saved best {model_name} model to {save_path.name}")
    return model
