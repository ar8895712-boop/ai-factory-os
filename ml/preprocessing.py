# ==============================================================
# ml/preprocessing.py — Scaler & Sliding Window Preprocessor
# ==============================================================
"""
Implements:
1. Sensor normalisation using MinMaxScaler fit STRICTLY on TRAIN engines.
2. Sliding window generation (window_size=30) computed WITHIN each engine separately.
3. Feature engineering for tabular models (XGBoost):
   - Last value, Mean, Std dev, Linear slope across the 30-cycle window.
4. 3D sequence array creation for Deep Learning models (1D-CNN, LSTM/GRU):
   Shape: (num_samples, window_size=30, num_features=14).
5. Extraction of the LAST window of each test engine for test evaluation vs RUL_FD001.txt.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Tuple

import joblib
import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler

from ml.data_loader import USEFUL_SENSORS

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCALER_PATH = PROJECT_ROOT / "data" / "models" / "scaler.pkl"
WINDOW_SIZE = 30


class CMapssPreprocessor:
    """
    Manages scaling and windowing for C-MAPSS data with strict leakage prevention.
    """

    def __init__(self, window_size: int = WINDOW_SIZE, feature_cols: List[str] | None = None):
        self.window_size = window_size
        self.feature_cols = feature_cols or list(USEFUL_SENSORS)
        self.scaler = MinMaxScaler(feature_range=(0, 1))
        self.is_fitted = False

    def fit(self, train_df: pd.DataFrame) -> "CMapssPreprocessor":
        """
        Fits MinMaxScaler ONLY on the sensor columns of TRAIN engines.
        """
        self.scaler.fit(train_df[self.feature_cols])
        self.is_fitted = True

        # Save fitted scaler
        SCALER_PATH.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self.scaler, SCALER_PATH)
        print(f"✅ [Preprocessor] Scaler fit on {len(train_df)} rows and saved to {SCALER_PATH.name}")
        return self

    def transform_df(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Transforms sensor columns using the fitted scaler.
        Preserves non-sensor columns (engine_id, cycle, rul).
        """
        assert self.is_fitted, "Scaler must be fitted before transforming."
        scaled = df.copy()
        scaled[self.feature_cols] = self.scaler.transform(df[self.feature_cols])
        return scaled

    def create_sequence_windows(
        self, df: pd.DataFrame, is_test: bool = False
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Builds sliding windows (size 30) INSIDE each engine separately.
        Never crosses engine boundaries.

        Returns:
            X_seq: 3D numpy array (N, window_size=30, n_features=14)
            y: 1D numpy array (N,) of RUL values (or empty for test without labels)
            engine_cycles: 2D numpy array (N, 2) storing (engine_id, cycle) at end of window
        """
        X_list: List[np.ndarray] = []
        y_list: List[float] = []
        meta_list: List[Tuple[int, int]] = []

        grouped = df.groupby("engine_id")
        for engine_id, group in grouped:
            engine_data = group[self.feature_cols].values
            cycles = group["cycle"].values
            n_rows = len(group)

            has_rul = "rul" in group.columns
            ruls = group["rul"].values if has_rul else None

            if n_rows < self.window_size:
                # If engine has fewer than window_size cycles, pad with the first reading
                pad_len = self.window_size - n_rows
                pad_features = np.repeat(engine_data[:1, :], pad_len, axis=0)
                padded_data = np.vstack([pad_features, engine_data])
                X_list.append(padded_data)
                meta_list.append((int(engine_id), int(cycles[-1])))
                if has_rul:
                    y_list.append(float(ruls[-1]))  # type: ignore
                continue

            for start in range(n_rows - self.window_size + 1):
                end = start + self.window_size
                window = engine_data[start:end, :]
                X_list.append(window)
                meta_list.append((int(engine_id), int(cycles[end - 1])))
                if has_rul:
                    y_list.append(float(ruls[end - 1]))  # type: ignore

        X_seq = np.array(X_list, dtype=np.float32)
        y = np.array(y_list, dtype=np.float32) if y_list else np.empty(0, dtype=np.float32)
        meta = np.array(meta_list, dtype=np.int32)
        return X_seq, y, meta

    def extract_test_last_windows(self, test_df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        """
        Extracts strictly the LAST window of each test engine.
        Rule: "Test evaluation: only the LAST window of each test engine vs RUL_FD001.txt."

        Returns:
            X_test_last: 3D array (100, window_size=30, n_features=14)
            test_engine_ids: 1D array of engine IDs (1 to 100)
        """
        X_last: List[np.ndarray] = []
        engine_ids: List[int] = []

        for engine_id, group in test_df.groupby("engine_id"):
            engine_data = group[self.feature_cols].values
            n_rows = len(group)

            if n_rows >= self.window_size:
                window = engine_data[-self.window_size :, :]
            else:
                pad_len = self.window_size - n_rows
                pad_features = np.repeat(engine_data[:1, :], pad_len, axis=0)
                window = np.vstack([pad_features, engine_data])

            X_last.append(window)
            engine_ids.append(int(engine_id))

        return np.array(X_last, dtype=np.float32), np.array(engine_ids, dtype=np.int32)

    @staticmethod
    def extract_tabular_features(X_seq: np.ndarray, feature_names: List[str]) -> Tuple[np.ndarray, List[str]]:
        """
        Extracts summary features from sliding windows for XGBoost:
        - last value (t)
        - mean across window
        - std deviation across window
        - slope across window (linear rate of change: (last - first) / (w - 1))

        For 14 sensors, this produces 14 * 4 = 56 tabular features.
        """
        N, W, D = X_seq.shape
        last_vals = X_seq[:, -1, :]              # (N, D)
        mean_vals = np.mean(X_seq, axis=1)        # (N, D)
        std_vals = np.std(X_seq, axis=1)          # (N, D)
        slope_vals = (X_seq[:, -1, :] - X_seq[:, 0, :]) / max(1, W - 1)  # (N, D)

        X_tab = np.hstack([last_vals, mean_vals, std_vals, slope_vals])  # (N, 4*D)

        tab_names: List[str] = (
            [f"{f}_last" for f in feature_names]
            + [f"{f}_mean" for f in feature_names]
            + [f"{f}_std" for f in feature_names]
            + [f"{f}_slope" for f in feature_names]
        )
        return X_tab, tab_names

